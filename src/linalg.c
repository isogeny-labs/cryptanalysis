/*
 * linalg.c - structured Gaussian elimination + Lanczos modulo a prime.
 */
#include "linalg.h"
#include "ca_internal.h"

#include <pthread.h>
#include <sched.h>
#include <stdatomic.h>
#include <unistd.h>

/* ---- sparse matrix ------------------------------------------------------ */

ca_status ca_spmat_init(ca_spmat *m, uint32_t cols, uint32_t expected_rows, uint32_t expected_nnz)
{
    memset(m, 0, sizeof(*m));
    m->cols = cols;
    m->row_cap = (size_t)expected_rows + 1;
    m->row_ptr = malloc(m->row_cap * sizeof(uint32_t));
    m->cap = expected_nnz ? expected_nnz : 1024;
    m->col = malloc(m->cap * sizeof(uint32_t));
    m->val = malloc(m->cap * sizeof(int32_t));
    if (!m->row_ptr || !m->col || !m->val) { ca_spmat_free(m); return CA_ERR_NOMEM; }
    m->row_ptr[0] = 0;
    m->rows = 0;
    m->nnz = 0;
    return CA_OK;
}

void ca_spmat_free(ca_spmat *m)
{
    free(m->row_ptr);
    free(m->col);
    free(m->val);
    memset(m, 0, sizeof(*m));
}

ca_status ca_spmat_add_row(ca_spmat *m, const uint32_t *cols, const int32_t *vals, uint32_t n)
{
    /* row_ptr needs rows + 2 slots once this row is appended.  The capacity
     * is per matrix: expected_rows at init is a hint, not a limit, and a
     * matrix must never grow into another matrix's bookkeeping. */
    size_t need = (size_t)m->rows + 2;
    if (m->row_cap < need) {
        size_t ncap = m->row_cap ? m->row_cap : 1024;
        while (ncap < need) ncap *= 2;
        uint32_t *np = realloc(m->row_ptr, ncap * sizeof(uint32_t));
        if (!np) return CA_ERR_NOMEM;
        m->row_ptr = np;
        m->row_cap = ncap;
    }
    if ((size_t)m->nnz + n > m->cap) {
        uint32_t ncap = m->cap;
        while ((size_t)m->nnz + n > ncap) ncap *= 2;
        uint32_t *nc = realloc(m->col, ncap * sizeof(uint32_t));
        if (!nc) return CA_ERR_NOMEM;
        m->col = nc;
        int32_t *nv = realloc(m->val, ncap * sizeof(int32_t));
        if (!nv) return CA_ERR_NOMEM;
        m->val = nv;
        m->cap = ncap;
    }
    uint32_t start = m->nnz;
    for (uint32_t i = 0; i < n; i++) {
        if (vals[i] == 0) continue;
        int merged = 0;
        for (uint32_t k = start; k < m->nnz; k++) {
            if (m->col[k] == cols[i]) { m->val[k] += vals[i]; merged = 1; break; }
        }
        if (!merged) {
            m->col[m->nnz] = cols[i];
            m->val[m->nnz] = vals[i];
            m->nnz++;
        }
    }
    /* drop zeros produced by merging */
    uint32_t w = start;
    for (uint32_t k = start; k < m->nnz; k++) {
        if (m->val[k] != 0) { m->col[w] = m->col[k]; m->val[w] = m->val[k]; w++; }
    }
    m->nnz = w;
    m->rows++;
    m->row_ptr[m->rows] = m->nnz;
    return CA_OK;
}

/* ---- multiplication by a fixed factor (Shoup) --------------------------- */

/* For a fixed w < q < 2^63, wp = floor(w * 2^64 / q) turns a * w mod q into
 * two multiplications and one conditional subtraction, for any a < 2^64:
 * a*w - floor(a*wp / 2^64)*q lies in [0, 2q) (Shoup; Harvey 2014).  The
 * result equals ca_mulmod(a, w, q). */
static inline uint64_t shoup_pre(uint64_t w, uint64_t q)
{
    return (uint64_t)(((ca_u128)w << 64) / q);
}

static inline uint64_t shoup_mul(uint64_t a, uint64_t w, uint64_t wp, uint64_t q)
{
    uint64_t qhat = (uint64_t)(((ca_u128)a * wp) >> 64);
    uint64_t r = a * w - qhat * q;
    return r >= q ? r - q : r;
}

/* ---- dense elimination -------------------------------------------------- */

static ca_status dense_solve_rowops(uint64_t *M, uint32_t n, uint64_t *rhs, uint64_t q, uint64_t *x)
{
#define A(i, j) M[(size_t)(i) * n + (j)]
    /* Reduce once: every entry the elimination writes is already in
     * [0, q), so the per-access % q of the loops below had nothing left to
     * do after the first touch.  Below 2^63 each row update multiplies by
     * a fixed factor, which Shoup's precomputation makes division-free.
     *
     * Forward elimination with the pivot row normalised, then back
     * substitution: the pivot of column c is the first row at or below c
     * whose entry is nonzero, the same row Gauss-Jordan elimination picks
     * (its extra updates touch only the rows above c), so singularity is
     * decided identically, and the solution is the unique one.  It updates
     * the rows below the pivot only, about two thirds of the products of
     * Gauss-Jordan.  M and rhs are left in echelon form. */
    for (size_t k = 0; k < (size_t)n * n; k++) M[k] %= q;
    for (uint32_t i = 0; i < n; i++) rhs[i] %= q;
    const int shoup = q < ((uint64_t)1 << 63);
    for (uint32_t c = 0; c < n; c++) {
        uint32_t piv = c;
        while (piv < n && A(piv, c) == 0) piv++;
        if (piv == n) return CA_ERR_SINGULAR;
        if (piv != c) {
            for (uint32_t j = c; j < n; j++) {
                uint64_t t = A(c, j);
                A(c, j) = A(piv, j);
                A(piv, j) = t;
            }
            uint64_t t = rhs[c]; rhs[c] = rhs[piv]; rhs[piv] = t;
        }
        uint64_t inv = ca_invmod(A(c, c), q);
        A(c, c) = 1;
        for (uint32_t j = c + 1; j < n; j++) A(c, j) = ca_mulmod(A(c, j), inv, q);
        rhs[c] = ca_mulmod(rhs[c], inv, q);
        for (uint32_t i = c + 1; i < n; i++) {
            uint64_t f = A(i, c);
            if (!f) continue;
            A(i, c) = 0;
            if (shoup) {
                uint64_t fp = shoup_pre(f, q);
                for (uint32_t j = c + 1; j < n; j++)
                    A(i, j) = ca_submod(A(i, j), shoup_mul(A(c, j), f, fp, q), q);
                rhs[i] = ca_submod(rhs[i], shoup_mul(rhs[c], f, fp, q), q);
            } else {
                for (uint32_t j = c + 1; j < n; j++)
                    A(i, j) = ca_submod(A(i, j), ca_mulmod(f, A(c, j), q), q);
                rhs[i] = ca_submod(rhs[i], ca_mulmod(f, rhs[c], q), q);
            }
        }
    }
    for (uint32_t c = n; c-- > 0;) {
        uint64_t t = rhs[c];
        for (uint32_t j = c + 1; j < n; j++) t = ca_submod(t, ca_mulmod(A(c, j), x[j], q), q);
        x[c] = t;
    }
#undef A
    return CA_OK;
}

/* sum_k a[k] b[k] mod q over n terms (q < 2^63): `chunk` products fit in
 * the 128-bit sum (dense_chunk), reduced as hi (2^64 mod q) + lo. */
static uint64_t dense_dot(const uint64_t *a, const uint64_t *b, uint32_t n, uint64_t q,
                          uint32_t chunk, uint64_t r64, uint64_t r64p, uint64_t onep)
{
    uint64_t r = 0;
    for (uint32_t i0 = 0; i0 < n;) {
        uint32_t i1 = n - i0 > chunk ? i0 + chunk : n;
        ca_u128 acc = 0;
        /* one running 128-bit sum (mul, add, adc a term), four terms a step */
        const uint64_t *pa = a + i0, *pb = b + i0;
        uint32_t cnt = i1 - i0;
        for (; cnt >= 4; cnt -= 4, pa += 4, pb += 4) {
            acc += (ca_u128)pa[0] * pb[0];
            acc += (ca_u128)pa[1] * pb[1];
            acc += (ca_u128)pa[2] * pb[2];
            acc += (ca_u128)pa[3] * pb[3];
        }
        for (; cnt; cnt--) acc += (ca_u128)*pa++ * *pb++;
        uint64_t hi = (uint64_t)(acc >> 64), lo = (uint64_t)acc;
        r = ca_addmod(r, ca_addmod(shoup_mul(hi, r64, r64p, q), shoup_mul(lo, 1, onep, q), q), q);
        i0 = i1;
    }
    return r;
}

