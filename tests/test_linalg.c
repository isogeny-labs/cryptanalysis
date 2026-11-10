#include "linalg.h"
#include "ca_internal.h"
#include "test_util.h"

static void random_system(uint32_t rows, uint32_t cols, uint32_t per_row, uint64_t q,
                          ca_spmat *A, uint64_t *b, uint64_t *xtrue, ca_rng *rng)
{
    for (uint32_t j = 0; j < cols; j++) xtrue[j] = ca_rng_below(rng, q);
    CHECK(ca_spmat_init(A, cols, rows, rows * per_row) == CA_OK);
    uint32_t *tc = malloc(per_row * sizeof(uint32_t));
    int32_t *tv = malloc(per_row * sizeof(int32_t));
    if (!tc || !tv) {
        CHECK(tc && tv);
        exit(EXIT_FAILURE);
    }
    for (uint32_t i = 0; i < rows; i++) {
        for (uint32_t k = 0; k < per_row; k++) {
            tc[k] = (uint32_t)ca_rng_below(rng, cols);
            tv[k] = (int32_t)(1 + ca_rng_below(rng, 5)) * ((ca_rng_next(rng) & 1) ? 1 : -1);
        }
        CHECK(ca_spmat_add_row(A, tc, tv, per_row) == CA_OK);
        /* b_i = sum val * x */
        uint64_t acc = 0;
        for (uint32_t k = A->row_ptr[i]; k < A->row_ptr[i + 1]; k++) {
            int32_t v = A->val[k];
            uint64_t c = v >= 0 ? (uint64_t)v % q : q - ((uint64_t)(-v) % q);
            acc = ca_addmod(acc, ca_mulmod(c, xtrue[A->col[k]], q), q);
        }
        b[i] = acc;
    }
    free(tc); free(tv);
}

