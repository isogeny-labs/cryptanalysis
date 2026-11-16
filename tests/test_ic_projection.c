/* Exhaustive projected solution sets, independent of the Lanczos solver. */
// Exercise private graph/CSR helpers without expanding the public ABI.
#include "../src/indexcalc.c" // NOLINT(bugprone-suspicious-include)
#include <inttypes.h>

static uint64_t projected(const rel_list *rels, const ca_spmat *A, const uint64_t *b,
                          uint32_t ncols, uint64_t modulus)
{
    /* The first two coordinates define the bit set: modulus^2 must fit64 bits.
     * Reject bad test parameters instead of comparing two empty sentinels. */
    if (ncols < 2 || ncols > 6 || modulus < 2 || modulus > 8 ||
        (!rels && (!A || (A->rows && !b)))) {
        fprintf(stderr, "invalid projection test parameters\n");
        exit(5);
    }
    uint32_t rows;
    if (rels)
        rows = rels->n;
    else {
        if (!A) exit(5);
        rows = A->rows;
    }
    uint64_t count = 1, result = 0;
    for (uint32_t j = 0; j < ncols; ++j) count *= modulus;
    for (uint64_t code = 0; code < count; ++code) {
        uint64_t digits = code, x[6] = {0};
        for (uint32_t j = 0; j < ncols; ++j) {
            x[j] = digits % modulus;
            digits /= modulus;
        }
        int valid = 1;
        for (uint32_t i = 0; valid && i < rows; ++i) {
            int64_t sum = 0;
            uint64_t rhs;
            if (rels) {
                uint32_t len = rel_len(rels, i);
                const uint32_t *rcol = rel_cols(rels, i);
                const int32_t *rval = rel_vals(rels, i);
                for (uint32_t k = 0; k < len; ++k) sum += (int64_t)rval[k] * (int64_t)x[rcol[k]];
                rhs = rels->rhs[i];
            } else {
                for (uint32_t k = A->row_ptr[i]; k < A->row_ptr[i + 1]; ++k)
                    sum += (int64_t)A->val[k] * (int64_t)x[A->col[k]];
                rhs = b[i];
            }
            sum %= (int64_t)modulus;
            if (sum < 0) sum += (int64_t)modulus;
            valid = (uint64_t)sum == rhs % modulus;
        }
        if (valid) result |= UINT64_C(1) << (x[0] + modulus * x[1]);
    }
    return result;
}

static int check_trial32(void)
{
    uint32_t primes[1600], inverse[1600], limit[1600];
    ic_fbdiv div[1600];
    size_t n = ca_sieve_primes(13000, primes, 1600);
    if (n > 1600) return 1;
    for (size_t i = 0; i < n; ++i) {
        uint64_t q = primes[i], inv = q;
        for (unsigned k = 0; k < 5; ++k) inv *= 2 - q * inv;
        div[i] = (ic_fbdiv){inv, UINT64_MAX / q};
        inverse[i] = (uint32_t)inv;
        limit[i] = UINT32_MAX / primes[i];
    }
    ca_ic_ctx ctx = {0};
    ctx.fb = primes;
    ctx.nfb = (uint32_t)n;
    ctx.fb_inv32 = inverse;
    ctx.fb_lim32 = limit;
    ca_ic_scan32_fn scanners[] = {ca_ic_scan32_portable, ca_ic_scan32_select()};
#if defined(__x86_64__) && (defined(__GNUC__) || defined(__clang__))
    printf("trial32 runtime backend: %s\n", scanners[1] == ca_ic_scan32_avx2 ? "AVX2" : "portable");
#elif defined(__aarch64__)
    puts("trial32 runtime backend: NEON");
#else
    puts("trial32 runtime backend: portable");
#endif
    ca_rng rng;
    ca_rng_seed(&rng, UINT64_C(0x32c20261115));
    unsigned checks = 0;
    for (unsigned scanner = 0; scanner < 2; ++scanner) {
        ctx.scan32 = scanners[scanner];
        for (unsigned k = 0; k < 24000; ++k) {
            uint32_t value = k < 4096 ? k : (uint32_t)ca_rng_next(&rng);
            if (k == 4096) value = UINT32_MAX;
            if (k == 4097) value = UINT32_C(0x80000000);
            for (unsigned mode = 0; mode < 3; ++mode) {
                relation a = {0}, b = {0};
                uint32_t na = mode ? IC_MAX_REL_COLS - (mode == 1) : 0, nb = na;
                int ra = trial_factor(value, primes, div, (uint32_t)n, 7, &a, &na);
                int rb = trial_factor32(value, &ctx, 7, &b, &nb);
                if (ra != rb || na != nb || memcmp(a.col, b.col, sizeof(a.col)) ||
                    memcmp(a.val, b.val, sizeof(a.val))) {
                    fprintf(stderr, "trial32 mismatch scanner=%u value=%u mode=%u\n", scanner,
                            value, mode);
                    return 1;
                }
                ++checks;
            }
        }
    }
    printf("ok: %u exact 32/64-bit factorization comparisons\n", checks);
    return 0;
}

