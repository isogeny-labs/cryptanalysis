#include "test_fixtures.h"
#include <unistd.h>

static void run(const ca_group *g, const ca_elem *gen, uint64_t width, int reps, double *ratio)
{
    uint64_t n = g->order;
    ca_rng rng;
    ca_rng_seed(&rng, 5);
    double tot = 0;
    for (int k = 0; k < reps; k++) {
        uint64_t lo = ca_rng_below(&rng, n - width);
        uint64_t x = lo + ca_rng_below(&rng, width);
        ca_elem h;
        fx_instance(g, gen, x, &h);
        ca_kangaroo_params p;
        ca_kangaroo_params_default(&p);
        p.seed = 77 + k;
        uint64_t got = 0;
        ca_stats st = {0};
        ca_status rc = ca_kangaroo_solve(g, gen, &h, lo, lo + width - 1, &p, &got, &st);
        CHECK(rc == CA_OK);
        CHECK_EQ_U64(got, x);
        tot += (double)st.group_ops;
    }
    if (ratio) *ratio = tot / reps / sqrt((double)width);
}

int main(void)
{
    ca_group g;
    ca_elem gen;
    double ratio;
    fx_zp_safe(&g, &gen, 2000000579ULL);
    {
        char dir[] = "/tmp/ca-kangaroo-resume-XXXXXX";
        CHECK(mkdtemp(dir) != NULL);
        char path[128], progress[160];
        snprintf(path, sizeof(path), "%s/herd.ckpt", dir);
        snprintf(progress, sizeof(progress), "%s.progress.json", path);
        ca_elem target;
        fx_instance(&g, &gen, 424242, &target);
        ca_kangaroo_params cp;
        ca_kangaroo_params_default(&cp);
        cp.seed = 17;
        cp.dp_bits = 0;
        cp.herd_size = 2;
        cp.max_ops = 400;
        uint64_t answer = 0;
        ca_stats first = {0}, second = {0};
        CHECK(ca_kangaroo_solve_checkpointed(&g, &gen, &target, 0, 1u << 20,
            &cp, path, 1, 1, 0, &answer, &first) == CA_ERR_LIMIT);
        CHECK(first.table_entries > 0);
        CHECK(access(path, F_OK) == 0 && access(progress, F_OK) == 0);
        cp.seed = 18;
        CHECK(ca_kangaroo_solve_checkpointed(&g, &gen, &target, 0, 1u << 20,
            &cp, path, 1, 1, 0, &answer, NULL) == CA_ERR_INVALID);
        cp.seed = 17;
        cp.max_ops = 1000000;
        CHECK(ca_kangaroo_solve_checkpointed(&g, &gen, &target, 0, 1u << 20,
            &cp, path, 1, 1, 0, &answer, &second) == CA_OK);
        CHECK_EQ_U64(answer, 424242);
        CHECK(second.group_ops > first.group_ops);
        FILE *f = fopen(path, "rb+");
        CHECK(f != NULL);
        CHECK(fseek(f, -1, SEEK_END) == 0);
        int last = fgetc(f);
        CHECK(last != EOF);
        CHECK(fseek(f, -1, SEEK_END) == 0);
        CHECK(fputc(last ^ 1, f) != EOF);
        CHECK(fclose(f) == 0);
        CHECK(ca_kangaroo_solve_checkpointed(&g, &gen, &target, 0, 1u << 20,
            &cp, path, 1, 1, 0, &answer, NULL) == CA_ERR_INVALID);
        unlink(progress); unlink(path); rmdir(dir);
    }
    run(&g, &gen, 1ULL << 26, 8, &ratio);
    printf("zp  width 2^26 ops/sqrt(w) = %.2f\n", ratio);
    CHECK(ratio < 8.0);
    fx_ec(&g, &gen, 1000000007ULL, 3, 11);
    run(&g, &gen, 1ULL << 24, 8, &ratio);
    printf("ec  width 2^24 ops/sqrt(w) = %.2f\n", ratio);
    CHECK(ratio < 8.0);
    /* small widths and the linear-scan path */
    run(&g, &gen, 100, 5, NULL);
    run(&g, &gen, 5000, 5, NULL);
    run(&g, &gen, 100000, 5, NULL);
    /* interval near the top of the group so wraparound happens */
    uint64_t n = g.order;
    ca_elem h;
    uint64_t got;
    fx_instance(&g, &gen, n - 3, &h);
    CHECK(ca_kangaroo_solve(&g, &gen, &h, n - 100000, n - 1, NULL, &got, NULL) == CA_OK);
    CHECK_EQ_U64(got, n - 3);
    /* whole group */
    fx_instance(&g, &gen, 987654, &h);
    CHECK(ca_kangaroo_solve(&g, &gen, &h, 0, 0, NULL, &got, NULL) == CA_OK);
    CHECK_EQ_U64(got, 987654);

    /* Regression, fuzz/crashes/grumpy_kangaroo_out_of_interval: a base that
     * generates a proper subgroup.  The solutions form a class modulo
     * ord(base), not modulo the group order, so the answer 2 is in [0, 2]
     * even though 5 is the representative modulo 6. */
    ca_group sg;
    ca_elem sbase, starget;
    CHECK(ca_group_zp_init(&sg, 7, 0) == CA_OK); /* Z_7^*, order 6 */
    const uint64_t w2[4] = {2, 0, 0, 0};         /* 2 has order 3 */
    CHECK(ca_group_encode(&sg, &sbase, w2));
    ca_group_mul(&sg, &starget, &sbase, 2, NULL);
    ca_kangaroo_params kp;
    ca_kangaroo_params_default(&kp);
    kp.seed = 1;
    kp.max_ops = 100000;
    uint64_t sub = 0;
    ca_status src = ca_kangaroo_solve(&sg, &sbase, &starget, 0, 2, &kp, &sub, NULL);
    CHECK(src == CA_OK || src == CA_ERR_LIMIT || src == CA_ERR_NOT_FOUND);
    if (src == CA_OK) CHECK(sub <= 2);

    /* Regression, fuzz/crashes/rho_kangaroo_dp_bits_shift: dp_bits at or above
     * the width of the mask used to be a shift by >= 64. */
    fx_instance(&g, &gen, 4242, &h);
    for (int32_t dpb = 62; dpb <= 200; dpb += 23) {
        ca_kangaroo_params dp;
        ca_kangaroo_params_default(&dp);
        dp.seed = 3;
        dp.dp_bits = dpb;
        dp.max_ops = 200000;
        uint64_t any = 0;
        ca_status r = ca_kangaroo_solve(&g, &gen, &h, 0, 100000, &dp, &any, NULL);
        CHECK(r == CA_OK || r == CA_ERR_LIMIT || r == CA_ERR_NOT_FOUND);
        if (r == CA_OK) CHECK_EQ_U64(any, 4242);
    }

    /* Regression, fuzz/crashes/kangaroo_herd_size_hang: 2 * herd_size used to
     * wrap to an empty herd, so the loop never advanced ops and max_ops never
     * fired.  This must terminate. */
    ca_kangaroo_params hp;
    ca_kangaroo_params_default(&hp);
    hp.seed = 1;
    hp.max_ops = 100000;
    hp.herd_size = 0x80000000u;
    uint64_t hx = 0;
    ca_status hrc = ca_kangaroo_solve(&g, &gen, &h, 0, 100000, &hp, &hx, NULL);
    CHECK(hrc == CA_OK || hrc == CA_ERR_LIMIT || hrc == CA_ERR_NOT_FOUND || hrc == CA_ERR_NOMEM);
    if (hrc == CA_OK) CHECK_EQ_U64(hx, 4242);

    /* Regression: the base is the identity and the target is not.  Past the
     * linear scan the herd hopped until max_ops (forever without one). */
    {
        ca_elem idb, tgt;
        ca_group_identity(&g, &idb);
        ca_kangaroo_params ip;
        ca_kangaroo_params_default(&ip);
        ip.seed = 1;
        ip.max_ops = 1000000;
        ca_stats ist = {0};
        uint64_t ix = 0;
        CHECK(ca_kangaroo_solve(&g, &idb, &h, 0, 100000, &ip, &ix, &ist) == CA_ERR_NOT_FOUND);
        CHECK_EQ_U64(ist.group_ops, 0);
        ca_group_identity(&g, &tgt);
        CHECK(ca_kangaroo_solve(&g, &idb, &tgt, 5, 100000, &ip, &ix, NULL) == CA_OK);
        CHECK_EQ_U64(ix, 5);
    }

    /* Regression: a target outside the order-n subgroup has no logarithm;
     * the herd used to hop until max_ops.  p - 1 = -1 is a non-residue in
     * the order-q subgroup of the safe prime p, so (p - 1)^q != 1. */
    {
        ca_group zg;
        ca_elem zgen, outside;
        fx_zp_safe(&zg, &zgen, 2000000579ULL);
        const uint64_t wm1[4] = {zg.p - 1, 0, 0, 0};
        CHECK(ca_group_encode(&zg, &outside, wm1));
        ca_kangaroo_params op;
        ca_kangaroo_params_default(&op);
        op.seed = 1;
        op.max_ops = 1000000;
        uint64_t ox = 0;
        CHECK(ca_kangaroo_solve(&zg, &zgen, &outside, 0, 100000, &op, &ox, NULL) ==
              CA_ERR_NOT_FOUND);
    }

    /* Regression: the abandon threshold 32 << dp_bits wrapped to 0 for
     * dp_bits >= 59 (dp_bits is clamped to 62), which restarted every
     * kangaroo at every hop.  No distinguished point is reachable at these
     * widths, so there must be no restart at all. */
    fx_instance(&g, &gen, 4242, &h);
    for (int32_t dpb = 59; dpb <= 62; dpb++) {
        ca_kangaroo_params ap;
        ca_kangaroo_params_default(&ap);
        ap.seed = 3;
        ap.dp_bits = dpb;
        ap.max_ops = 20000;
        ca_stats ast = {0};
        uint64_t ax = 0;
        CHECK(ca_kangaroo_solve(&g, &gen, &h, 0, 100000, &ap, &ax, &ast) == CA_ERR_LIMIT);
        CHECK_EQ_U64(ast.collisions, 0);
    }
    TEST_MAIN_END();
}