ca_status ca_dense_solve_mod_prime(uint64_t *M, uint32_t n, uint64_t *rhs, uint64_t q, uint64_t *x)
{
    /* Below 2^63, Crout's order of the same elimination: the entry the row
     * operations would leave at (i, c) is a(i, c) - sum_{k<c} l(i, k)
     * u(k, c), with l(i, k) the multiplier of row i at step k (the entry
     * at (i, k) when step k ran) and u(k, .) the normalised pivot row k.
     * Each entry is therefore one dot product, summed in 128 bits and
     * reduced once, instead of c Shoup products and subtractions.  Column c
     * is formed for the rows at and below c, its first nonzero row is the
     * pivot (the row dense_solve_rowops picks: same values), the rows are
     * swapped whole (their multipliers with them), and row c of U is
     * formed and normalised (into M, whose row c right of the diagonal is
     * read no more, and transposed into UT, so that every dot product runs
     * over contiguous words).  Same pivots, same singularity, the unique
     * solution.  M and rhs are overwritten. */
    if (n == 0) return CA_OK;
    if (q >= ((uint64_t)1 << 63)) return dense_solve_rowops(M, n, rhs, q, x);
    uint64_t *UT =
        malloc((size_t)n * (n + 1) * sizeof(uint64_t)); /* UT[j][k] = u(k, j); j = n: rhs */
    if (!UT) return dense_solve_rowops(M, n, rhs, q, x);
#define A(i, j)   M[(size_t)(i) * n + (j)]
#define UTm(j, k) UT[(size_t)(j) * n + (k)]
    for (size_t k = 0; k < (size_t)n * n; k++) M[k] %= q;
    for (uint32_t i = 0; i < n; i++) rhs[i] %= q;
    const uint32_t bits = 64 - (uint32_t)__builtin_clzll(q - 1 ? q - 1 : 1);
    const uint32_t room = 128 - 2 * bits; /* products a 128-bit sum holds: 2^room */
    const uint32_t chunk = room >= 32 ? UINT32_MAX : (uint32_t)1 << (room & 31);
    const uint64_t r64 = (uint64_t)((((ca_u128)1) << 64) % q), r64p = shoup_pre(r64, q);
    const uint64_t onep = shoup_pre(1, q);
    ca_status rc = CA_OK;
    for (uint32_t c = 0; c < n; c++) {
        /* column c at and below the diagonal: a(i, c) - l(i, 0..c) . u(0..c, c) */
        for (uint32_t i = c; i < n; i++)
            A(i, c) = ca_submod(A(i, c),
                                dense_dot(&A(i, 0), &UTm(c, 0), c, q, chunk, r64, r64p, onep), q);
        uint32_t piv = c;
        while (piv < n && A(piv, c) == 0) piv++;
        if (piv == n) {
            rc = CA_ERR_SINGULAR;
            break;
        }
        if (piv != c) {
            for (uint32_t j = 0; j < n; j++) {
                uint64_t t = A(c, j);
                A(c, j) = A(piv, j);
                A(piv, j) = t;
            }
            uint64_t t = rhs[c];
            rhs[c] = rhs[piv];
            rhs[piv] = t;
        }
        const uint64_t inv = ca_invmod(A(c, c), q), invp = shoup_pre(inv, q);
        /* row c of U right of the diagonal, and the right-hand side */
        for (uint32_t j = c + 1; j < n; j++) {
            uint64_t t = ca_submod(
                A(c, j), dense_dot(&A(c, 0), &UTm(j, 0), c, q, chunk, r64, r64p, onep), q);
            UTm(j, c) = A(c, j) = shoup_mul(t, inv, invp, q); /* a(c, j) is read no more */
        }
        {
            uint64_t t =
                ca_submod(rhs[c], dense_dot(&A(c, 0), &UTm(n, 0), c, q, chunk, r64, r64p, onep), q);
            UTm(n, c) = shoup_mul(t, inv, invp, q);
        }
    }
    if (rc == CA_OK) {
        /* back substitution: x_c = rhs'_c - sum_{j>c} u(c, j) x_j */
        for (uint32_t c = n; c-- > 0;)
            x[c] = ca_submod(
                UTm(n, c), dense_dot(&A(c, c + 1), &x[c + 1], n - c - 1, q, chunk, r64, r64p, onep),
                q);
    }
#undef UTm
#undef A
    free(UT);
    return rc;
}

/* ---- modular vector helpers ------------------------------------------- */

/* small signed coefficient reduced into [0, q) */
static inline uint64_t coef_mod(int64_t v, uint64_t q)
{
    if (v >= 0) return (uint64_t)v % q;
    uint64_t m = (uint64_t)(-v) % q;
    return m ? q - m : 0;
}

/* v mod q for a signed 128-bit v, canonical. */
static inline uint64_t i128_mod(ca_i128 v, uint64_t q)
{
    if (v >= 0) return (uint64_t)((ca_u128)v % q);
    uint64_t m = (uint64_t)((ca_u128)(-v) % q);
    return m ? q - m : 0;
}

/* y = A v (mod q) with one signed 128-bit accumulator per row: each term is
 * below 2^31 * 2^64 = 2^95 in size, so 2^31 of them cannot overflow, and a
 * row is flushed every 2^30 terms regardless.  (A v) mod q is what the old
 * positive/negative pair of accumulators computed, without its
 * data-dependent branch and with one reduction a row instead of two. */
static void spmv(const ca_spmat *A, const uint64_t *v, uint64_t *y, uint64_t q)
{
    for (uint32_t i = 0; i < A->rows; i++) {
        ca_i128 acc = 0;
        uint32_t cnt = 0;
        uint64_t r = 0;
        for (uint32_t k = A->row_ptr[i]; k < A->row_ptr[i + 1]; k++) {
            acc += (ca_i128)A->val[k] * (ca_i128)v[A->col[k]];
            if (++cnt == 1u << 30) { /* never in practice */
                r = ca_addmod(r, i128_mod(acc, q), q);
                acc = 0;
                cnt = 0;
            }
        }
        y[i] = ca_addmod(r, i128_mod(acc, q), q);
    }
}

/* z = A^T w (mod q), one signed 128-bit accumulator per column: terms
 * are below 2^95 in size, so up to 2^31 rows fit. */
static void spmtv(const ca_spmat *A, const uint64_t *w, uint64_t *z, uint64_t q, ca_i128 *acc)
{
    memset(acc, 0, A->cols * sizeof(ca_i128));
    for (uint32_t i = 0; i < A->rows; i++) {
        uint64_t wi = w[i];
        if (!wi) continue;
        for (uint32_t k = A->row_ptr[i]; k < A->row_ptr[i + 1]; k++)
            acc[A->col[k]] += (ca_i128)A->val[k] * (ca_i128)wi;
    }
    for (uint32_t j = 0; j < A->cols; j++) z[j] = i128_mod(acc[j], q);
}

/* ---- the Lanczos kernels ------------------------------------------------ */

/* A CSR matrix re-laid for the gather kernels.  Index calculus matrices
 * are 90 %+ +-1 entries, and the kernels read a vector v of n entries
 * stored with its negation behind it: vv = [v | q - v], 2n entries.  A
 * term c * v[col] with c < 0 is then |c| * vv[n + col], so every term is
 * nonnegative: the row sum is a plain unsigned sum (no bias, no sign
 * handling) congruent to the signed one mod q, and the unit terms need no
 * coefficient load and no multiply.  Each row holds its unit terms first:
 * ptr (not owned) bounds the row, ue ends the unit run; idx holds the
 * (offset) columns and oval the magnitudes of the remaining terms (slots
 * of the unit run are unused).
 *
 * A row whose sum of |c| times q reaches 2^64 (a "heavy" row, flagged in
 * bit 31 of ue: the dense columns of A^T, and nearly every row for q near
 * 2^63) could overflow the 64-bit sum: it is summed from the plain CSR
 * (hcol, hval, not owned, the same offsets as ptr) in signed 128 bits. */
#define LZ_HEAVY 0x80000000u
typedef struct lz_gat {
    const uint32_t *ptr, *hcol;
    const int32_t *hval;
    uint32_t *ue, *idx, *oval;
} lz_gat;

/* What one Lanczos call reads besides A: its transpose (A^T in CSR, built
 * once, so that A^T w is a row gather like A v rather than a scatter into
 * 128-bit column accumulators), whether the gather kernels apply, and the
 * constants of the reductions. */
