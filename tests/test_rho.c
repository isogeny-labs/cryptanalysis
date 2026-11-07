#include "test_fixtures.h"
#include <unistd.h>

static void run_rho(const ca_group *g, const ca_elem *gen, const ca_rho_params *p, int reps,
                    double *ratio_out)
{
    uint64_t n = g->order;
    ca_rng rng;
    ca_rng_seed(&rng, 99 + p->threads);
    double total_ops = 0;
    for (int k = 0; k < reps; k++) {
        uint64_t x = ca_rng_below(&rng, n);
        ca_elem h;
        fx_instance(g, gen, x, &h);
        uint64_t got = 0;
        ca_stats st = {0};
        ca_rho_params pp = *p;
        pp.seed = 1000 + k;
        ca_status rc = ca_rho_solve(g, gen, &h, &pp, &got, &st);
        CHECK(rc == CA_OK);
        CHECK_EQ_U64(got, x);
        total_ops += (double)st.group_ops;
    }
    if (ratio_out) *ratio_out = total_ops / reps / sqrt((double)n);
}

/* The native (Z/pZ)^* group takes a fused round in rho.c; the same group
 * behind a copy of its vtable is not native and takes the staged batch_op
 * path.  Same seed, same answer, same operations and table: the fused round
 * is the staged one reordered, not a different walk.  r = 32 indexes by mask,
 * r = 20 by fastmod, and max_ops checks that a capped run stops at the same
 * count. */
static void check_zp_fused_matches_staged(void)
{
    ca_group g, g2;
    ca_elem gen;
    fx_zp_safe(&g, &gen, 2000000579ULL);
    static ca_group_vtable vt2;
    vt2 = *g.vt;
    g2 = g;
    g2.vt = &vt2;
    const uint32_t rs[2] = {32, 20};
    for (int k = 0; k < 6; k++) {
        ca_elem h;
        fx_instance(&g, &gen, 123456789ULL * (uint64_t)(k + 1) % g.order, &h);
        ca_rho_params p;
        ca_rho_params_default(&p);
        p.seed = 77 + (uint64_t)k;
        p.r = rs[k & 1];
        if (k == 5) p.max_ops = 20000;
        uint64_t x1 = 0, x2 = 0;
        ca_stats s1 = {0}, s2 = {0};
        ca_status rc1 = ca_rho_solve(&g, &gen, &h, &p, &x1, &s1);
        ca_status rc2 = ca_rho_solve(&g2, &gen, &h, &p, &x2, &s2);
        CHECK(rc1 == rc2);
        CHECK(x1 == x2);
        CHECK(s1.group_ops == s2.group_ops);
        CHECK(s1.iterations == s2.iterations);
        CHECK(s1.table_entries == s2.table_entries);
    }
}

