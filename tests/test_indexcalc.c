#include "test_fixtures.h"
#include "ic_trial.h"

static void check_remove(uint64_t v, uint32_t q, const ca_ic_divisor *d)
{
    uint64_t expected = v, got = v;
    int32_t exponent = 0;
    while (expected % q == 0) { expected /= q; ++exponent; }
    CHECK(ca_ic_remove_prime(&got, q, d) == exponent);
    CHECK_EQ_U64(got, expected);
}

static void test_fixed_divisors(void)
{
    uint32_t primes[1600];
    size_t n = ca_sieve_primes(13000, primes, 1600);
    CHECK(n <= 1600);
    /* Include the largest 32-bit prime, beyond the normal IC base. */
    primes[n++] = UINT32_C(4294967291);
    ca_rng rng;
    ca_rng_seed(&rng, 0x1c20261115ULL);
    for (size_t i = 0; i < n; ++i) {
        uint32_t q = primes[i];
        ca_ic_divisor d = ca_ic_divisor_init(q);
        if (q & 1) CHECK_EQ_U64(d.inverse * q, 1);
        uint64_t power = 1;
        for (;;) {
            check_remove(power, q, &d);
            if (power > 1) check_remove(power - 1, q, &d);
            if (power < UINT64_MAX) check_remove(power + 1, q, &d);
            if (power > UINT64_MAX / q) break;
            power *= q;
        }
        uint64_t top = (UINT64_MAX / q) * q;
        check_remove(top, q, &d);
        check_remove(top - 1, q, &d);
        if (top < UINT64_MAX) check_remove(top + 1, q, &d);
        check_remove(UINT64_MAX, q, &d);
        for (unsigned j = 0; j < 128; ++j) {
            uint64_t v = ca_rng_next(&rng) | 1;
            check_remove(v, q, &d);
            v = (v / q) * q;
            if (v) check_remove(v, q, &d);
        }
    }
}

static void run(uint64_t p, ca_ic_method method, uint32_t threads, int nlogs)
{
    ca_ic_params pr;
    ca_ic_params_default(&pr);
    pr.method = method;
    pr.threads = threads;
    pr.seed = 12345;
    ca_ic_ctx *ctx;
    ca_ic_stats st;
    uint64_t g = ca_primitive_root(p);
    ca_status rc = ca_ic_precompute(p, g, &pr, &ctx, &st);
    CHECK(rc == CA_OK);
    if (rc != CA_OK) { fprintf(stderr, "precompute failed for p=%" PRIu64 ": %s (%s)\n", p, ca_status_string(rc), ca_last_error()); return; }
    printf("p=%" PRIu64 " %s thr=%u: fb=%u unknowns=%u rels=%u verified=%u sieve=%.2fs linalg=%.2fs\n",
           p, method == CA_IC_LINEAR_SIEVE ? "lsieve" : "rexp", threads, st.factor_base_size, st.unknowns,
           st.relations, st.verified_logs, st.sieve_seconds, st.linalg_seconds);
    CHECK(st.verified_logs == st.factor_base_size);
    ca_rng rng;
    ca_rng_seed(&rng, p);
    for (int k = 0; k < nlogs; k++) {
        uint64_t x = ca_rng_below(&rng, p - 1);
        uint64_t h = ca_powmod(g, x, p);
        uint64_t got = 0;
        ca_stats s2 = {0};
        rc = ca_ic_log(ctx, h, &got, &s2);
        CHECK(rc == CA_OK);
        CHECK_EQ_U64(got, x);
    }
    /* non-primitive base: g^2 has order (p-1)/2 */
    ca_ic_free(ctx);
    uint64_t g2 = ca_mulmod(g, g, p);
    rc = ca_ic_precompute(p, g2, &pr, &ctx, &st);
    CHECK(rc == CA_OK);
    if (rc == CA_OK) {
        uint64_t x = 777777 % ((p - 1) / 2);
        uint64_t h = ca_powmod(g2, x, p);
        uint64_t got;
        CHECK(ca_ic_log(ctx, h, &got, NULL) == CA_OK);
        CHECK_EQ_U64(got, x);
        /* element outside <g2> (a non-residue) must be rejected */
        uint64_t nr = g;
        CHECK(ca_ic_log(ctx, nr, &got, NULL) != CA_OK);
        ca_ic_free(ctx);
    }
}

int main(void)
{
    test_fixed_divisors();
    /* small primes with a large prime factor in p-1 (safe primes) and
     * primes with smooth p-1 (Pohlig-Hellman path) */
    run(1000003, CA_IC_LINEAR_SIEVE, 1, 5);           /* 20 bits, p-1 = 2*3*166667 */
    run(1000003, CA_IC_RANDOM_EXPONENT, 1, 5);
    run(2000000579ULL, CA_IC_LINEAR_SIEVE, 2, 5);     /* 31 bits, safe prime */
    run(2000000579ULL, CA_IC_RANDOM_EXPONENT, 2, 3);
    run(1099511627791ULL, CA_IC_LINEAR_SIEVE, 4, 5);  /* 2^40 + 15 */
    /* 48-bit prime */
    run(281474976710597ULL, CA_IC_LINEAR_SIEVE, 4, 5); /* 2^48 - 59 */
    /* p-1 with a squared large prime? use p = 2*q^2+1 form if prime */
    uint64_t q = 16777259, pp = 0; /* q > 2^24 so the Lanczos + Hensel path is used */
    for (uint64_t k = 1; k < 200 && !pp; k++) {
        if (ca_is_prime(2 * k * q * q + 1)) pp = 2 * k * q * q + 1;
    }
    CHECK(pp != 0);
    printf("square case p=%" PRIu64 " (q=%" PRIu64 ")\n", pp, q);
    run(pp, CA_IC_LINEAR_SIEVE, 2, 3);
    /* one-shot API */
    uint64_t x;
    ca_ic_stats st;
    CHECK(ca_ic_solve(1000003, 2, 123456, NULL, &x, &st) == CA_OK);
    CHECK_EQ_U64(ca_powmod(2, x, 1000003), 123456);
    TEST_MAIN_END();
}