typedef struct lz_ctx {
    uint64_t q;
    lz_gat ga, gt;    /* A and A^T for the gather kernels (fast != 0) */
    int fast;         /* 0: the 128-bit scatter kernels; 1: the gathers */
    uint32_t heavy_a; /* heavy rows of A (they need 2^64 D_i mod q) */
    uint32_t tcols; /* rows of A^T = cols of A */
    uint32_t *tptr, *tcol; /* A^T in CSR */
    int32_t *tval;
    uint32_t dot_chunk; /* vdot terms summed in 128 bits between reductions */
    uint64_t r64, r64p; /* 2^64 mod q and its Shoup constant (q < 2^63) */
    uint64_t npi;       /* q^{-1} mod 2^64, for lz_redc */
    uint64_t onep;      /* Shoup constant of 1: floor(2^64 / q), a remainder by q */
    ca_u128 bias128;    /* K q, K the largest row or column sum of |val|, for the 128-bit gather */
} lz_ctx;

/* v mod q for an unsigned 128-bit v: below 2^63 as hi * (2^64 mod q) + lo
 * with two Shoup products (lo mod q is lo * 1), no division; otherwise by
 * the library's 128-bit remainder.  Canonical either way. */
static inline uint64_t lz_u128_mod(const lz_ctx *z, ca_u128 v)
{
    uint64_t hi = (uint64_t)(v >> 64), lo = (uint64_t)v, q = z->q;
    if (q >= ((uint64_t)1 << 63)) return (uint64_t)(v % q);
    uint64_t l = shoup_mul(lo, 1, z->onep, q);
    if (!hi) return l;
    return ca_addmod(shoup_mul(hi, z->r64, z->r64p, q), l, q);
}

/* u 2^-64 mod q for u < q 2^64 (Montgomery's reduction, the subtraction
 * form of ca_mont_redc): canonical. */
static inline uint64_t lz_redc(const lz_ctx *z, ca_u128 u)
{
    const uint64_t q = z->q, lo = (uint64_t)u, hi = (uint64_t)(u >> 64);
    const uint64_t m = lo * z->npi;
    const uint64_t mh = (uint64_t)(((ca_u128)m * q) >> 64);
    uint64_t r = hi - mh;
    if (hi < mh) r += q;
    return r;
}

/* The three products a Lanczos step reads, w.Bw, w.b' and Bw.Bw, mod q in
 * one pass.  Each product is at most (q-1)^2 < 2^(2 bits(q-1)), so
 * z->dot_chunk = 2^(128 - 2 bits(q-1)) of them (all of them below 2^48)
 * fit in a 128-bit sum before it must be reduced. */
static inline void vdot3(const lz_ctx *z, const uint64_t *w, const uint64_t *Bw, const uint64_t *bp,
                         uint32_t n, uint64_t out[3])
{
    uint64_t r0 = 0, r1 = 0, r2 = 0, q = z->q;
    for (uint32_t i0 = 0; i0 < n;) {
        uint32_t i1 = n - i0 > z->dot_chunk ? i0 + z->dot_chunk : n;
        ca_u128 a0 = 0, a1 = 0, a2 = 0;
        for (uint32_t i = i0; i < i1; i++) {
            const uint64_t wi = w[i], bi = Bw[i];
            a0 += (ca_u128)wi * bi;
            a1 += (ca_u128)wi * bp[i];
            a2 += (ca_u128)bi * bi;
        }
        r0 = ca_addmod(r0, lz_u128_mod(z, a0), q);
        r1 = ca_addmod(r1, lz_u128_mod(z, a1), q);
        r2 = ca_addmod(r2, lz_u128_mod(z, a2), q);
        i0 = i1;
    }
    out[0] = r0;
    out[1] = r1;
    out[2] = r2;
}

/* Re-lay a CSR matrix into g (see lz_gat); the vector it will read has
 * voff entries.  False on allocation failure. */
static int lz_gat_build(lz_gat *g, uint32_t rows, const uint32_t *ptr, const uint32_t *col,
                        const int32_t *val, uint32_t nnz, uint32_t voff, uint64_t light_sum,
                        uint32_t *nheavy)
{
    g->ptr = ptr;
    g->hcol = col;
    g->hval = val;
    g->ue = malloc(((size_t)rows + 1) * sizeof(uint32_t));
    g->idx = malloc(((size_t)nnz + 1) * sizeof(uint32_t));
    g->oval = calloc((size_t)nnz + 1, sizeof(uint32_t));
    if (!g->ue || !g->idx || !g->oval) return 0;
    for (uint32_t i = 0; i < rows; i++) {
        uint32_t o = ptr[i];
        const uint32_t e = ptr[i + 1];
        for (uint32_t k = ptr[i]; k < e; k++)
            if (val[k] == 1)
                g->idx[o++] = col[k];
            else if (val[k] == -1)
                g->idx[o++] = col[k] + voff;
        g->ue[i] = o;
        uint64_t rs = 0;
        for (uint32_t k = ptr[i]; k < e; k++)
            rs += (uint64_t)(val[k] < 0 ? -(int64_t)val[k] : (int64_t)val[k]);
        if (rs > light_sum) {
            g->ue[i] |= LZ_HEAVY;
            (*nheavy)++;
        }
        for (uint32_t k = ptr[i]; k < e; k++)
            if (val[k] != 1 && val[k] != -1) {
                g->idx[o] = val[k] < 0 ? col[k] + voff : col[k];
                g->oval[o++] = val[k] < 0 ? (uint32_t)(-(int64_t)val[k]) : (uint32_t)val[k];
            }
    }
    return 1;
}

static void lz_gat_free(lz_gat *g)
{
    free(g->ue);
    free(g->idx);
    free(g->oval);
    g->ue = g->idx = g->oval = NULL;
}

/* sum of v[*p] over [p, e) in 64 bits: two chains, four terms a step */
static inline uint64_t lz_sum_idx64(const uint32_t *p, const uint32_t *e, const uint64_t *v)
{
    uint64_t a = 0, b = 0;
    for (; e - p >= 4; p += 4) {
        a += v[p[0]];
        b += v[p[1]];
        a += v[p[2]];
        b += v[p[3]];
    }
    if (e - p >= 2) {
        a += v[p[0]];
        b += v[p[1]];
        p += 2;
    }
    if (p < e) a += v[p[0]];
    return a + b;
}

/* A heavy row, y_i = D_i (sum_k val_k v[col_k]) mod q in signed 128-bit
 * arithmetic over the plain CSR: v < q < 2^63, so one signed 64 x 64 -> 128
 * product a term; every term is below 2^31 * 2^63 = 2^94 in size and the
 * row has fewer than 2^31 terms (lz_init), so the sum stays below 2^125 and
 * needs no intermediate reduction.  The sum >= -K (q - 1), so u = sum + K q
 * (K the largest row or column sum of |val|) is positive and below 2 K q <
 * q 2^64: its Montgomery reduction is u 2^-64 mod q, and the Shoup product
 * by 2^64 D_i mod q (2^64 mod q without the scaling) puts back the 2^64. */
static inline __attribute__((always_inline)) uint64_t
lz_row128(const lz_ctx *z, uint32_t k, uint32_t e, const uint32_t *col, const int32_t *val,
          const uint64_t *v, const uint64_t *DR, const uint64_t *DRp)
{
    ca_i128 acc = 0;
    for (; k + 4 <= e; k += 4) {
        acc += (ca_i128)((int64_t)val[k]) * (int64_t)v[col[k]];
        acc += (ca_i128)((int64_t)val[k + 1]) * (int64_t)v[col[k + 1]];
        acc += (ca_i128)((int64_t)val[k + 2]) * (int64_t)v[col[k + 2]];
        acc += (ca_i128)((int64_t)val[k + 3]) * (int64_t)v[col[k + 3]];
    }
    switch (e - k) { /* the last 0-3 terms, straight-line */
    case 3: acc += (ca_i128)((int64_t)val[k + 2]) * (int64_t)v[col[k + 2]]; /* fall through */
    case 2: acc += (ca_i128)((int64_t)val[k + 1]) * (int64_t)v[col[k + 1]]; /* fall through */
    case 1: acc += (ca_i128)((int64_t)val[k]) * (int64_t)v[col[k]];         /* fall through */
    default: break;
    }
    const uint64_t r = lz_redc(z, (ca_u128)acc + z->bias128);
    return DR ? shoup_mul(r, *DR, *DRp, z->q) : shoup_mul(r, z->r64, z->r64p, z->q);
}

/* y_i = D_i * (sum_k c_k vv[idx_k]) mod q over the rows of a gather-laid
 * matrix, in 64 bits (heavy rows: lz_row128); D == NULL leaves out the
 * scaling (DR likewise: 2^64 D_i mod q with its Shoup constants DRp, for the
 * heavy rows); yn, when given, receives q - y_i (the negation half of the
 * next kernel's input).  A light row has K_i q < 2^64, K_i its sum of |c|:
 * every term is below |c| q, so the unsigned sum is below 2^64, and a
 * Shoup product reduces any 64-bit operand (by D_i when scaling, by 1
 * otherwise).  The sum is congruent to the signed (A v)_i, so the value is
 * the exact (A v)_i mod q the 128-bit rows compute. */