int main(void)
{
    ca_group g;
    ca_elem gen;
    ca_rho_params p;
    ca_rho_params_default(&p);

    check_zp_fused_matches_staged();
    /* Exercise fixed-base setup with scalars whose top uint64 bit is set.
     * y^2 = x^3 + 1 over this p == 2 (mod 3) has p+1 points; (0,1)
     * is a nonidentity point of order 3. The work cap avoids a large search.
     * Under UBSan this catches a shift by 64 in the table scalar loop. */
    {
        ca_group wide;
        ca_elem point;
        const uint64_t prime = UINT64_C(18446744073709551557);
        CHECK(ca_group_ec_init(&wide, prime, 0, 1, prime + 1) == CA_OK);
        const uint64_t words[4] = {0, 1, 0, 0};
        CHECK(ca_group_encode(&wide, &point, words));
        ca_rho_params bounded;
        ca_rho_params_default(&bounded);
        bounded.r = 16;
        bounded.walks_per_thread = 1;
        bounded.negation_map = 0;
        bounded.dp_bits = 0;
        bounded.seed = 1;
        bounded.max_ops = 1000;
        uint64_t answer = 0;
        ca_status result = ca_rho_solve(&wide, &point, &point, &bounded, &answer, NULL);
        CHECK(result == CA_OK || result == CA_ERR_LIMIT);
        if (result == CA_OK) {
            ca_elem recovered;
            ca_group_mul(&wide, &recovered, &point, answer, NULL);
            CHECK(ca_group_equal(&wide, &recovered, &point));
        }
    }

    /* Z_p^* subgroup of prime order ~2^30 */
    fx_zp_safe(&g, &gen, 2000000579ULL);
    double ratio;
    run_rho(&g, &gen, &p, 6, &ratio);
    printf("zp  serial   ops/sqrt(n) = %.2f\n", ratio);
    CHECK(ratio < 6.0);
    p.threads = 4;
    run_rho(&g, &gen, &p, 6, &ratio);
    printf("zp  4 thread ops/sqrt(n) = %.2f\n", ratio);
    CHECK(ratio < 8.0);

    /* Elliptic curve, prime-order subgroup, negation map on and off */
    fx_ec(&g, &gen, 1000000007ULL, 3, 11);
    printf("ec order %" PRIu64 " (cofactor %" PRIu64 ")\n", g.order, g.cofactor);
    ca_rho_params_default(&p);
    p.negation_map = 0;
    run_rho(&g, &gen, &p, 6, &ratio);
    printf("ec  no-neg   ops/sqrt(n) = %.2f\n", ratio);
    CHECK(ratio < 6.0);
    p.negation_map = 1;
    run_rho(&g, &gen, &p, 6, &ratio);
    printf("ec  negmap   ops/sqrt(n) = %.2f\n", ratio);
    CHECK(ratio < 6.0);
    p.threads = 4;
    run_rho(&g, &gen, &p, 4, &ratio);
    printf("ec  neg 4thr ops/sqrt(n) = %.2f\n", ratio);
    CHECK(ratio < 8.0);
    /* explicit small dp bits and few walks */
    ca_rho_params_default(&p);
    p.dp_bits = 2;
    p.walks_per_thread = 3;
    p.r = 16;
    run_rho(&g, &gen, &p, 3, NULL);
    /* User-supplied table sizes also exercise the general index path. */
    p.r = 15;
    run_rho(&g, &gen, &p, 3, NULL);

    /* tiny groups must still work (brute force path and dp_bits = 0) */
    fx_zp_safe(&g, &gen, 23);
    run_rho(&g, &gen, &p, 5, NULL);
    fx_zp_safe(&g, &gen, 1019);
    run_rho(&g, &gen, &p, 5, NULL);
    fx_ec(&g, &gen, 10007, 1, 1);
    run_rho(&g, &gen, &p, 5, NULL);

    /* composite order (full Z_p^*) */
    CHECK(ca_group_zp_init(&g, 1000003, 0) == CA_OK);
    const uint64_t w[4] = {2, 0, 0, 0};
    CHECK(ca_group_encode(&g, &gen, w));
    ca_rho_params_default(&p);
    run_rho(&g, &gen, &p, 5, NULL);

    /* limits */
    fx_zp_safe(&g, &gen, 2000000579ULL);
    p.max_ops = 100;
    ca_elem h;
    uint64_t got;
    fx_instance(&g, &gen, 424242, &h);
    CHECK(ca_rho_solve(&g, &gen, &h, &p, &got, NULL) == CA_ERR_LIMIT);

    /* A capped run saves its DP corpus; a later process can raise the
     * cumulative operation budget and continue against that corpus. */
    {
        char dir[] = "/tmp/ca-rho-resume-XXXXXX";
        CHECK(mkdtemp(dir) != NULL);
        char path[128], progress[160];
        snprintf(path, sizeof(path), "%s/rho.dp", dir);
        snprintf(progress, sizeof(progress), "%s.progress.json", path);
        ca_rho_params rp;
        ca_rho_params_default(&rp);
        rp.seed = 1984;
        rp.dp_bits = 0;
        rp.walks_per_thread = 4;
        rp.max_ops = 500;
        ca_stats first = {0}, second = {0};
        CHECK(ca_rho_solve_checkpointed(&g, &gen, &h, &rp, path, 1, 1, 0,
                                        &got, &first) == CA_ERR_LIMIT);
        CHECK(first.table_entries > 0);
        CHECK(access(path, F_OK) == 0);
        CHECK(access(progress, F_OK) == 0);
        rp.seed = 1985;
        CHECK(ca_rho_solve_checkpointed(&g, &gen, &h, &rp, path, 1, 1, 0,
                                        &got, NULL) == CA_ERR_INVALID);
        rp.seed = 1984;
        rp.max_ops = 1000000;
        CHECK(ca_rho_solve_checkpointed(&g, &gen, &h, &rp, path, 1, 1, 0,
                                        &got, &second) == CA_OK);
        CHECK_EQ_U64(got, 424242);
        CHECK(second.group_ops > first.group_ops);
        FILE *f = fopen(path, "ab");
        CHECK(f != NULL);
        if (f) {
            CHECK(fputc(0, f) != EOF);
            CHECK(fclose(f) == 0);
        }
        CHECK(ca_rho_solve_checkpointed(&g, &gen, &h, &rp, path, 1, 1, 0,
                                        &got, NULL) == CA_ERR_INVALID);
        unlink(progress);
        unlink(path);
        rmdir(dir);
    }
    /* Regression, fuzz/crashes/rho_kangaroo_dp_bits_shift: dp_bits at or above
     * the width of the mask used to shift a 64-bit value by >= 64. */
    for (int32_t dpb = 58; dpb <= 200; dpb += 27) {
        ca_rho_params dp;
        ca_rho_params_default(&dp);
        dp.seed = 7;
        dp.threads = 1;
        dp.dp_bits = dpb;
        dp.max_ops = 200000;
        uint64_t any = 0;
        ca_status r = ca_rho_solve(&g, &gen, &h, &dp, &any, NULL);
        CHECK(r == CA_OK || r == CA_ERR_LIMIT || r == CA_ERR_NOT_FOUND);
        if (r == CA_OK) {
            ca_elem chk;
            ca_group_mul(&g, &chk, &gen, any, NULL);
            CHECK(ca_group_equal(&g, &chk, &h));
        }
    }

    /* Regression: the base is the identity and the target is not.  No power
     * of the identity equals the target, and the walk never produced a
     * collision that verifies, so it ran until max_ops (forever without
     * one).  It must report NOT_FOUND at once. */
    {
        ca_elem idb, tgt;
        ca_group_identity(&g, &idb);
        fx_instance(&g, &gen, 12345, &tgt);
        ca_rho_params ip;
        ca_rho_params_default(&ip);
        ip.seed = 3;
        ip.max_ops = 2000000;
        ca_stats ist = {0};
        uint64_t ix = 0;
        CHECK(ca_rho_solve(&g, &idb, &tgt, &ip, &ix, &ist) == CA_ERR_NOT_FOUND);
        CHECK_EQ_U64(ist.group_ops, 0);
        CHECK(ca_rho_solve(&g, &idb, &idb, &ip, &ix, NULL) == CA_OK);
        CHECK_EQ_U64(ix, 0);
    }

    /* Regression: with the negation map the look-ahead rule rejects a
     * multiplier that returns to the previous point.  When all r multipliers
     * are rejected the scan wrapped around and repeated forever; a small
     * user-chosen r reaches that point with probability r^-r per step (about
     * 1/256 per point at r = 4), so most runs at r = 4 stalled until max_ops.
     * Every run must now finish, long before 400000 ops on a group of 65k. */
    fx_ec(&g, &gen, 65537, 1, 1);
    for (uint32_t r = 4; r <= 5; r++) {
        for (uint64_t seed = 1; seed <= 30; seed++) {
            ca_rho_params sp;
            ca_rho_params_default(&sp);
            sp.seed = seed;
            sp.r = r;
            sp.dp_bits = 0;
            sp.max_ops = 400000;
            uint64_t sx = 0;
            fx_instance(&g, &gen, (seed * 7919) % g.order, &h);
            ca_status sr = ca_rho_solve(&g, &gen, &h, &sp, &sx, NULL);
            CHECK(sr == CA_OK);
            if (sr == CA_OK) {
                ca_elem chk;
                ca_group_mul(&g, &chk, &gen, sx, NULL);
                CHECK(ca_group_equal(&g, &chk, &h));
            }
        }
    }
    TEST_MAIN_END();
}
