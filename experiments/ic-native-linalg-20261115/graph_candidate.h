/* Exact elimination for linear-sieve relations. Included after relation's
 * definition. Auxiliary columns occur as h_u+h_v or 2*h_u. */
#ifndef CA_IC_GRAPH_H
#define CA_IC_GRAPH_H

#include <limits.h>

static ca_status build_graph_matrix(const rel_list *rels, uint32_t ncols,
                                    uint32_t nfb, uint64_t modulus,
                                    ca_spmat *A, uint64_t **b_out)
{
    const uint32_t none = UINT32_MAX;
    uint32_t nv = ncols - nfb;
    /* Bound the dense expression workspace; larger instances use CSR as
     * before. All persistent relation output remains sparse. */
    if (!nv || !nfb || (size_t)nv > (64u * 1024u * 1024u) / sizeof(int32_t) / nfb ||
        rels->n > UINT32_MAX / 2) return CA_ERR_INVALID;
    ca_status rc = CA_ERR_NOMEM;
    uint32_t *u = malloc((size_t)rels->n * sizeof(*u));
    uint32_t *v = malloc((size_t)rels->n * sizeof(*v));
    uint32_t *head = malloc((size_t)nv * sizeof(*head));
    uint32_t *next = malloc((size_t)rels->n * 2 * sizeof(*next));
    uint32_t *queue = malloc((size_t)nv * sizeof(*queue));
    uint32_t *component = malloc((size_t)nv * sizeof(*component));
    int8_t *sign = calloc(nv, sizeof(*sign));
    int32_t *expr = calloc((size_t)nv * nfb, sizeof(*expr));
    uint64_t *constant = calloc(nv, sizeof(*constant));
    int64_t *row = calloc(nfb, sizeof(*row));
    uint32_t *cols = malloc(((size_t)nfb + 1) * sizeof(*cols));
    int32_t *vals = malloc(((size_t)nfb + 1) * sizeof(*vals));
    uint64_t *rhs = calloc(rels->n ? rels->n : 1, sizeof(*rhs));
    int initialized = 0;
    if (!u || !v || !head || !next || !queue || !component || !sign || !expr ||
        !constant || !row || !cols || !vals || !rhs) goto done;
    for (uint32_t j = 0; j < nv; ++j) head[j] = none;
    for (uint32_t i = 0; i < rels->n; ++i) {
        const relation *r = &rels->r[i];
        u[i] = v[i] = none;
        unsigned count = 0;
        for (uint32_t k = 0; k < r->n; ++k) {
            if (r->col[k] < nfb) continue;
            if (r->col[k] >= ncols || ++count > 2) { rc = CA_ERR_INVALID; goto done; }
            uint32_t node = r->col[k] - nfb;
            if (r->val[k] == 2 && count == 1) u[i] = v[i] = node;
            else if (r->val[k] == 1) {
                if (count == 1) u[i] = node;
                else if (v[i] == none) v[i] = node;
                else { rc = CA_ERR_INVALID; goto done; }
            } else { rc = CA_ERR_INVALID; goto done; }
        }
        if (!count) continue;
        if (u[i] == none || v[i] == none) { rc = CA_ERR_INVALID; goto done; }
        next[2 * i] = head[u[i]]; head[u[i]] = 2 * i;
        next[2 * i + 1] = head[v[i]]; head[v[i]] = 2 * i + 1;
    }
    uint32_t nc = 0;
    for (uint32_t root = 0; root < nv; ++root) {
        if (sign[root] || head[root] == none) continue;
        uint32_t first = 0, end = 0;
        sign[root] = 1;
        component[root] = nc++;
        queue[end++] = root;
        while (first < end) {
            uint32_t parent = queue[first++];
            for (uint32_t edge = head[parent]; edge != none; edge = next[edge]) {
                uint32_t i = edge / 2;
                uint32_t child = u[i] == parent ? v[i] : u[i];
                if (sign[child]) continue;
                sign[child] = (int8_t)-sign[parent];
                component[child] = component[parent];
                constant[child] = ca_submod(rels->r[i].rhs % modulus, constant[parent], modulus);
                int32_t *dst = expr + (size_t)child * nfb;
                const int32_t *src = expr + (size_t)parent * nfb;
                for (uint32_t j = 0; j < nfb; ++j) {
                    if (src[j] == INT32_MIN) { rc = CA_ERR_INVALID; goto done; }
                    dst[j] = -src[j];
                }
                const relation *r = &rels->r[i];
                for (uint32_t k = 0; k < r->n; ++k) {
                    uint32_t j = r->col[k];
                    if (j >= nfb) continue;
                    int64_t value = (int64_t)dst[j] - r->val[k];
                    if (value <= INT32_MIN || value > INT32_MAX) { rc = CA_ERR_INVALID; goto done; }
                    dst[j] = (int32_t)value;
                }
                queue[end++] = child;
            }
        }
    }
    rc = ca_spmat_init(A, nfb + nc, rels->n, rels->n * 16);
    if (rc != CA_OK) goto done;
    initialized = 1;
    for (uint32_t i = 0; i < rels->n; ++i) {
        const relation *r = &rels->r[i];
        memset(row, 0, (size_t)nfb * sizeof(*row));
        uint64_t b = r->rhs % modulus;
        int root_coef = 0;
        if (u[i] != none) {
            const int32_t *eu = expr + (size_t)u[i] * nfb;
            const int32_t *ev = expr + (size_t)v[i] * nfb;
            for (uint32_t j = 0; j < nfb; ++j) row[j] = (int64_t)eu[j] + ev[j];
            root_coef = sign[u[i]] + sign[v[i]];
            b = ca_submod(ca_submod(b, constant[u[i]], modulus), constant[v[i]], modulus);
        }
        for (uint32_t k = 0; k < r->n; ++k)
            if (r->col[k] < nfb) row[r->col[k]] += r->val[k];
        uint32_t count = 0;
        for (uint32_t j = 0; j < nfb; ++j) {
            if (!row[j]) continue;
            if (row[j] <= INT32_MIN || row[j] > INT32_MAX) { rc = CA_ERR_INVALID; goto done; }
            cols[count] = j; vals[count++] = (int32_t)row[j];
        }
        if (root_coef) {
            cols[count] = nfb + component[u[i]];
            vals[count++] = root_coef;
        }
        if (!count && !b) continue; /* spanning-tree equations become 0=0 */
        rhs[A->rows] = b;
        rc = ca_spmat_add_row(A, cols, vals, count);
        if (rc != CA_OK) goto done;
    }
    *b_out = rhs;
    rhs = NULL;
    rc = CA_OK;
done:
    if (rc != CA_OK && initialized) ca_spmat_free(A);
    free(u); free(v); free(head); free(next); free(queue); free(component);
    free(sign); free(expr); free(constant); free(row); free(cols); free(vals); free(rhs);
    return rc;
}
#endif