static inline __attribute__((always_inline)) void
spmv_body(const lz_ctx *z, const uint32_t *ptr, const uint32_t *ue, const lz_gat *g, uint32_t rows,
          const uint64_t *vv, uint64_t *y, uint64_t *yn, const uint64_t *D, const uint64_t *Dp,
          const uint64_t *DR, const uint64_t *DRp)
{
    const uint64_t q = z->q, onep = z->onep;
    const uint32_t *const idx = g->idx, *const oval = g->oval;
    for (uint32_t i = 0; i < rows; i++) {
        uint64_t r;
        const uint32_t u0 = ue[i];
        if (__builtin_expect(u0 & LZ_HEAVY, 0)) {
            r = lz_row128(z, ptr[i], ptr[i + 1], g->hcol, g->hval, vv, DR ? DR + i : NULL,
                          DR ? DRp + i : NULL);
        } else {
            const uint32_t *const e = idx + ptr[i + 1], *const ub = idx + u0;
            uint64_t u = lz_sum_idx64(idx + ptr[i], ub, vv);
            for (const uint32_t *t = ub; t < e; t++) u += (uint64_t)oval[t - idx] * vv[*t];
            r = D ? shoup_mul(u, D[i], Dp[i], q) : shoup_mul(u, 1, onep, q);
        }
        y[i] = r;
        if (yn) yn[i] = q - r;
    }
}

/* Rows [r0, r0 + rows) of the product (a thread of the Lanczos pool runs a
 * block of rows; no element of y is written by two threads, and the sums
 * are exact whatever the block); y, yn, D, Dp, DR and DRp are indexed from
 * the block's first row.  The two call shapes, A v (scaled, with its
 * negation) and A^T w (neither), get their own copies: the tests on D and
 * yn then leave the row loop. */
static void lz_spmv(const lz_ctx *z, const lz_gat *g, uint32_t r0, uint32_t rows,
                    const uint64_t *vv, uint64_t *y, uint64_t *yn, const uint64_t *D,
                    const uint64_t *Dp, const uint64_t *DR, const uint64_t *DRp)
{
    const uint32_t *ptr = g->ptr + r0, *ue = g->ue + r0;
    if (D && yn)
        spmv_body(z, ptr, ue, g, rows, vv, y, yn, D, Dp, DR, DRp);
    else if (!D && !yn)
        spmv_body(z, ptr, ue, g, rows, vv, y, NULL, NULL, NULL, NULL, NULL);
    else
        spmv_body(z, ptr, ue, g, rows, vv, y, yn, D, Dp, DR, DRp);
}

static void lz_free(lz_ctx *z)
{
    free(z->tptr);
    free(z->tcol);
    free(z->tval);
    z->tptr = z->tcol = NULL;
    z->tval = NULL;
    lz_gat_free(&z->ga);
    lz_gat_free(&z->gt);
}

/* Decide the kernels and build A^T for the 64-bit ones.  CA_ERR_NOMEM only
 * when the transpose cannot be allocated. */
static ca_status lz_init(lz_ctx *z, const ca_spmat *A, uint64_t q)
{
    memset(z, 0, sizeof(*z));
    z->q = q;
    uint32_t bits = 64 - (uint32_t)__builtin_clzll(q - 1);
    const uint32_t room = 128 - 2 * bits; /* products a 128-bit sum holds: 2^room */
    z->dot_chunk = room >= 32 ? UINT32_MAX : (uint32_t)1 << (room & 31);
    if (q >= ((uint64_t)1 << 63)) return CA_OK;
    z->r64 = (uint64_t)((((ca_u128)1) << 64) % q);
    z->r64p = shoup_pre(z->r64, q);
    z->onep = shoup_pre(1, q);
    {
        uint64_t inv = q; /* Newton: q^{-1} mod 2^64, 3 -> 6 -> ... -> 96 bits */
        for (int it = 0; it < 5; it++) inv *= 2 - q * inv;
        z->npi = inv;
    }
    /* the largest row and column sums of |val|: each below nnz * 2^31 */
    uint64_t *csum = calloc(A->cols ? A->cols : 1, sizeof(uint64_t));
    if (!csum) return CA_ERR_NOMEM;
    uint64_t rmax = 0, cmax = 0;
    for (uint32_t i = 0; i < A->rows; i++) {
        uint64_t rs = 0;
        for (uint32_t k = A->row_ptr[i]; k < A->row_ptr[i + 1]; k++) {
            uint64_t a = (uint64_t)(A->val[k] < 0 ? -(int64_t)A->val[k] : A->val[k]);
            rs += a;
            csum[A->col[k]] += a;
        }
        if (rs > rmax) rmax = rs;
    }
    for (uint32_t j = 0; j < A->cols; j++)
        if (csum[j] > cmax) cmax = csum[j];
    free(csum);
    /* A row or column whose sum of |val| is at most light_sum = floor((2^64 - 1) / q)
     * sums to below 2^64 in 64 bits (every term |c| (v or q - v) is at most
     * |c| q); the others are heavy (lz_gat).  The negation halves are
     * indexed past n (resp. m) entries, flags live in bit 31 of the row
     * ends, and a heavy row has fewer than 2^31 terms. */
    const uint64_t K = rmax > cmax ? rmax : cmax; /* below nnz 2^31 < 2^63 */
    const uint64_t light_sum = UINT64_MAX / q;
    z->bias128 = (ca_u128)K * q;
    if (A->rows >= (uint32_t)1 << 31 || A->cols >= (uint32_t)1 << 31 || A->nnz >= (uint32_t)1 << 31)
        return CA_OK;
    z->tcols = A->cols;
    z->tptr = calloc((size_t)A->cols + 1, sizeof(uint32_t));
    z->tcol = malloc((A->nnz ? A->nnz : 1) * sizeof(uint32_t));
    z->tval = malloc((A->nnz ? A->nnz : 1) * sizeof(int32_t));
    if (!z->tptr || !z->tcol || !z->tval) {
        lz_free(z);
        return CA_ERR_NOMEM;
    }
    for (uint32_t k = 0; k < A->nnz; k++) z->tptr[A->col[k] + 1]++;
    for (uint32_t j = 0; j < A->cols; j++) z->tptr[j + 1] += z->tptr[j];
    /* rows in increasing order within each column: the sum is exact, so
     * the order does not matter, but it keeps the gather sequential */
    uint32_t *fill = malloc((A->cols ? A->cols : 1) * sizeof(uint32_t));
    if (!fill) {
        lz_free(z);
        return CA_ERR_NOMEM;
    }
    memcpy(fill, z->tptr, A->cols * sizeof(uint32_t));
    for (uint32_t i = 0; i < A->rows; i++) {
        for (uint32_t k = A->row_ptr[i]; k < A->row_ptr[i + 1]; k++) {
            uint32_t slot = fill[A->col[k]]++;
            z->tcol[slot] = i;
            z->tval[slot] = A->val[k];
        }
    }
    free(fill);
    uint32_t heavy_t = 0;
    if (!lz_gat_build(&z->gt, z->tcols, z->tptr, z->tcol, z->tval, A->nnz, A->rows, light_sum,
                      &heavy_t) ||
        !lz_gat_build(&z->ga, A->rows, A->row_ptr, A->col, A->val, A->nnz, A->cols, light_sum,
                      &z->heavy_a)) {
        lz_free(z);
        return CA_ERR_NOMEM;
    }
    z->fast = 1;
    return CA_OK;
}

/* y = D (A v) mod q, D == NULL for none (v has its negation behind it for
 * the gather kernels, y gets q - y into yn when given); DR_i = 2^64 D_i mod q (with its
 * Shoup constants DRp) for the 128-bit gather. */
static void lz_av(const lz_ctx *z, const ca_spmat *A, const uint64_t *v, uint64_t *y, uint64_t *yn,
                  const uint64_t *D, const uint64_t *Dp, const uint64_t *DR, const uint64_t *DRp)
{
    if (z->fast) {
        lz_spmv(z, &z->ga, 0, A->rows, v, y, yn, D, Dp, D ? DR : NULL, DRp);
        return;
    }
    spmv(A, v, y, z->q);
    if (!D) return;
    if (z->q < ((uint64_t)1 << 63)) {
        for (uint32_t i = 0; i < A->rows; i++) y[i] = shoup_mul(y[i], D[i], Dp[i], z->q);
    } else {
        for (uint32_t i = 0; i < A->rows; i++) y[i] = ca_mulmod(y[i], D[i], z->q);
    }
}