int main(void)
{
    ca_rng rng;
    ca_rng_seed(&rng, 8);
    /* dense */
    {
        uint64_t q = 1000003;
        uint32_t n = 40;
        uint64_t *M = calloc((size_t)n * n, sizeof(uint64_t)), *rhs = calloc(n, sizeof(uint64_t));
        uint64_t *xt = calloc(n, sizeof(uint64_t)), *x = calloc(n, sizeof(uint64_t));
        if (!M || !rhs || !xt || !x) {
            CHECK(M && rhs && xt && x);
            exit(EXIT_FAILURE);
        }
        for (uint32_t j = 0; j < n; j++) xt[j] = ca_rng_below(&rng, q);
        for (uint32_t i = 0; i < n; i++) {
            for (uint32_t j = 0; j < n; j++) {
                M[i * n + j] = ca_rng_below(&rng, q);
                rhs[i] = ca_addmod(rhs[i], ca_mulmod(M[i * n + j], xt[j], q), q);
            }
        }
        CHECK(ca_dense_solve_mod_prime(M, n, rhs, q, x) == CA_OK);
        for (uint32_t j = 0; j < n; j++) CHECK_EQ_U64(x[j], xt[j]);
        free(M); free(rhs); free(xt); free(x);
    }
    /* dense with unreduced 64-bit entries, at the largest prime below 2^63
     * (the division-free path) and the largest below 2^64 (the fallback) */
    {
        const uint64_t dqs[] = {9223372036854775783ULL, 18446744073709551557ULL};
        for (size_t qi = 0; qi < 2; qi++) {
            uint64_t q = dqs[qi];
            uint32_t n = 60;
            uint64_t *M = calloc((size_t)n * n, sizeof(uint64_t)),
                     *rhs = calloc(n, sizeof(uint64_t));
            uint64_t *xt = calloc(n, sizeof(uint64_t)), *x = calloc(n, sizeof(uint64_t));
            if (!M || !rhs || !xt || !x) {
                CHECK(M && rhs && xt && x);
                exit(EXIT_FAILURE);
            }
            for (uint32_t j = 0; j < n; j++) xt[j] = ca_rng_below(&rng, q);
            for (uint32_t i = 0; i < n; i++) {
                uint64_t acc = 0;
                for (uint32_t j = 0; j < n; j++) {
                    M[i * n + j] = ca_rng_next(&rng);
                    acc = ca_addmod(acc, ca_mulmod(M[i * n + j] % q, xt[j], q), q);
                }
                rhs[i] = acc + (UINT64_MAX - acc) / q * q; /* unreduced, same residue */
            }
            CHECK(ca_dense_solve_mod_prime(M, n, rhs, q, x) == CA_OK);
            for (uint32_t j = 0; j < n; j++) CHECK_EQ_U64(x[j], xt[j]);
            free(M);
            free(rhs);
            free(xt);
            free(x);
        }
    }
    /* sparse: various sizes, big prime modulus */
    const uint64_t qs[] = {4294967311ULL, 1000000000000000003ULL, 18446744073709551557ULL};
    for (size_t qi = 0; qi < 3; qi++) {
        uint64_t q = qs[qi];
        uint32_t sizes[][2] = {{60, 40}, {700, 500}, {2600, 2000}};
        for (size_t s = 0; s < 3; s++) {
            uint32_t rows = sizes[s][0], cols = sizes[s][1];
            ca_spmat A;
            uint64_t *b = malloc(rows * sizeof(uint64_t));
            uint64_t *xt = malloc(cols * sizeof(uint64_t));
            uint64_t *x = malloc(cols * sizeof(uint64_t));
            uint8_t *known = malloc(cols);
            if (!b || !xt || !x || !known) {
                CHECK(b && xt && x && known);
                exit(EXIT_FAILURE);
            }
            random_system(rows, cols, 12, q, &A, b, xt, &rng);
            ca_linsolve_report rep;
            ca_status rc = ca_linsolve_mod_prime(&A, b, q, x, known, 5, &rep);
            CHECK(rc == CA_OK);
            uint32_t nk = 0, bad = 0;
            for (uint32_t j = 0; j < cols; j++) {
                if (!known[j]) continue;
                nk++;
                if (x[j] != xt[j]) bad++;
            }
            printf("q=%" PRIu64 " %ux%u: active %ux%u, iters %u, attempts %u, dense %d, known %u, wrong %u, %.3fs\n",
                   q, rows, cols, rep.active_rows, rep.active_cols, rep.lanczos_iters, rep.attempts,
                   rep.used_dense, nk, bad, rep.seconds);
            CHECK_EQ_U64(bad, 0);
            CHECK(nk >= cols * 9 / 10);
            ca_spmat_free(&A);
            free(b); free(xt); free(x); free(known);
        }
    }
    /* singleton chains: column appearing once must be recovered by back-substitution */
    {
        uint64_t q = 1000000007ULL;
        ca_spmat A;
        CHECK(ca_spmat_init(&A, 4, 4, 16) == CA_OK);
        const uint32_t c0[] = {0, 1};
        const int32_t v0[] = {1, 1}; /* x0 + x1 = 5 */
        const uint32_t c1[] = {1, 2};
        const int32_t v1[] = {2, -1}; /* 2x1 - x2 = 1 */
        const uint32_t c2[] = {1};
        const int32_t v2[] = {3}; /* 3x1 = 9 -> x1 = 3 */
        const uint32_t c3[] = {2, 3};
        const int32_t v3[] = {1, 1}; /* x2 + x3 = 12 */
        ca_spmat_add_row(&A, c0, v0, 2);
        ca_spmat_add_row(&A, c1, v1, 2);
        ca_spmat_add_row(&A, c2, v2, 1);
        ca_spmat_add_row(&A, c3, v3, 2);
        const uint64_t b[4] = {5, 1, 9, 12};
        uint64_t x[4];
        uint8_t known[4];
        CHECK(ca_linsolve_mod_prime(NULL, b, q, x, known, 1, NULL) == CA_ERR_INVALID);
        CHECK(ca_linsolve_mod_prime(&A, NULL, q, x, known, 1, NULL) == CA_ERR_INVALID);
        CHECK(ca_linsolve_mod_prime(&A, b, q, NULL, known, 1, NULL) == CA_ERR_INVALID);
        CHECK(ca_linsolve_mod_prime(&A, b, q, x, NULL, 1, NULL) == CA_ERR_INVALID);
        CHECK(ca_linsolve_mod_prime(&A, b, q, x, known, 1, NULL) == CA_OK);
        CHECK(known[0] && known[1] && known[2] && known[3]);
        CHECK_EQ_U64(x[0], 2); CHECK_EQ_U64(x[1], 3); CHECK_EQ_U64(x[2], 5); CHECK_EQ_U64(x[3], 7);
        ca_spmat_free(&A);
    }
    /* row_ptr capacity is per matrix: expected_rows is a hint, so a matrix may
     * grow past it, and one matrix growing must not let another skip its own
     * reallocation.  (The capacity used to be a file-scope static shared by
     * every matrix, and this sequence wrote past the small one's row_ptr.) */
    {
        const uint32_t c = 0;
        const int32_t v = 1;
        ca_spmat big, small;
        CHECK(ca_spmat_init(&big, 8, 10, 64) == CA_OK);
        for (uint32_t i = 0; i < 2000; i++) CHECK(ca_spmat_add_row(&big, &c, &v, 1) == CA_OK);
        CHECK(ca_spmat_init(&small, 8, 4, 64) == CA_OK); /* row_ptr starts with 5 slots */
        for (uint32_t i = 0; i < 10; i++) CHECK(ca_spmat_add_row(&small, &c, &v, 1) == CA_OK);
        CHECK_EQ_U64(big.rows, 2000);
        CHECK_EQ_U64(big.row_ptr[2000], 2000);
        CHECK_EQ_U64(small.rows, 10);
        CHECK_EQ_U64(small.row_ptr[10], 10);
        CHECK(small.row_cap >= 11);
        ca_spmat_free(&small);
        ca_spmat_free(&big);
    }
    /* The Lanczos pool: the solution, `known` and the report (iterations,
     * attempts, active size, dense fallback) are identical at every thread
     * count, for the 64-bit gather (q < 2^32), the 128-bit gather (q near
     * 2^60) and the one-thread scatter fallback (q near 2^64), including a
     * rank-deficient system (columns 0 and 1 always together with the same
     * coefficient) whose solve does not determine every unknown. */
    {
        const uint64_t tqs[] = {4294967311ULL, 1000000000000000003ULL, 18446744073709551557ULL};
        const uint32_t tsizes[][3] = {{1400, 1000, 10}, {3200, 2600, 8}, {1300, 1000, 8}};
        for (size_t qi = 0; qi < 3; qi++) {
            for (size_t s = 0; s < 3; s++) {
                const uint64_t q = tqs[qi];
                const uint32_t rows = tsizes[s][0], cols = tsizes[s][1];
                ca_spmat A;
                uint64_t *b = malloc(rows * sizeof(uint64_t));
                uint64_t *xt = malloc(cols * sizeof(uint64_t));
                uint64_t *x1 = malloc(cols * sizeof(uint64_t));
                uint64_t *xk = malloc(cols * sizeof(uint64_t));
                uint8_t *k1 = malloc(cols), *kk = malloc(cols);
                if (!b || !xt || !x1 || !xk || !k1 || !kk) {
                    CHECK(b && xt && x1 && xk && k1 && kk);
                    exit(EXIT_FAILURE);
                }
                random_system(rows, cols, tsizes[s][2], q, &A, b, xt, &rng);
                if (s == 2) {
                    /* rebuild with column 1 tied to column 0 */
                    ca_spmat B;
                    CHECK(ca_spmat_init(&B, cols, rows, A.nnz + rows) == CA_OK);
                    uint32_t tc[32];
                    int32_t tv[32];
                    for (uint32_t i = 0; i < rows; i++) {
                        uint32_t n = 0;
                        int32_t v0 = 0;
                        for (uint32_t k = A.row_ptr[i]; k < A.row_ptr[i + 1] && n < 30; k++) {
                            if (A.col[k] == 1) continue;
                            if (A.col[k] == 0) v0 = A.val[k];
                            tc[n] = A.col[k];
                            tv[n++] = A.val[k];
                        }
                        if (v0) { tc[n] = 1; tv[n++] = v0; }
                        CHECK(ca_spmat_add_row(&B, tc, tv, n) == CA_OK);
                        uint64_t acc = 0;
                        for (uint32_t k = B.row_ptr[i]; k < B.row_ptr[i + 1]; k++) {
                            int32_t v = B.val[k];
                            uint64_t c = v >= 0 ? (uint64_t)v % q : q - ((uint64_t)(-v) % q);
                            acc = ca_addmod(acc, ca_mulmod(c, xt[B.col[k]], q), q);
                        }
                        b[i] = acc;
                    }
                    ca_spmat_free(&A);
                    A = B;
                }
                ca_linsolve_report r1, rk;
                ca_status rc1 = ca_linsolve_mod_prime_mt(&A, b, q, x1, k1, 77, 1, &r1);
                for (uint32_t t = 2; t <= 5; t++) {
                    memset(xk, 0xa5, cols * sizeof(uint64_t));
                    ca_status rck = ca_linsolve_mod_prime_mt(&A, b, q, xk, kk, 77, t, &rk);
                    CHECK_EQ_U64((uint64_t)rck, (uint64_t)rc1);
                    CHECK_EQ_U64(rk.active_rows, r1.active_rows);
                    CHECK_EQ_U64(rk.active_cols, r1.active_cols);
                    CHECK_EQ_U64(rk.lanczos_iters, r1.lanczos_iters);
                    CHECK_EQ_U64(rk.attempts, r1.attempts);
                    CHECK_EQ_U64((uint64_t)rk.used_dense, (uint64_t)r1.used_dense);
                    CHECK(memcmp(xk, x1, cols * sizeof(uint64_t)) == 0);
                    CHECK(memcmp(kk, k1, cols) == 0);
                }
                printf("threads q=%" PRIu64 " %ux%u: rc %d, iters %u, attempts %u, dense %d: identical at 1-5 threads\n",
                       q, rows, cols, (int)rc1, r1.lanczos_iters, r1.attempts, r1.used_dense);
                ca_spmat_free(&A);
                free(b); free(xt); free(x1); free(xk); free(k1); free(kk);
            }
        }
    }
    TEST_MAIN_END();
}
