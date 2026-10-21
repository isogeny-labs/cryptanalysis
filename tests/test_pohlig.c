#include "test_fixtures.h"
#include <unistd.h>

int main(void)
{
    ca_group g;
    ca_elem gen, h;
    uint64_t got;
    /* full Z_p^* for a p-1 with many small factors and one large one */
    uint64_t p = 1000003; /* p-1 = 2 * 3 * 166667 */
    CHECK(ca_group_zp_init(&g, p, 0) == CA_OK);
    uint64_t w[4] = {ca_primitive_root(p), 0, 0, 0};
    CHECK(ca_group_encode(&g, &gen, w));
    for (uint64_t x = 0; x < p - 1; x += 99991) {
        fx_instance(&g, &gen, x, &h);
        ca_stats st = {0};
        CHECK(ca_dlog(&g, &gen, &h, &got, &st) == CA_OK);
        CHECK_EQ_U64(got, x);
    }
    /* prime power factors: p = 2^16 * 3^4 * 5 + 1? find a prime with such structure */
    uint64_t q = 256ULL * 81 * 25 * 49 * 11 * 13 + 1; /* check primality below */
    while (!ca_is_prime(q)) q += 2ULL * 3 * 5 * 7 * 11 * 13 * 2;
    CHECK(ca_group_zp_init(&g, q, 0) == CA_OK);
    w[0] = ca_primitive_root(q);
    CHECK(ca_group_encode(&g, &gen, w));
    ca_rng rng;
    ca_rng_seed(&rng, 3);
    for (int k = 0; k < 10; k++) {
        uint64_t x = ca_rng_below(&rng, q - 1);
        fx_instance(&g, &gen, x, &h);
        CHECK(ca_dlog(&g, &gen, &h, &got, NULL) == CA_OK);
        CHECK_EQ_U64(got, x);
    }
    /* each explicit solver through the dispatcher */
    ca_solver solvers[] = {CA_SOLVER_BSGS, CA_SOLVER_RHO, CA_SOLVER_KANGAROO, CA_SOLVER_GRUMPY};
    uint64_t p2 = 2000000579ULL;
    CHECK(ca_group_zp_init(&g, p2, 0) == CA_OK); /* order 2 * 1000000289 */
    w[0] = ca_primitive_root(p2);
    CHECK(ca_group_encode(&g, &gen, w));
    for (size_t s = 0; s < 4; s++) {
        ca_dlog_params dp;
        ca_dlog_params_default(&dp);
        dp.solver = solvers[s];
        dp.rho.seed = 5;
        uint64_t x = 1234567891ULL;
        fx_instance(&g, &gen, x, &h);
        ca_stats st = {0};
        ca_status rc = ca_pohlig_hellman(&g, &gen, &h, &dp, &got, &st);
        CHECK(rc == CA_OK);
        CHECK_EQ_U64(got, x);
        printf("%-9s ops=%" PRIu64 " time=%.3fs\n", ca_solver_name(solvers[s]), st.group_ops, st.seconds);
    }
    /* The parent checkpoint retains solved factors while the selected BSGS
     * digit checkpoint retains an incomplete baby table across a cap change. */
    {
        ca_group dg;
        ca_elem db, dh;
        CHECK(ca_group_zp_init(&dg, 1000003, 0) == CA_OK);
        const uint64_t dw[4] = {ca_primitive_root(1000003), 0, 0, 0};
        CHECK(ca_group_encode(&dg, &db, dw));
        fx_instance(&dg, &db, 12345, &dh);
        char dir[] = "/tmp/ca-dlog-XXXXXX";
        CHECK(mkdtemp(dir) != NULL);
        char prefix[256], file[320];
        snprintf(prefix, sizeof(prefix), "%s/dlog", dir);
        ca_dlog_params dp;
        ca_dlog_params_default(&dp);
        dp.bsgs.max_ops = 100;
        ca_stats first = {0}, resumed = {0};
        CHECK(ca_pohlig_hellman_checkpointed(&dg, &db, &dh, &dp, prefix,
                                              1, 1, 0, &got, &first) == CA_ERR_LIMIT);
        snprintf(file, sizeof(file), "%s.ckpt", prefix);
        CHECK(access(file, F_OK) == 0);
        snprintf(file, sizeof(file), "%s.factor2.digit0.ckpt", prefix);
        CHECK(access(file, F_OK) == 0);
        dp.bsgs.max_ops = 0;
        CHECK(ca_pohlig_hellman_checkpointed(&dg, &db, &dh, &dp, prefix,
                                              1, 1, 0, &got, &resumed) == CA_OK);
        CHECK_EQ_U64(got, 12345);
        ca_stats again = {0};
        CHECK(ca_pohlig_hellman_checkpointed(&dg, &db, &dh, &dp, prefix,
                                              1, 1, 0, &got, &again) == CA_OK);
        CHECK_EQ_U64(got, 12345);
        CHECK_EQ_U64(resumed.group_ops, again.group_ops);
        fx_instance(&dg, &db, 12346, &dh);
        CHECK(ca_pohlig_hellman_checkpointed(&dg, &db, &dh, &dp, prefix,
                                              1, 1, 0, &got, NULL) == CA_ERR_INVALID);
        snprintf(file, sizeof(file), "%s.ckpt", prefix);
        FILE *damage = fopen(file, "r+b");
        CHECK(damage != NULL);
        if (damage) {
            CHECK(fseek(damage, -1, SEEK_END) == 0);
            int last = fgetc(damage);
            CHECK(last != EOF);
            CHECK(fseek(damage, -1, SEEK_END) == 0);
            CHECK(fputc(last ^ 0xff, damage) != EOF);
            CHECK(fclose(damage) == 0);
        }
        fx_instance(&dg, &db, 12345, &dh);
        CHECK(ca_pohlig_hellman_checkpointed(&dg, &db, &dh, &dp, prefix,
                                              1, 1, 0, &got, NULL) == CA_ERR_INVALID);
        snprintf(file, sizeof(file), "%s.ckpt", prefix); unlink(file);
        snprintf(file, sizeof(file), "%s.ckpt.progress.json", prefix); unlink(file);
        snprintf(file, sizeof(file), "%s.factor2.digit0.ckpt", prefix); unlink(file);
        snprintf(file, sizeof(file), "%s.factor2.digit0.ckpt.progress.json", prefix); unlink(file);
        rmdir(dir);
    }
    {
        /* Several digits of the same prime power exercise xk/qk recovery. */
        ca_group dg;
        ca_elem db, dh;
        CHECK(ca_group_zp_init(&dg, 1009, 0) == CA_OK); /* 1008 = 2^4 * 3^2 * 7 */
        const uint64_t dw[4] = {ca_primitive_root(1009), 0, 0, 0};
        CHECK(ca_group_encode(&dg, &db, dw));
        fx_instance(&dg, &db, 777, &dh);
        char dir[] = "/tmp/ca-dlog-power-XXXXXX";
        CHECK(mkdtemp(dir) != NULL);
        char prefix[256], file[320];
        snprintf(prefix, sizeof(prefix), "%s/dlog", dir);
        ca_stats stats = {0};
        CHECK(ca_pohlig_hellman_checkpointed(&dg, &db, &dh, NULL, prefix,
                                              1, 1, 0, &got, &stats) == CA_OK);
        CHECK_EQ_U64(got, 777);
        CHECK(ca_pohlig_hellman_checkpointed(&dg, &db, &dh, NULL, prefix,
                                              1, 1, 0, &got, NULL) == CA_OK);
        CHECK_EQ_U64(got, 777);
        snprintf(file, sizeof(file), "%s.ckpt", prefix); unlink(file);
        snprintf(file, sizeof(file), "%s.ckpt.progress.json", prefix); unlink(file);
        rmdir(dir);
    }
    /* Repeatedly resume one capped rho digit. The parent must retain the
     * child's checkpointed elapsed time as well as its operation counters. */
    {
        ca_group dg;
        ca_elem db, dh;
        fx_zp_safe(&dg, &db, 2000000579ULL);
        fx_instance(&dg, &db, 424242, &dh);
        ca_dlog_params dp;
        ca_dlog_params_default(&dp);
        dp.solver = CA_SOLVER_RHO;
        dp.rho.seed = 1984;
        dp.rho.walks_per_thread = 4;
        dp.rho.dp_bits = 0;
        char dir[] = "/tmp/ca-dlog-elapsed-XXXXXX";
        CHECK(mkdtemp(dir) != NULL);
        char prefix[256], file[320];
        snprintf(prefix, sizeof(prefix), "%s/dlog", dir);
        double observed = 0;
        ca_stats resumed = {0};
        for (unsigned attempt = 1; attempt <= 3; attempt++) {
            dp.rho.max_ops = 500 * attempt;
            memset(&resumed, 0, sizeof(resumed));
            double before = ca_now();
            CHECK(ca_pohlig_hellman_checkpointed(&dg, &db, &dh, &dp, prefix,
                        1, 1, 0, &got, &resumed) == CA_ERR_LIMIT);
            observed += ca_now() - before;
        }
        /* Snapshot timestamps precede their final writes; allow that small
         * uncheckpointed tail, but not loss of whole prior invocations. */
        CHECK(resumed.seconds + 0.02 >= observed);
        snprintf(file, sizeof(file), "%s.ckpt", prefix); unlink(file);
        snprintf(file, sizeof(file), "%s.ckpt.progress.json", prefix); unlink(file);
        snprintf(file, sizeof(file), "%s.factor0.digit0.ckpt", prefix); unlink(file);
        snprintf(file, sizeof(file), "%s.factor0.digit0.ckpt.progress.json", prefix); unlink(file);
        rmdir(dir);
    }
    /* EC group with cofactor: dlog in full group order */
    uint64_t n;
    CHECK(ca_ec_count_points(1000003, 1, 7, &n, NULL) == CA_OK);
    CHECK(ca_group_ec_init(&g, 1000003, 1, 7, n) == CA_OK);
    ca_elem P;
    ca_ec_random_point(&g, &P, 9);
    uint64_t ordP = ca_group_elem_order(&g, &P);
    g.order = ordP;
    CHECK(ordP > 4096);
    /* Boundary widths exercise the serial scan, batched explicit brute
     * scan, and the EC AUTO switch to BSGS.  Check the first/last position
     * and a miss, including a final block at UINT64_MAX. */
    const uint64_t widths[] = {63, 64, 255, 256, 257, 4095};
    for (size_t wi = 0; wi < sizeof(widths) / sizeof(widths[0]); wi++) {
        uint64_t width = widths[wi];
        uint64_t lo = 12345;
        uint64_t positions[] = {0, 1, width / 2, width - 1};
        for (size_t pi = 0; pi < sizeof(positions) / sizeof(positions[0]); pi++) {
            uint64_t want = lo + positions[pi];
            fx_instance(&g, &P, want, &h);
            for (int mode = 0; mode < 2; mode++) {
                ca_dlog_params dp;
                ca_dlog_params_default(&dp);
                dp.solver = mode ? CA_SOLVER_AUTO : CA_SOLVER_BRUTE;
                ca_stats scan = {0};
                CHECK(ca_dlog_prime_order(&g, &P, &h, lo, lo + width - 1,
                                          &dp, &got, &scan) == CA_OK);
                CHECK_EQ_U64(got, want);
                CHECK(scan.group_ops > 0);
            }
        }
        fx_instance(&g, &P, lo + width, &h);
        ca_dlog_params brute;
        ca_dlog_params_default(&brute);
        brute.solver = CA_SOLVER_BRUTE;
        CHECK(ca_dlog_prime_order(&g, &P, &h, lo, lo + width - 1,
                                  &brute, &got, NULL) == CA_ERR_NOT_FOUND);
    }
    {
        /* A caller-specified BSGS cap below this interval keeps AUTO on
         * brute force, matching the previous dispatcher behavior. */
        ca_dlog_params capped, brute;
        ca_dlog_params_default(&capped);
        ca_dlog_params_default(&brute);
        capped.bsgs_max_prime = 128;
        brute.solver = CA_SOLVER_BRUTE;
        fx_instance(&g, &P, 12473, &h);
        ca_stats cs = {0}, bs = {0};
        CHECK(ca_dlog_prime_order(&g, &P, &h, 12345, 12601,
                                  &capped, &got, &cs) == CA_OK);
        CHECK_EQ_U64(got, 12473);
        CHECK(ca_dlog_prime_order(&g, &P, &h, 12345, 12601,
                                  &brute, &got, &bs) == CA_OK);
        CHECK_EQ_U64(cs.group_ops, bs.group_ops);
    }
    {
        ca_dlog_params brute;
        ca_dlog_params_default(&brute);
        brute.solver = CA_SOLVER_BRUTE;
        uint64_t lo = UINT64_MAX - 63;
        fx_instance(&g, &P, UINT64_MAX, &h);
        CHECK(ca_dlog_prime_order(&g, &P, &h, lo, UINT64_MAX,
                                  &brute, &got, NULL) == CA_OK);
        CHECK_EQ_U64(got, UINT64_MAX);
    }
    for (int k = 0; k < 10; k++) {
        uint64_t x = ca_rng_below(&rng, ordP);
        fx_instance(&g, &P, x, &h);
        CHECK(ca_dlog(&g, &P, &h, &got, NULL) == CA_OK);
        CHECK_EQ_U64(got, x);
    }
    /* base of smaller order than the group: a non-cyclic curve group,
     * E(F_46687): y^2 = x^3 + 18059 x + 13589 with #E = 2^6 3^6 and a base of
     * order 23328 (challenges/ecc fp-smooth-b16).  The group order stays the
     * full #E; the log comes back modulo ord(base). */
    CHECK(ca_group_ec_init(&g, 46687, 18059, 13589, 46656) == CA_OK);
    const uint64_t wb[4] = {0x1cce, 0x4e7, 0, 0}, wt[4] = {0xaee4, 0x446f, 0, 0};
    CHECK(ca_group_encode(&g, &P, wb));
    CHECK(ca_group_encode(&g, &h, wt));
    CHECK_EQ_U64(ca_group_elem_order(&g, &P), 23328);
    CHECK(ca_dlog(&g, &P, &h, &got, NULL) == CA_OK);
    CHECK_EQ_U64(got, 0x32d9 % 23328);
    /* target outside <base> is rejected */
    CHECK(ca_group_zp_init(&g, 1000003, 166667) == CA_OK);
    CHECK(ca_group_find_generator(&g, &gen, 1) == CA_OK);
    w[0] = 2; /* order 1000002/... 2 generates the whole group, not the subgroup */
    CHECK(ca_group_encode(&g, &h, w));
    if (ca_group_elem_order(&g, &h) == 0) CHECK(ca_dlog(&g, &gen, &h, &got, NULL) != CA_OK);
    TEST_MAIN_END();
}