/* z = A^T w mod q. */
static void lz_atw(const lz_ctx *z, const ca_spmat *A, const uint64_t *w, uint64_t *out,
                   ca_i128 *acc)
{
    if (z->fast)
        lz_spmv(z, &z->gt, 0, z->tcols, w, out, NULL, NULL, NULL, NULL, NULL);
    else
        spmtv(A, w, out, z->q, acc);
}

/* ---- the Lanczos thread pool ------------------------------------------- */

/*
 * The products A v and A^T w of a Lanczos step, its three dot products and
 * its vector update, split across a persistent pool of threads: started
 * on first use, reused by every step of every attempt of every solve, and
 * asleep in between.
 *
 * Determinism: each thread owns a block of output rows (rows of A for A v;
 * rows of A^T, which are the coordinates of the n-vectors, for A^T w, the
 * dot products and the update), so no element is written by two threads,
 * and every element is the same exact residue mod q as in the one-thread
 * code.  The dot products are exact sums mod q: each thread reduces its
 * block to residues and the main thread adds the per-thread residues in
 * thread order, which gives the one-thread residue whatever the partition.
 * Nothing the solver reports (iterations, attempts, the solution) depends
 * on the thread count.
 *
 * Synchronisation: a step is far shorter than a condition-variable round
 * trip at the sizes index calculus produces (784 x 700 matrices are a few
 * microseconds a product), so the main thread publishes a job by bumping
 * a generation counter and the workers spin on it, falling asleep on a
 * condition variable only after a long idle spell (between solves, during
 * the dense fallback).  The blocks of a job are claimed from an atomic
 * counter by whichever thread gets there first, the main thread included,
 * so a worker the scheduler has not run yet (a busy or oversubscribed
 * host) costs nothing: the main thread does its block.  Which thread runs
 * a block never changes what the block computes.
 */

enum { LZ_JOB_AV = 1, LZ_JOB_ATW_DOT, LZ_JOB_ATW, LZ_JOB_UPDATE };

#define LZ_MAX_THREADS        64u
#define LZ_MIN_NNZ_PER_THREAD 512u       /* below this a block is not worth a thread */
#define LZ_WORKER_SPINS       (1u << 11) /* pause loops (tens of microseconds) before a worker sleeps */
#define LZ_MAIN_SPINS         (1u << 12) /* pause loops before the main thread yields */

typedef struct lz_job {
    int kind;
    const lz_ctx *z;
    const ca_spmat *A;
    /* LZ_JOB_AV: y = D (A v) */
    const uint64_t *v, *D, *Dp, *DR, *DRp;
    uint64_t *y, *yn;
    /* LZ_JOB_ATW[_DOT]: out = A^T w; dots of (wc, out, bp) */
    const uint64_t *w, *wc, *bp;
    uint64_t *out;
    /* LZ_JOB_UPDATE */
    uint64_t *x, *wn;
    uint32_t n; /* length of wn's plain half; its negation follows */
    const uint64_t *wp, *Bw;
    uint64_t coef, coefp, c1, c1p, c2, c2p;
} lz_job;

typedef struct lz_pool lz_pool;

typedef struct lz_worker {
    lz_pool *P;
    uint32_t id;
    uint32_t gen0; /* the generation when the worker was started */
} lz_worker;

struct lz_pool {
    uint32_t T;        /* blocks per job (threads used) for the current solve */
    uint32_t nthreads; /* threads started, the caller included */
    uint32_t pgen;     /* generation of the last job (written under lz_pool_lock) */
    pthread_t tids[LZ_MAX_THREADS];
    lz_worker args[LZ_MAX_THREADS];
    pthread_mutex_t mu;
    pthread_cond_t cv;
    uint32_t sleepers; /* under mu */
    /* (generation << 32) | (blocks << 16) | next unclaimed block: a claim
     * names the job it belongs to, so a worker that wakes after its job is
     * over can never take a block of the next one, and it reads the block
     * count from the same word */
    _Atomic uint64_t ticket;
    _Atomic uint32_t done; /* blocks of the current job finished */
    lz_job job;
    uint32_t arow[LZ_MAX_THREADS + 1]; /* block bounds over the rows of A */
    uint32_t trow[LZ_MAX_THREADS + 1]; /* ... over the rows of A^T (coordinates) */
    uint64_t dots[LZ_MAX_THREADS][8];  /* per-block dot residues, a cache line each */
};

static inline void lz_relax(void)
{
#if defined(__x86_64__) || defined(__i386__)
    __builtin_ia32_pause();
#elif defined(__aarch64__)
    __asm__ __volatile__("yield");
#endif
}

/* Block bounds over the rows of a CSR matrix, balanced by nonzeros plus
 * one per row (the per-row reduction). */
static void lz_split(uint32_t rows, const uint32_t *ptr, uint32_t T, uint32_t *bounds)
{
    const uint64_t total = (uint64_t)ptr[rows] + rows;
    uint32_t i = 0;
    bounds[0] = 0;
    for (uint32_t t = 1; t < T; t++) {
        const uint64_t want = total * t / T;
        while (i < rows && (uint64_t)ptr[i] + i < want) i++;
        bounds[t] = i;
    }
    bounds[T] = rows;
}

/* The vector update of a Lanczos step over coordinates [j0, j1):
 * x += coef w_cur, w_next = Bw - c1 w_cur - c2 w_prev, and, when the gather
 * kernels read w_next (neg), its negation q - w_next into wnn.  neg is a
 * constant in each of the two copies. */
static inline __attribute__((always_inline)) void
lz_update_body(uint64_t q, uint32_t j0, uint32_t j1, uint64_t *x, uint64_t *wn, uint64_t *wnn,
               const uint64_t *wc, const uint64_t *wp, const uint64_t *Bw, uint64_t coef,
               uint64_t coefp, uint64_t c1, uint64_t c1p, uint64_t c2, uint64_t c2p, int neg)
{
    if (c2) {
        for (uint32_t j = j0; j < j1; j++) {
            const uint64_t wj = wc[j];
            x[j] = ca_addmod(x[j], shoup_mul(wj, coef, coefp, q), q);
            uint64_t t = ca_submod(Bw[j], shoup_mul(wj, c1, c1p, q), q);
            wn[j] = ca_submod(t, shoup_mul(wp[j], c2, c2p, q), q);
            if (neg) wnn[j] = q - wn[j];
        }
    } else {
        for (uint32_t j = j0; j < j1; j++) {
            const uint64_t wj = wc[j];
            x[j] = ca_addmod(x[j], shoup_mul(wj, coef, coefp, q), q);
            wn[j] = ca_submod(Bw[j], shoup_mul(wj, c1, c1p, q), q);
            if (neg) wnn[j] = q - wn[j];
        }
    }
}

static void lz_update(int neg, uint64_t q, uint32_t j0, uint32_t j1, uint32_t n, uint64_t *x,
                      uint64_t *wn, const uint64_t *wc, const uint64_t *wp, const uint64_t *Bw,
                      uint64_t coef, uint64_t coefp, uint64_t c1, uint64_t c1p, uint64_t c2,
                      uint64_t c2p)
{
    if (neg)
        lz_update_body(q, j0, j1, x, wn, wn + n, wc, wp, Bw, coef, coefp, c1, c1p, c2, c2p, 1);
    else
        lz_update_body(q, j0, j1, x, wn, wn + n, wc, wp, Bw, coef, coefp, c1, c1p, c2, c2p, 0);
}

static void lz_run_block(lz_pool *P, uint32_t t)
{
    const lz_job *J = &P->job;
    const lz_ctx *z = J->z;
    switch (J->kind) {
    case LZ_JOB_AV: {
        const uint32_t r0 = P->arow[t], r1 = P->arow[t + 1];
        lz_spmv(z, &z->ga, r0, r1 - r0, J->v, J->y + r0, J->yn ? J->yn + r0 : NULL,
                J->D ? J->D + r0 : NULL, J->D ? J->Dp + r0 : NULL, J->DR ? J->DR + r0 : NULL,
                J->DR ? J->DRp + r0 : NULL);
        break;
    }
    case LZ_JOB_ATW:
    case LZ_JOB_ATW_DOT: {
        const uint32_t r0 = P->trow[t], r1 = P->trow[t + 1];
        lz_spmv(z, &z->gt, r0, r1 - r0, J->w, J->out + r0, NULL, NULL, NULL, NULL, NULL);
        /* the coordinates this block just wrote are the ones it dots */
        if (J->kind == LZ_JOB_ATW_DOT)
            vdot3(z, J->wc + r0, J->out + r0, J->bp + r0, r1 - r0, P->dots[t]);
        break;
    }
    case LZ_JOB_UPDATE: {
        const uint32_t j0 = P->trow[t], j1 = P->trow[t + 1];
        lz_update(z->fast, z->q, j0, j1, J->n, J->x, J->wn, J->wc, J->wp, J->Bw, J->coef, J->coefp,
                  J->c1, J->c1p, J->c2, J->c2p);
        break;
    }
    default: break;
    }
}