int main(void)
{
    if (check_trial32()) return 5;
    const uint64_t primes[] = {
        3, 5, 17, 1000003, 4294967311ULL, 2305843009213693951ULL, 18446744073709551557ULL};
    ca_rng rng;
    ca_rng_seed(&rng, 0x1c20261115ULL);
    unsigned reconstruction_checks = 0;
    for (unsigned pi = 0; pi < sizeof(primes) / sizeof(*primes); ++pi) {
        uint64_t p = primes[pi], bound = ca_isqrt(p);
        for (unsigned k = 0; k < 100000; ++k) {
            uint64_t value = 1 + ca_rng_below(&rng, p - 1), a, b;
            int negative;
            ca_ic_rational_split(value, p, bound, &a, &b, &negative);
            uint64_t residue = ca_mulmod(b, value, p);
            if (negative) residue = ca_submod(0, residue, p);
            if (!a || !b || a > bound || b > p / (bound + 1) || residue != a) {
                fprintf(stderr,
                        "rational reconstruction mismatch p=%" PRIu64 " value=%" PRIu64 "\n", p,
                        value);
                return 4;
            }
            ++reconstruction_checks;
        }
    }
    const uint32_t edges[][4][2] = {
        {{0, 1}, {1, 2}, {2, 3}, {0, 1}}, {{0, 1}, {1, 2}, {2, 3}, {3, 0}},
        {{0, 1}, {1, 2}, {2, 0}, {0, 0}}, {{0, 0}, {0, 1}, {1, 1}, {1, 2}},
        {{0, 1}, {2, 3}, {0, 0}, {2, 2}},
    };
    unsigned checks = 0;
    for (uint64_t modulus = 3; modulus <= 6; ++modulus) {
        for (unsigned family = 0; family < 6; ++family) {
            for (unsigned variant = 0; variant < 4; ++variant) {
                rel_list rels = {0};
                for (unsigned i = 0; i < (family == 5 ? 0 : 4); ++i) {
                    relation r = {0};
                    r.col[0] = 0;
                    r.val[0] = -(int32_t)(i + 1);
                    r.col[1] = 1;
                    r.val[1] = (int32_t)(variant + i) - 2;
                    uint32_t u = edges[family][i][0], v = edges[family][i][1];
                    r.col[2] = 2 + u;
                    r.val[2] = u == v ? 2 : 1;
                    r.n = 3;
                    if (u != v) {
                        r.col[3] = 2 + v;
                        r.val[3] = 1;
                        r.n = 4;
                    }
                    int64_t rhs = 0;
                    for (uint32_t k = 0; k < r.n; ++k)
                        rhs += (int64_t)r.val[k] * (int64_t)((3 * r.col[k] + 2) % modulus);
                    rhs %= (int64_t)modulus;
                    if (rhs < 0) rhs += (int64_t)modulus;
                    r.rhs = (uint64_t)rhs;
                    if (rel_push(&rels, &r)) return 1;
                }
                relation r = {0};
                r.col[0] = 0;
                r.val[0] = 1;
                r.n = 1;
                r.rhs = (2 + (variant == 3)) % modulus;
                if (rel_push(&rels, &r)) return 1;
                ca_spmat reduced;
                uint64_t *b = NULL;
                ca_status rc = build_graph_matrix(&rels, 6, 2, modulus, &reduced, &b);
                if (rc != CA_OK || reduced.cols > 6) return 2;
                uint64_t before = projected(&rels, NULL, NULL, 6, modulus);
                uint64_t after = projected(NULL, &reduced, b, reduced.cols, modulus);
                if (before != after) {
                    fprintf(stderr, "projection mismatch mod=%" PRIu64 " family=%u variant=%u\n",
                            modulus, family, variant);
                    return 3;
                }
                ++checks;
                ca_spmat_free(&reduced);
                free(b);
                rel_free(&rels);
            }
        }
    }
    printf("ok: %u exhaustive projected-solution comparisons, moduli 3..6\n", checks);
    printf("ok: %u exact rational reconstruction and size-bound comparisons\n",
           reconstruction_checks);
    return 0;
}
