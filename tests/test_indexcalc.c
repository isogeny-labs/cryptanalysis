#include "test_fixtures.h"
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>

static void checkpoint_roundtrip(void)
{
    char dir[] = "/tmp/ca-ic-checkpoint-XXXXXX";
    CHECK(mkdtemp(dir) != NULL);
    char journal[256], precomp[280], progress[280];
    snprintf(journal, sizeof(journal), "%s/relations.ckpt", dir);
    snprintf(precomp, sizeof(precomp), "%s.precomp", journal);
    snprintf(progress, sizeof(progress), "%s/progress.json", dir);
    ca_ic_params pr;
    ca_ic_params_default(&pr);
    pr.seed = 7;
    uint64_t x = 0;
    ca_ic_stats st;
    CHECK(ca_ic_solve_checkpointed(1000003, 2, 123456, &pr, journal, 1, &x, &st) == CA_OK);
    CHECK_EQ_U64(ca_powmod(2, x, 1000003), 123456);
    CHECK(access(journal, F_OK) == 0);
    CHECK(access(precomp, F_OK) == 0);
    CHECK(access(progress, F_OK) == 0);

    /* The verified precomputation can be loaded without repeating the sieve. */
    x = 0;
    CHECK(ca_ic_solve_checkpointed(1000003, 2, 123456, &pr, journal, 1, &x, &st) == CA_OK);
    CHECK_EQ_U64(ca_powmod(2, x, 1000003), 123456);
    CHECK(st.sieve_seconds == 0);

    /* A changed base must never reuse either artifact. */
    CHECK(ca_ic_solve_checkpointed(1000003, 3, 123456, &pr, journal, 1, &x, &st) == CA_ERR_INVALID);

    /* Simulate interruption during the last relation record.  The completed
     * prefix is replayed and the missing sieve unit is recomputed. */
    CHECK(unlink(precomp) == 0);
    struct stat sb;
    CHECK(stat(journal, &sb) == 0);
    int fd = open(journal, O_WRONLY);
    CHECK(fd >= 0);
    if (fd >= 0) {
        CHECK(ftruncate(fd, sb.st_size - 4) == 0);
        close(fd);
    }
    CHECK(ca_ic_solve_checkpointed(1000003, 2, 123456, &pr, journal, 1, &x, &st) == CA_OK);
    CHECK_EQ_U64(ca_powmod(2, x, 1000003), 123456);
    CHECK(unlink(precomp) == 0);
    CHECK(ca_ic_solve_checkpointed(1000003, 3, 123456, &pr, journal, 1, &x, &st) == CA_ERR_INVALID);
    unlink(journal);
    unlink(progress);
    rmdir(dir);
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
    checkpoint_roundtrip();
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

    /* Regression: the automatic factor-base bound (60 and up) exceeded a tiny
     * modulus, so a prime q >= p was in the base, reduced to 0 or to another
     * prime's residue, and the logarithms could not be solved. */
    static const uint64_t tiny[] = {7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 53, 59, 61};
    for (size_t i = 0; i < sizeof(tiny) / sizeof(tiny[0]); i++) {
        for (int m = 0; m < 2; m++) {
            uint64_t tp = tiny[i], tg = ca_primitive_root(tp), th = 2 + (i % (tp - 3));
            ca_ic_params tpar;
            ca_ic_params_default(&tpar);
            tpar.seed = 5 + i;
            tpar.method = m ? CA_IC_RANDOM_EXPONENT : CA_IC_LINEAR_SIEVE;
            uint64_t tx = 0;
            ca_status trc = ca_ic_solve(tp, tg, th, &tpar, &tx, NULL);
            CHECK(trc == CA_OK);
            if (trc == CA_OK) CHECK_EQ_U64(ca_powmod(tg, tx, tp), th);
        }
    }
    TEST_MAIN_END();
}