/* Claim and run blocks of job generation g until none is left.  A
 * successful claim reads the ticket the main thread published (release)
 * after writing the job, so it sees the whole job. */
static void lz_claim_blocks(lz_pool *P, uint32_t g)
{
    uint64_t t = atomic_load_explicit(&P->ticket, memory_order_acquire);
    for (;;) {
        if ((uint32_t)(t >> 32) != g) return; /* a later job: not ours */
        const uint32_t blk = (uint32_t)t & 0xffffu, nblk = ((uint32_t)t >> 16) & 0xffffu;
        if (blk >= nblk) return;
        if (!atomic_compare_exchange_weak_explicit(&P->ticket, &t, t + 1, memory_order_acq_rel,
                                                   memory_order_acquire))
            continue; /* t reloaded */
        lz_run_block(P, blk);
        atomic_fetch_add_explicit(&P->done, 1, memory_order_release);
        t = atomic_load_explicit(&P->ticket, memory_order_acquire);
    }
}

static inline uint32_t lz_gen(lz_pool *P)
{
    return (uint32_t)(atomic_load_explicit(&P->ticket, memory_order_acquire) >> 32);
}

/* pthread_create fixes the start routine as void *(*)(void *), so arg stays
 * non-const even though the worker only reads through it. */
// cppcheck-suppress constParameterCallback
static void *lz_worker_main(void *arg)
{
    const lz_worker *W = arg;
    lz_pool *P = W->P;
    uint32_t seen = W->gen0;
    for (;;) {
        uint32_t g;
        uint32_t spins = 0;
        while ((g = lz_gen(P)) == seen) {
            if (++spins < LZ_WORKER_SPINS) {
                lz_relax();
                continue;
            }
            pthread_mutex_lock(&P->mu);
            P->sleepers++;
            while (lz_gen(P) == seen) pthread_cond_wait(&P->cv, &P->mu);
            P->sleepers--;
            pthread_mutex_unlock(&P->mu);
            spins = 0;
        }
        seen = g;
        lz_claim_blocks(P, g);
    }
    return NULL;
}

/* Run P->job on P->T blocks and return when all are done.  Every block of
 * the previous job is finished here, so no thread still reads P->job. */
static void lz_pool_run(lz_pool *P)
{
    const uint32_t g = ++P->pgen;
    atomic_store_explicit(&P->done, 0, memory_order_relaxed);
    pthread_mutex_lock(&P->mu);
    atomic_store_explicit(&P->ticket, (uint64_t)g << 32 | (uint64_t)P->T << 16,
                          memory_order_release);
    if (P->sleepers) pthread_cond_broadcast(&P->cv);
    pthread_mutex_unlock(&P->mu);
    lz_claim_blocks(P, g);
    uint32_t spins = 0;
    while (atomic_load_explicit(&P->done, memory_order_acquire) != P->T) {
        if (++spins < LZ_MAIN_SPINS)
            lz_relax();
        else
            sched_yield(); /* a worker was preempted mid-block: let it run */
    }
}

/* One pool per process, grown on demand and never torn down: its workers
 * sleep on the condition variable between solves, so a solve neither
 * starts nor joins threads (on a busy host, joining a descheduled worker
 * costs a scheduler time slice).  One solve uses it at a time; a solve
 * that finds it busy (solves running concurrently in several threads)
 * takes the one-thread path, which computes the same result. */
static pthread_mutex_t lz_pool_lock = PTHREAD_MUTEX_INITIALIZER;
static lz_pool *lz_pool_global;

/* The pool with T >= 2 blocks for a matrix with nnz nonzeros, held until
 * lz_pool_release, or NULL for the one-thread path (threads <= 1, a small
 * matrix, the pool busy, or no memory or threads to be had). */
static lz_pool *lz_pool_acquire(uint32_t threads, uint32_t nnz)
{
    if (threads > LZ_MAX_THREADS) threads = LZ_MAX_THREADS;
    /* spinning threads beyond the online CPUs only take turns */
    const long ncpu = sysconf(_SC_NPROCESSORS_ONLN);
    if (ncpu > 0 && threads > (uint32_t)ncpu) threads = (uint32_t)ncpu;
    const uint32_t cap = nnz / LZ_MIN_NNZ_PER_THREAD;
    if (threads > cap) threads = cap;
    if (threads <= 1) return NULL;
    if (pthread_mutex_trylock(&lz_pool_lock) != 0) return NULL;
    lz_pool *P = lz_pool_global;
    if (!P) {
        P = calloc(1, sizeof(*P));
        if (!P) {
            pthread_mutex_unlock(&lz_pool_lock);
            return NULL;
        }
        pthread_mutex_init(&P->mu, NULL);
        pthread_cond_init(&P->cv, NULL);
        atomic_init(&P->ticket, 0);
        atomic_init(&P->done, 0);
        P->nthreads = 1;
        lz_pool_global = P;
    }
    /* the workers are idle (no job since the last solve finished), so
     * starting more cannot race with one */
    while (P->nthreads < threads) {
        const uint32_t t = P->nthreads;
        P->args[t].P = P;
        P->args[t].id = t;
        P->args[t].gen0 = P->pgen;
        pthread_attr_t attr;
        pthread_attr_init(&attr);
        pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED);
        const int rc = pthread_create(&P->tids[t], &attr, lz_worker_main, &P->args[t]);
        pthread_attr_destroy(&attr);
        if (rc != 0) break;
        P->nthreads++;
    }
    P->T = threads < P->nthreads ? threads : P->nthreads;
    if (P->T <= 1) {
        pthread_mutex_unlock(&lz_pool_lock);
        return NULL;
    }
    return P;
}

static void lz_pool_release(const lz_pool *P)
{
    if (P) pthread_mutex_unlock(&lz_pool_lock);
}

/* The thread count a solve uses: CA_LA_THREADS when set to a positive
 * integer (a measurement knob: it overrides the caller), else the
 * caller's, 0 meaning 1. */
static uint32_t lz_threads(uint32_t requested)
{
    const char *env = getenv("CA_LA_THREADS");
    if (env && *env) {
        char *end = NULL;
        unsigned long v = strtoul(env, &end, 10);
        if (end && *end == '\0' && v >= 1) return v > LZ_MAX_THREADS ? LZ_MAX_THREADS : (uint32_t)v;
    }
    return requested ? requested : 1;
}

/* y = D (A v) through the pool when there is one. */
static void lz_av_p(lz_pool *P, const lz_ctx *z, const ca_spmat *A, const uint64_t *v, uint64_t *y,
                    uint64_t *yn, const uint64_t *D, const uint64_t *Dp, const uint64_t *DR,
                    const uint64_t *DRp)
{
    if (!P || !z->fast) {
        lz_av(z, A, v, y, yn, D, Dp, DR, DRp);
        return;
    }
    lz_job *J = &P->job;
    J->kind = LZ_JOB_AV;
    J->z = z;
    J->A = A;
    J->v = v;
    J->y = y;
    J->yn = yn;
    J->D = D;
    J->Dp = Dp;
    J->DR = DR;
    J->DRp = DRp;
    lz_pool_run(P);
}

/* out = A^T w through the pool when there is one. */
static void lz_atw_p(lz_pool *P, const lz_ctx *z, const ca_spmat *A, const uint64_t *w,
                     uint64_t *out, ca_i128 *acc)
{
    if (!P || !z->fast) {
        lz_atw(z, A, w, out, acc);
        return;
    }
    lz_job *J = &P->job;
    J->kind = LZ_JOB_ATW;
    J->z = z;
    J->w = w;
    J->out = out;
    lz_pool_run(P);
}

/*
 * Lanczos on B = A^T D A with random diagonal D, solving B x = A^T D b.
 * Returns CA_OK if A x == b verified, CA_ERR_SINGULAR on breakdown.
 */
