/*
 * linalg.c - structured Gaussian elimination + Lanczos modulo a prime.
 */
#include "linalg.h"
#include "ca_internal.h"

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
        uint32_t i = i0;
        for (; i + 2 <= i1; i += 2) acc += (ca_u128)a[i] * b[i] + (ca_u128)a[i + 1] * b[i + 1];
        if (i < i1) acc += (ca_u128)a[i] * b[i];
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

/* What one Lanczos call reads besides A: its transpose (A^T in CSR, built
 * once, so that A^T w is a row gather like A v rather than a scatter into
 * 128-bit column accumulators), whether the 64-bit kernels apply, and the
 * constants of the reductions. */
typedef struct lz_ctx {
    uint64_t q;
    int fast;       /* 0: the 128-bit scatter kernels; 1: 64-bit gathers; 2: 128-bit gathers */
    uint32_t tcols; /* rows of A^T = cols of A */
    uint32_t *tptr, *tcol; /* A^T in CSR */
    int32_t *tval;
    uint32_t dot_chunk; /* vdot terms summed in 128 bits between reductions */
    uint64_t r64, r64p; /* 2^64 mod q and its Shoup constant (q < 2^63) */
    uint64_t npi;       /* q^{-1} mod 2^64, for lz_redc */
    uint64_t onep;      /* Shoup constant of 1: floor(2^64 / q), a remainder by q */
    uint64_t bias64;    /* K q, K the largest row or column sum of |val| */
    ca_u128 bias128;    /* the same, for the 128-bit gather */
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

/* y_i = D_i * (sum_k val_k v[col_k]) mod q over the rows of a CSR matrix,
 * in signed 64-bit arithmetic; D == NULL leaves out the scaling.  lz_init
 * admits this only when K (2q - 1) < 2^64, K the largest row or column sum
 * of |val|: no partial sum overflows int64, and adding K q makes the sum
 * nonnegative and keeps it below 2^64, so its remainder is one Shoup
 * product by 1, no division.  The value is the exact (A v)_i mod q the
 * 128-bit kernels compute. */
static void spmv64(const lz_ctx *z, uint32_t rows, const uint32_t *ptr, const uint32_t *col,
                   const int32_t *val, const uint64_t *v, uint64_t *y, const uint64_t *D,
                   const uint64_t *Dp)
{
    const uint64_t q = z->q, onep = z->onep, bias = z->bias64;
    for (uint32_t i = 0; i < rows; i++) {
        uint32_t k = ptr[i];
        const uint32_t e = ptr[i + 1];
        int64_t acc = 0;
        /* two terms a step: the loop control is most of what a term costs */
        for (; k + 2 <= e; k += 2)
            acc +=
                (int64_t)val[k] * (int64_t)v[col[k]] + (int64_t)val[k + 1] * (int64_t)v[col[k + 1]];
        if (k < e) acc += (int64_t)val[k] * (int64_t)v[col[k]];
        /* a Shoup product reduces any 64-bit operand: by D_i when scaling,
         * by 1 otherwise */
        const uint64_t u = (uint64_t)acc + bias;
        y[i] = D ? shoup_mul(u, D[i], Dp[i], q) : shoup_mul(u, 1, onep, q);
    }
}

/* The same gather in signed 128-bit arithmetic, for moduli too large for
 * spmv64: every term is below 2^31 * 2^63 = 2^94 in size and lz_init
 * admits it only for rows of fewer than 2^31 terms, so the sum stays below
 * 2^125 and needs no intermediate reduction; the reduction is lz_u128_mod
 * of the sum plus K q (nonnegative), not the library's 128-bit remainder. */
static void spmv128(const lz_ctx *z, uint32_t rows, const uint32_t *ptr, const uint32_t *col,
                    const int32_t *val, const uint64_t *v, uint64_t *y, const uint64_t *DR,
                    const uint64_t *DRp)
{
    const uint64_t q = z->q;
    for (uint32_t i = 0; i < rows; i++) {
        uint32_t k = ptr[i];
        const uint32_t e = ptr[i + 1];
        ca_i128 acc = 0;
        /* v < q < 2^63: one signed 64 x 64 -> 128 product a term */
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
        /* acc >= -K (q - 1), so u = acc + K q is positive and below 2 K q <
         * q 2^64: its Montgomery reduction is u 2^-64 mod q, and the Shoup
         * product by 2^64 D_i mod q (2^64 mod q without the scaling) puts
         * back the 2^64 */
        const ca_u128 u = (ca_u128)acc + z->bias128;
        const uint64_t r = lz_redc(z, u);
        y[i] = DR ? shoup_mul(r, DR[i], DRp[i], q) : shoup_mul(r, z->r64, z->r64p, q);
    }
}

static void lz_free(lz_ctx *z)
{
    free(z->tptr);
    free(z->tcol);
    free(z->tval);
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
    /* level 1: K (2q - 1) < 2^64.  A row sum lies in [-K (q - 1), K (q - 1)],
     * so it fits in int64 (K (q - 1) < 2^63), and plus K q it lies in
     * [K, K (2q - 1)], nonnegative and below 2^64. */
    const uint64_t K = rmax > cmax ? rmax : cmax; /* below nnz 2^31 < 2^63 */
    const uint64_t lim = UINT64_MAX / (2 * q - 1);
    int level = K <= lim ? 1 : 2;
    z->bias64 = level == 1 ? K * q : 0;
    z->bias128 = (ca_u128)K * q;
    if (level == 2) {
        /* the 128-bit gather needs every row and column shorter than 2^31 */
        uint32_t lmax = 0;
        for (uint32_t i = 0; i < A->rows; i++)
            if (A->row_ptr[i + 1] - A->row_ptr[i] > lmax) lmax = A->row_ptr[i + 1] - A->row_ptr[i];
        uint32_t *cl = calloc(A->cols ? A->cols : 1, sizeof(uint32_t));
        if (!cl) return CA_ERR_NOMEM;
        for (uint32_t k = 0; k < A->nnz; k++)
            if (++cl[A->col[k]] > lmax) lmax = cl[A->col[k]];
        free(cl);
        if (lmax >= (uint32_t)1 << 31) return CA_OK;
    }
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
    z->fast = level;
    return CA_OK;
}

/* y = D (A v) mod q, D == NULL for none; DR_i = 2^64 D_i mod q (with its
 * Shoup constants DRp) for the 128-bit gather. */
static void lz_av(const lz_ctx *z, const ca_spmat *A, const uint64_t *v, uint64_t *y,
                  const uint64_t *D, const uint64_t *Dp, const uint64_t *DR, const uint64_t *DRp)
{
    if (z->fast == 1) {
        spmv64(z, A->rows, A->row_ptr, A->col, A->val, v, y, D, Dp);
        return;
    }
    if (z->fast == 2) {
        spmv128(z, A->rows, A->row_ptr, A->col, A->val, v, y, D ? DR : NULL, DRp);
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
    if (z->fast == 1)
        spmv64(z, z->tcols, z->tptr, z->tcol, z->tval, w, out, NULL, NULL);
    else if (z->fast == 2)
        spmv128(z, z->tcols, z->tptr, z->tcol, z->tval, w, out, NULL, NULL);
    else
        spmtv(A, w, out, z->q, acc);
}

/*
 * Lanczos on B = A^T D A with random diagonal D, solving B x = A^T D b.
 * Returns CA_OK if A x == b verified, CA_ERR_SINGULAR on breakdown.
 */
static ca_status lanczos(const ca_spmat *A, const uint64_t *b, uint64_t q, uint64_t *x,
                         ca_rng *rng, uint32_t *iters_out)
{
    uint32_t n = A->cols, m = A->rows;
    uint64_t *D = malloc(m * sizeof(uint64_t));
    uint64_t *Dp = malloc(m * sizeof(uint64_t)); /* Shoup constants of D */
    const int shoup = q < ((uint64_t)1 << 63);
    uint64_t *tmp_m = malloc(m * sizeof(uint64_t));
    uint64_t *bp = calloc(n, sizeof(uint64_t)); /* A^T D b */
    uint64_t *w0 = calloc(n, sizeof(uint64_t));
    uint64_t *w1 = calloc(n, sizeof(uint64_t));
    uint64_t *w2 = calloc(n, sizeof(uint64_t));
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
    for (uint32_t i = 0; i < m; i++) {
        D[i] = 1 + ca_rng_below(rng, q - 1);
        Dp[i] = shoup ? shoup_pre(D[i], q) : 0;
    }
    if (z.fast == 2) {
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
    for (uint32_t i = 0; i < m; i++) tmp_m[i] = ca_mulmod(D[i], b[i] % q, q);
    lz_atw(&z, A, tmp_m, bp, acc);
    memset(x, 0, n * sizeof(uint64_t));
    /* w_prev = w0 (i-1), w_cur = w1 (i) */
    uint64_t *w_prev = w0, *w_cur = w1, *w_next = w2;
    memcpy(w_cur, bp, n * sizeof(uint64_t));
    uint64_t prev_wBw = 0;
    uint32_t it = 0;
    for (it = 0; it < n + 8; it++) {
        /* Bw = A^T D A w_cur */
        lz_av(&z, A, w_cur, tmp_m, D, Dp, DR, DRp);
        lz_atw(&z, A, tmp_m, Bw, acc);
        uint64_t dots[3];
        vdot3(&z, w_cur, Bw, bp, n, dots);
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
            if (c2) {
                for (uint32_t j = 0; j < n; j++) {
                    const uint64_t wj = w_cur[j];
                    x[j] = ca_addmod(x[j], shoup_mul(wj, coef, coefp, q), q);
                    uint64_t t = ca_submod(Bw[j], shoup_mul(wj, c1, c1p, q), q);
                    w_next[j] = ca_submod(t, shoup_mul(w_prev[j], c2, c2p, q), q);
                }
            } else {
                for (uint32_t j = 0; j < n; j++) {
                    const uint64_t wj = w_cur[j];
                    x[j] = ca_addmod(x[j], shoup_mul(wj, coef, coefp, q), q);
                    w_next[j] = ca_submod(Bw[j], shoup_mul(wj, c1, c1p, q), q);
                }
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
    }
    if (rc == CA_OK) {
        /* verify A x == b */
        lz_av(&z, A, x, tmp_m, NULL, NULL, NULL, NULL);
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
        for (int attempt = 0; attempt < 4 && rc != CA_OK; attempt++) {
            lrep.attempts++;
            rc = lanczos(&Ared, bred, q, xred, &rng, &lrep.lanczos_iters);
            if (rc == CA_ERR_NOMEM) goto out2;
        }
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