static ca_status lanczos(const ca_spmat *A, const uint64_t *b, uint64_t q, uint64_t *x, ca_rng *rng,
                         uint32_t *iters_out, lz_pool *P0)
{
    lz_pool *P = P0;
    uint32_t n = A->cols, m = A->rows;
    uint64_t *D = malloc(m * sizeof(uint64_t));
    uint64_t *Dp = malloc(m * sizeof(uint64_t)); /* Shoup constants of D */
    const int shoup = q < ((uint64_t)1 << 63);
    /* the vectors the gather kernels read (w0..w2, tmp_m) carry their
     * negation q - v behind them: 2n and 2m entries */
    uint64_t *tmp_m = malloc(2 * (size_t)m * sizeof(uint64_t));
    uint64_t *bp = calloc(n, sizeof(uint64_t)); /* A^T D b */
    uint64_t *w0 = calloc(2 * (size_t)n, sizeof(uint64_t));
    uint64_t *w1 = calloc(2 * (size_t)n, sizeof(uint64_t));
    uint64_t *w2 = calloc(2 * (size_t)n, sizeof(uint64_t));
    uint64_t *Bw = calloc(n, sizeof(uint64_t));
    ca_i128 *acc = malloc(n * sizeof(ca_i128));
    uint64_t *DR = NULL, *DRp = NULL; /* 2^64 D_i mod q, for the 128-bit gather */
    ca_status rc = CA_ERR_SINGULAR;
    lz_ctx z;
    memset(&z, 0, sizeof(z));
    if (!D || !Dp || !tmp_m || !bp || !w0 || !w1 || !w2 || !Bw || !acc) {
        rc = CA_ERR_NOMEM;
        goto out;
    }
    if (lz_init(&z, A, q) != CA_OK) {
        rc = CA_ERR_NOMEM;
        goto out;
    }
    /* the pool runs the gather kernels only; the scatter fallback stays on
     * one thread */
    if (P0 && !z.fast) P0 = P = NULL;
    if (P0) {
        lz_split(m, A->row_ptr, P0->T, P0->arow);
        lz_split(n, z.tptr, P0->T, P0->trow);
    }
    /* Pool or one thread, chosen by the clock: LZ_PROBE steps on one
     * thread, LZ_PROBE on the pool, then up to LZ_RUN windows of LZ_PROBE
     * steps on the faster, and again; a pool window slower than the
     * one-thread probe by a quarter re-probes at once.  The pool probe
     * starts its clock after one untimed step, which wakes the workers.  On a busy host a
     * spinning pool can lose to one thread (a preempted worker holds up
     * every step).  Both paths compute the same residues, so the choice
     * changes the time only, never the result. */
    enum { LZ_PROBE = 16, LZ_RUN = 32 };
    int phase = 0, pool_wins = 1, warm = 0;
    uint32_t left = LZ_PROBE, windows = 0;
    double t_phase = P0 ? ca_now() : 0, t_one = 0;
    for (uint32_t i = 0; i < m; i++) {
        D[i] = 1 + ca_rng_below(rng, q - 1);
        Dp[i] = shoup ? shoup_pre(D[i], q) : 0;
    }
    if (z.heavy_a) {
        DR = malloc((m ? m : 1) * sizeof(uint64_t));
        DRp = malloc((m ? m : 1) * sizeof(uint64_t));
        if (!DR || !DRp) {
            rc = CA_ERR_NOMEM;
            goto out;
        }
        for (uint32_t i = 0; i < m; i++) {
            DR[i] = shoup_mul(z.r64, D[i], Dp[i], q);
            DRp[i] = shoup_pre(DR[i], q);
        }
    }
    for (uint32_t i = 0; i < m; i++) {
        tmp_m[i] = ca_mulmod(D[i], b[i] % q, q);
        tmp_m[m + i] = q - tmp_m[i];
    }
    lz_atw_p(P, &z, A, tmp_m, bp, acc);
    memset(x, 0, n * sizeof(uint64_t));
    /* w_prev = w0 (i-1), w_cur = w1 (i) */
    uint64_t *w_prev = w0, *w_cur = w1, *w_next = w2;
    memcpy(w_cur, bp, n * sizeof(uint64_t));
    for (uint32_t j = 0; j < n; j++) w_cur[n + j] = q - w_cur[j];
    uint64_t prev_wBw = 0;
    uint32_t it = 0;
    for (it = 0; it < n + 8; it++) {
        if (P0) P = (phase == 1 || (phase == 2 && pool_wins)) ? P0 : NULL;
        /* Bw = A^T D A w_cur */
        uint64_t dots[3];
        if (P) {
            lz_av_p(P, &z, A, w_cur, tmp_m, tmp_m + m, D, Dp, DR, DRp);
            lz_job *J = &P->job;
            J->kind = LZ_JOB_ATW_DOT;
            J->z = &z;
            J->w = tmp_m;
            J->out = Bw;
            J->wc = w_cur;
            J->bp = bp;
            lz_pool_run(P);
            /* per-block residues added in block order: the exact sum mod q */
            dots[0] = dots[1] = dots[2] = 0;
            for (uint32_t t = 0; t < P->T; t++)
                for (int k = 0; k < 3; k++) dots[k] = ca_addmod(dots[k], P->dots[t][k], q);
        } else {
            lz_av(&z, A, w_cur, tmp_m, tmp_m + m, D, Dp, DR, DRp);
            lz_atw(&z, A, tmp_m, Bw, acc);
            vdot3(&z, w_cur, Bw, bp, n, dots);
        }
        uint64_t wBw = dots[0];
        int zero = 1;
        for (uint32_t j = 0; j < n; j++) if (w_cur[j]) { zero = 0; break; }
        if (zero) { rc = CA_OK; break; }
        if (wBw == 0) { rc = CA_ERR_SINGULAR; break; } /* breakdown */
        uint64_t inv = ca_invmod(wBw, q);
        /* x += (w . bp) / (w . Bw) * w */
        uint64_t coef = ca_mulmod(dots[1], inv, q);
        /* w_next = Bw - c1 w_cur - c2 w_prev */
        uint64_t c1 = ca_mulmod(dots[2], inv, q);
        uint64_t c2 = prev_wBw ? ca_mulmod(wBw, ca_invmod(prev_wBw, q), q) : 0;
        if (shoup) {
            /* coef, c1 and c2 are fixed for the whole vector update */
            const uint64_t coefp = shoup_pre(coef, q), c1p = shoup_pre(c1, q),
                           c2p = shoup_pre(c2, q);
            /* one pass: x and w_next both read w_cur */
            if (P) {
                lz_job *J = &P->job;
                J->kind = LZ_JOB_UPDATE;
                J->z = &z;
                J->x = x;
                J->wn = w_next;
                J->n = n;
                J->wc = w_cur;
                J->wp = w_prev;
                J->Bw = Bw;
                J->coef = coef;
                J->coefp = coefp;
                J->c1 = c1;
                J->c1p = c1p;
                J->c2 = c2;
                J->c2p = c2p;
                lz_pool_run(P);
            } else {
                lz_update(z.fast, q, 0, n, n, x, w_next, w_cur, w_prev, Bw, coef, coefp, c1, c1p,
                          c2, c2p);
            }
        } else {
            for (uint32_t j = 0; j < n; j++)
                x[j] = ca_addmod(x[j], ca_mulmod(coef, w_cur[j], q), q);
            for (uint32_t j = 0; j < n; j++) {
                uint64_t t = ca_submod(Bw[j], ca_mulmod(c1, w_cur[j], q), q);
                if (c2) t = ca_submod(t, ca_mulmod(c2, w_prev[j], q), q);
                w_next[j] = t;
            }
        }
        prev_wBw = wBw;
        uint64_t *t = w_prev; w_prev = w_cur; w_cur = w_next; w_next = t;
        if (P0 && phase == 1 && warm) {
            warm = 0;
            t_phase = ca_now();
        } else if (P0 && --left == 0) {
            const double now = ca_now();
            if (phase == 0) {
                t_one = now - t_phase;
                phase = 1;
                warm = 1;
            } else if (phase == 1) {
                pool_wins = now - t_phase < t_one;
                phase = 2;
                windows = LZ_RUN;
            } else if (--windows == 0 || (pool_wins && (now - t_phase) * 4 > t_one * 5)) {
                phase = 0;
            }
            left = LZ_PROBE;
            t_phase = now;
        }
    }
    P = P0 && pool_wins ? P0 : NULL;
    if (rc == CA_OK) {
        /* verify A x == b */
        /* w_next is free: x with its negation behind it */
        memcpy(w_next, x, n * sizeof(uint64_t));
        for (uint32_t j = 0; j < n; j++) w_next[n + j] = q - x[j];
        lz_av_p(P, &z, A, w_next, tmp_m, NULL, NULL, NULL, NULL, NULL);
        for (uint32_t i = 0; i < m; i++) {
            if (tmp_m[i] != b[i] % q) { rc = CA_ERR_SINGULAR; break; }
        }
    }
    if (iters_out) *iters_out = it;
out:
    lz_free(&z);
    free(DR);
    free(DRp);
    free(D);
    free(Dp);
    free(tmp_m);
    free(bp);
    free(w0);
    free(w1);
    free(w2);
    free(Bw);
    free(acc);
    return rc;
}

/* ---- structured elimination + driver ----------------------------------- */

ca_status ca_linsolve_mod_prime(const ca_spmat *A, const uint64_t *b, uint64_t q, uint64_t *x,
                                uint8_t *known, uint64_t seed, ca_linsolve_report *rep)
{
    return ca_linsolve_mod_prime_mt(A, b, q, x, known, seed, 1, rep);
}

ca_status ca_linsolve_mod_prime_mt(const ca_spmat *A, const uint64_t *b, uint64_t q, uint64_t *x,
                                   uint8_t *known, uint64_t seed, uint32_t threads,
                                   ca_linsolve_report *rep)
{
    if (!A || !b || !x || !known) {
        ca_set_error("linsolve: null input or output");
        return CA_ERR_INVALID;
    }
    double t0 = ca_now();
    uint32_t R = A->rows, C = A->cols;
    ca_linsolve_report lrep = {0};
    uint8_t *row_alive = malloc(R);
    uint8_t *col_alive = malloc(C);
    uint32_t *colw = calloc(C, sizeof(uint32_t));
    uint32_t *stack = malloc(R * sizeof(uint32_t)); /* dropped singleton rows in order */
    uint32_t *stack_col = malloc(R * sizeof(uint32_t));
    uint32_t nstack = 0;
    ca_status rc = CA_OK;
    if (!row_alive || !col_alive || !colw || !stack || !stack_col) { rc = CA_ERR_NOMEM; goto out; }
    memset(row_alive, 1, R);
    memset(col_alive, 1, C);
    memset(known, 0, C);
    memset(x, 0, C * sizeof(uint64_t));
    ca_rng rng;
    ca_rng_seed(&rng, ca_seed_or_random(seed));

    uint32_t maxlen = 0; /* longest row: bounds the per-row scratch below */
    for (uint32_t i = 0; i < R; i++) {
        uint32_t len = A->row_ptr[i + 1] - A->row_ptr[i];
        if (len > maxlen) maxlen = len;
        for (uint32_t k = A->row_ptr[i]; k < A->row_ptr[i + 1]; k++) colw[A->col[k]]++;
    }
    /* iterate singleton removal to a fixed point */
    int changed = 1;
    while (changed) {
        changed = 0;
        for (uint32_t i = 0; i < R; i++) {
            if (!row_alive[i]) continue;
            for (uint32_t k = A->row_ptr[i]; k < A->row_ptr[i + 1]; k++) {
                uint32_t j = A->col[k];
                if (col_alive[j] && colw[j] == 1) {
                    /* row i is the only row containing j: remove both, and
                     * solve for j later by back substitution */
                    row_alive[i] = 0;
                    col_alive[j] = 0;
                    stack[nstack] = i;
                    stack_col[nstack] = j;
                    nstack++;
                    for (uint32_t k2 = A->row_ptr[i]; k2 < A->row_ptr[i + 1]; k2++) colw[A->col[k2]]--;
                    changed = 1;
                    break;
                }
            }
        }
    }
    for (uint32_t j = 0; j < C; j++) if (colw[j] == 0) col_alive[j] = 0;

    /* build the reduced system */
    uint32_t *cmap = malloc(C * sizeof(uint32_t));
    uint32_t nc = 0;
    if (!cmap) { rc = CA_ERR_NOMEM; goto out; }
    for (uint32_t j = 0; j < C; j++) cmap[j] = col_alive[j] ? nc++ : UINT32_MAX;
    ca_spmat Ared;
    uint32_t nr = 0;
    for (uint32_t i = 0; i < R; i++) nr += row_alive[i];
    if (ca_spmat_init(&Ared, nc, nr, A->nnz) != CA_OK) { free(cmap); rc = CA_ERR_NOMEM; goto out; }
    uint64_t *bred = malloc((nr ? nr : 1) * sizeof(uint64_t));
    uint32_t *tc = malloc((maxlen ? maxlen : 1) * sizeof(uint32_t));
    int32_t *tv = malloc((maxlen ? maxlen : 1) * sizeof(int32_t));
    uint64_t *xred = calloc(nc ? nc : 1, sizeof(uint64_t));
    if (!bred || !tc || !tv || !xred) { rc = CA_ERR_NOMEM; goto out2; }
    {
        uint32_t ri = 0;
        for (uint32_t i = 0; i < R; i++) {
            if (!row_alive[i]) continue;
            uint32_t n = 0;
            for (uint32_t k = A->row_ptr[i]; k < A->row_ptr[i + 1]; k++) {
                if (cmap[A->col[k]] == UINT32_MAX) continue; /* cannot happen: dropped cols only in dropped rows */
                /* n < maxlen by construction; checked anyway so an
                 * inconsistent row_ptr cannot run off the scratch row. */
                if (n >= maxlen) {
                    rc = CA_ERR_INTERNAL;
                    goto out2;
                }
                tc[n] = cmap[A->col[k]];
                tv[n] = A->val[k];
                n++;
            }
            if (n == 0) continue;
            if (ca_spmat_add_row(&Ared, tc, tv, n) != CA_OK) { rc = CA_ERR_NOMEM; goto out2; }
            bred[ri++] = b[i] % q;
        }
        nr = ri;
    }
    lrep.active_rows = nr;
    lrep.active_cols = nc;
    if (nc > 0) {
        if (nr < nc) { rc = CA_ERR_SINGULAR; goto out2; }
        rc = CA_ERR_SINGULAR;
        /* one pool for every attempt; NULL keeps the one-thread path */
        lz_pool *pool = lz_pool_acquire(lz_threads(threads), Ared.nnz);
        for (int attempt = 0; attempt < 4 && rc != CA_OK; attempt++) {
            lrep.attempts++;
            rc = lanczos(&Ared, bred, q, xred, &rng, &lrep.lanczos_iters, pool);
            if (rc == CA_ERR_NOMEM) break;
        }
        lz_pool_release(pool);
        if (rc == CA_ERR_NOMEM) goto out2;
        if (rc != CA_OK && nc <= 1200) {
            /* dense fallback on the normal equations */
            lrep.used_dense = 1;
            uint64_t *M = calloc((size_t)nc * nc, sizeof(uint64_t));
            uint64_t *rhs = calloc(nc, sizeof(uint64_t));
            if (M && rhs) {
                /* M = A^T A, rhs = A^T b (mod q) */
                for (uint32_t i = 0; i < Ared.rows; i++) {
                    for (uint32_t k = Ared.row_ptr[i]; k < Ared.row_ptr[i + 1]; k++) {
                        uint64_t a = coef_mod(Ared.val[k], q);
                        uint32_t ja = Ared.col[k];
                        for (uint32_t l = Ared.row_ptr[i]; l < Ared.row_ptr[i + 1]; l++) {
                            uint64_t c = coef_mod(Ared.val[l], q);
                            M[(size_t)ja * nc + Ared.col[l]] =
                                ca_addmod(M[(size_t)ja * nc + Ared.col[l]], ca_mulmod(a, c, q), q);
                        }
                        rhs[ja] = ca_addmod(rhs[ja], ca_mulmod(a, bred[i], q), q);
                    }
                }
                rc = ca_dense_solve_mod_prime(M, nc, rhs, q, xred);
            } else rc = CA_ERR_NOMEM;
            free(M); free(rhs);
        }
        if (rc != CA_OK) goto out2;
    } else rc = CA_OK;
    for (uint32_t j = 0; j < C; j++) {
        if (cmap[j] != UINT32_MAX) { x[j] = xred[cmap[j]]; known[j] = 1; }
    }
    /* back-substitute singleton rows in reverse order */
    for (uint32_t s = nstack; s-- > 0;) {
        uint32_t i = stack[s], j = stack_col[s];
        uint64_t acc = b[i] % q;
        int64_t coef_j = 0;
        int ok = 1;
        for (uint32_t k = A->row_ptr[i]; k < A->row_ptr[i + 1]; k++) {
            uint32_t jj = A->col[k];
            if (jj == j) { coef_j = A->val[k]; continue; }
            if (!known[jj]) { ok = 0; break; }
            uint64_t c = coef_mod(A->val[k], q);
            acc = ca_submod(acc, ca_mulmod(c, x[jj], q), q);
        }
        if (!ok || coef_j == 0) continue;
        uint64_t cj = coef_mod(coef_j, q);
        uint64_t inv = ca_invmod(cj, q);
        if (!inv) continue;
        x[j] = ca_mulmod(acc, inv, q);
        known[j] = 1;
    }
out2:
    ca_spmat_free(&Ared);
    free(bred); free(tc); free(tv); free(xred); free(cmap);
out:
    free(row_alive); free(col_alive); free(colw); free(stack); free(stack_col);
    lrep.seconds = ca_now() - t0;
    if (rep) *rep = lrep;
    return rc;
}
