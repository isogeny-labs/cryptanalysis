/* Known-answer tests above 2^50.
 *
 * Every generic solver runs on groups whose modulus, group order or secret
 * exceeds 2^50: fields of 51, 53, 57, 62, 63 and 64 bits, which straddle the
 * double-precision mantissa (2^53) and the lazy-Montgomery switch (2^62).
 * Each case keeps the discrete-log work small (prime subgroups of about 2^26,
 * intervals of 2^31, Pohlig-Hellman on smooth orders), so the arithmetic is
 * wide while the run stays short.
 *
 * The parameters were found with this library (ca_is_prime,
 * ca_ec_count_points, ca_factorize) and are re-derived below before use:
 * primality, divisibility, and the curve order are checked again, so a wrong
 * table entry fails loudly instead of testing nothing.  Every answer is
 * compared with the planted secret, not only verified by the solver. */
#include "test_fixtures.h"

static unsigned bitlen(uint64_t v) { return v ? 64u - (unsigned)__builtin_clzll(v) : 0u; }

/* Planted secrets: a fixed sample per case, including both ends of the range
 * and a value just above 2^50 whenever the range allows it. */
static uint64_t secret(ca_rng *rng, uint64_t n, int k)
{
    switch (k) {
    case 0: return 1;
    case 1: return n - 1;
    case 2: return n > (1ULL << 50) + 7 ? (1ULL << 50) + 7 : n / 3;
    default: return 1 + ca_rng_below(rng, n - 1);
    }
}

/* ---- (Z/pZ)^*: order-q subgroup with q near 2^26 ---------------------- */

static const struct {
    unsigned w;
    uint64_t p, q;
} zp_small[] = {
    {51, UINT64_C(2251798344928547), UINT64_C(67159871)},
    {53, UINT64_C(9007198063276249), UINT64_C(67161893)},
    {57, UINT64_C(144115185495489511), UINT64_C(67165873)},
    {62, UINT64_C(4611686015196912683), UINT64_C(67170869)},
    {63, UINT64_C(9223372035428935873), UINT64_C(67171873)},
    {64, UINT64_C(18446744073654685417), UINT64_C(67172869)},
};

static void solve_all_prime_order(const ca_group *g, const ca_elem *gen, uint64_t n, uint64_t seed,
                                  const char *label)
{
    ca_rng rng;
    ca_rng_seed(&rng, seed);
    for (int k = 0; k < 5; k++) {
        uint64_t x = secret(&rng, n, k), got;
        ca_elem h;
        fx_instance(g, gen, x, &h);

        ca_rho_params rp;
        ca_rho_params_default(&rp);
        rp.seed = seed + (uint64_t)k;
        rp.negation_map = g->kind == CA_GROUP_EC;
        got = 0;
        CHECK(ca_rho_solve(g, gen, &h, &rp, &got, NULL) == CA_OK);
        CHECK_EQ_U64(got, x);

        got = 0;
        CHECK(ca_bsgs_solve(g, gen, &h, 0, n - 1, NULL, &got, NULL) == CA_OK);
        CHECK_EQ_U64(got, x);

        ca_kangaroo_params kp;
        ca_kangaroo_params_default(&kp);
        kp.seed = seed + 11 + (uint64_t)k;
        got = 0;
        CHECK(ca_kangaroo_solve(g, gen, &h, 0, n - 1, &kp, &got, NULL) == CA_OK);
        CHECK_EQ_U64(got, x);

        got = 0;
        CHECK(ca_grumpy_solve(g, gen, &h, 0, n - 1, NULL, &got, NULL) == CA_OK);
        CHECK_EQ_U64(got, x);

        got = 0;
        CHECK(ca_dlog(g, gen, &h, &got, NULL) == CA_OK);
        CHECK_EQ_U64(got, x);

        ca_gpu_rho_params gp;
        ca_gpu_rho_params_default(&gp);
        gp.backend = CA_GPU_BACKEND_EMULATE;
        gp.seed = seed + 23 + (uint64_t)k;
        gp.negation_map = g->kind == CA_GROUP_EC;
        got = 0;
        CHECK(ca_gpu_rho_solve(g, gen, &h, &gp, &got, NULL) == CA_OK);
        CHECK_EQ_U64(got, x);
    }
    printf("%-28s n=%" PRIu64 " p=%" PRIu64 ": rho bsgs kangaroo grumpy dlog gpu-emu ok\n", label,
           n, g->p);
}

static void test_zp_small_subgroups(void)
{
    for (size_t i = 0; i < sizeof(zp_small) / sizeof(zp_small[0]); i++) {
        uint64_t p = zp_small[i].p, q = zp_small[i].q;
        CHECK(bitlen(p) == zp_small[i].w);
        CHECK(ca_is_prime(p) && ca_is_prime(q) && (p - 1) % q == 0);
        ca_group g;
        ca_elem gen;
        CHECK(ca_group_zp_init(&g, p, q) == CA_OK);
        CHECK(ca_group_find_generator(&g, &gen, 1) == CA_OK);
        char label[48];
        snprintf(label, sizeof(label), "Z_p^* %u-bit p, q~2^26", zp_small[i].w);
        solve_all_prime_order(&g, &gen, q, 100 + i, label);

        /* Amortised precomputation needs ~n^(2/3) work; 2^26 keeps it short. */
        ca_precomp_params pp;
        ca_precomp_params_default(&pp);
        pp.seed = 7;
        ca_rng rng;
        ca_rng_seed(&rng, 900 + i);
        ca_precomp_table *t = NULL;
        CHECK(ca_precomp_table_new(&g, &gen, &pp, &t, NULL) == CA_OK);
        for (int k = 0; k < 3 && t; k++) {
            uint64_t x = secret(&rng, q, k + 2), got = 0;
            ca_elem h;
            fx_instance(&g, &gen, x, &h);
            CHECK(ca_precomp_table_solve(t, &h, &got, NULL) == CA_OK);
            CHECK_EQ_U64(got, x);
        }
        ca_precomp_table_free(t);
    }
}

/* ---- (Z/pZ)^* in full: order p-1 > 2^50, smooth ------------------------ */

static const struct {
    unsigned w;
    uint64_t p;
} zp_smooth[] = {
    {51, UINT64_C(2163740965728887)},    {53, UINT64_C(8966204961534539)},
    {57, UINT64_C(142286669184650183)},  {62, UINT64_C(4522919259377454623)},
    {63, UINT64_C(9178225507077796199)}, {64, UINT64_C(18412301237266326539)},
};

static void test_zp_full_group(void)
{
    for (size_t i = 0; i < sizeof(zp_smooth) / sizeof(zp_smooth[0]); i++) {
        uint64_t p = zp_smooth[i].p;
        CHECK(bitlen(p) == zp_smooth[i].w && ca_is_prime(p));
        ca_factorization f;
        CHECK(ca_factorize(p - 1, &f) == CA_OK);
        CHECK(f.f[f.count - 1].p < (1ULL << 28)); /* p-1 is 2^28-smooth */
        ca_group g;
        CHECK(ca_group_zp_init(&g, p, 0) == CA_OK);
        CHECK_EQ_U64(g.order, p - 1);
        uint64_t root = ca_primitive_root(p);
        CHECK(root != 0);
        CHECK_EQ_U64(ca_mult_order(root, p), p - 1);
        uint64_t w[4] = {root, 0, 0, 0};
        ca_elem gen;
        CHECK(ca_group_encode(&g, &gen, w));
        ca_rng rng;
        ca_rng_seed(&rng, 200 + i);
        for (int k = 0; k < 6; k++) {
            uint64_t x = secret(&rng, p - 1, k), got = 0;
            ca_elem h;
            fx_instance(&g, &gen, x, &h);
            /* The public element agrees with plain modular exponentiation. */
            uint64_t hw[4];
            ca_group_decode(&g, hw, &h);
            CHECK_EQ_U64(hw[0], ca_powmod(root, x, p));
            CHECK(ca_dlog(&g, &gen, &h, &got, NULL) == CA_OK);
            CHECK_EQ_U64(got, x);
            ca_dlog_params dp;
            ca_dlog_params_default(&dp);
            dp.solver = CA_SOLVER_RHO;
            dp.rho.seed = 31;
            got = 0;
            CHECK(ca_pohlig_hellman(&g, &gen, &h, &dp, &got, NULL) == CA_OK);
            CHECK_EQ_U64(got, x);
        }
        printf("Z_p^* full group %u-bit p: Pohlig-Hellman (auto, rho) ok\n", zp_smooth[i].w);
    }
}

/* ---- interval solvers in prime-order groups with n > 2^50 -------------- */

static void solve_intervals(const ca_group *g, const ca_elem *gen, uint64_t n, uint64_t seed,
                            const char *label)
{
    const uint64_t half = UINT64_C(1) << 30;
    ca_rng rng;
    ca_rng_seed(&rng, seed);
    /* A 51-bit field has no prime subgroup above 2^50, so the "just above
     * 2^50" secret falls back to 3n/4 there. */
    const uint64_t above = UINT64_C(1) << 50;
    uint64_t xs[4] = {n - 1, n > above + 12345 ? above + 12345 : n - n / 4, n / 2 + 7,
                      n / 4 + ca_rng_below(&rng, n - n / 4)};
    for (int k = 0; k < 4; k++) {
        uint64_t x = xs[k];
        uint64_t lo = x > half ? x - half + 17 : 0;
        uint64_t hi = x + half - 5 < n ? x + half - 5 : n - 1;
        ca_elem h;
        fx_instance(g, gen, x, &h);
        uint64_t got = 0;
        CHECK(ca_bsgs_solve(g, gen, &h, lo, hi, NULL, &got, NULL) == CA_OK);
        CHECK_EQ_U64(got, x);
        ca_kangaroo_params kp;
        ca_kangaroo_params_default(&kp);
        kp.seed = seed + (uint64_t)k;
        got = 0;
        CHECK(ca_kangaroo_solve(g, gen, &h, lo, hi, &kp, &got, NULL) == CA_OK);
        CHECK_EQ_U64(got, x);
        got = 0;
        CHECK(ca_grumpy_solve(g, gen, &h, lo, hi, NULL, &got, NULL) == CA_OK);
        CHECK_EQ_U64(got, x);
        ca_dlog_params dp;
        ca_dlog_params_default(&dp);
        dp.solver = CA_SOLVER_KANGAROO;
        dp.kangaroo.seed = seed + 40 + (uint64_t)k;
        got = 0;
        CHECK(ca_dlog_prime_order(g, gen, &h, lo, hi, &dp, &got, NULL) == CA_OK);
        CHECK_EQ_U64(got, x);
        /* A target outside the interval is never reported as found. */
        if (lo > 0) {
            ca_elem out;
            fx_instance(g, gen, lo - 1, &out);
            CHECK(ca_bsgs_solve(g, gen, &out, lo, hi, NULL, &got, NULL) == CA_ERR_NOT_FOUND);
        }
    }
    /* A whole-group walk on a group this large is bounded, not hung. */
    ca_elem h;
    fx_instance(g, gen, xs[3], &h);
    ca_rho_params rp;
    ca_rho_params_default(&rp);
    rp.seed = seed;
    rp.max_ops = UINT64_C(1) << 16;
    uint64_t got = 0;
    CHECK(ca_rho_solve(g, gen, &h, &rp, &got, NULL) == CA_ERR_LIMIT);
    printf("%-28s n=%" PRIu64 ": bsgs kangaroo grumpy intervals ok\n", label, n);
}

static const struct {
    unsigned w;
    uint64_t p, q;
} zp_big[] = {
    {51, UINT64_C(2251799813684117), UINT64_C(562949953421029)},
    {53, UINT64_C(9007199254734533), UINT64_C(2251799813683633)},
    {57, UINT64_C(144115188075855077), UINT64_C(36028797018963769)},
    {62, UINT64_C(4611686018427386309), UINT64_C(1152921504606846577)},
    {63, UINT64_C(9223372036854774893), UINT64_C(2305843009213693723)},
    {64, UINT64_C(18446744073709548557), UINT64_C(4611686018427387139)},
};

static void test_zp_big_subgroups(void)
{
    for (size_t i = 0; i < sizeof(zp_big) / sizeof(zp_big[0]); i++) {
        uint64_t p = zp_big[i].p, q = zp_big[i].q;
        CHECK(bitlen(p) == zp_big[i].w);
        CHECK(ca_is_prime(p) && ca_is_prime(q) && (p - 1) % q == 0);
        ca_group g;
        ca_elem gen;
        CHECK(ca_group_zp_init(&g, p, q) == CA_OK);
        CHECK(ca_group_find_generator(&g, &gen, 2) == CA_OK);
        char label[48];
        snprintf(label, sizeof(label), "Z_p^* %u-bit p, q~p/4", zp_big[i].w);
        solve_intervals(&g, &gen, q, 300 + i, label);
    }
}

/* ---- E(F_p) -------------------------------------------------------------- */

/* Curves y^2 = x^3 + a x + b over p of the given width.  n is #E(F_p); q is
 * a prime factor of n above 2^50 with n / q <= 8. */
static const struct {
    unsigned w;
    uint64_t p, a, b, n, q;
} ec_big[] = {
    {51, UINT64_C(2251799813685119), 5, 41, UINT64_C(2251799819167454), UINT64_C(1125899909583727)},
    {53, UINT64_C(9007199254740881), 5, 6, UINT64_C(9007199358655084), UINT64_C(2251799839663771)},
    {57, UINT64_C(144115188075855859), 5, 24, UINT64_C(144115188187986376),
     UINT64_C(18014398523498297)},
    {62, UINT64_C(4611686018427387847), 5, 22, UINT64_C(4611686014677274734),
     UINT64_C(768614335779545789)},
    {63, UINT64_C(9223372036854775783), 5, 44, UINT64_C(9223372038972452885),
     UINT64_C(1844674407794490577)},
    {64, UINT64_C(18446744056529682403), 5, 5, UINT64_C(18446744051100303869),
     UINT64_C(2635249150157186267)},
};

/* Curves whose order n is 2^26-smooth. */
static const struct {
    unsigned w;
    uint64_t p, a, b, n;
} ec_smooth[] = {
    {51, UINT64_C(2251799813685119), 5, 4, UINT64_C(2251799886979090)},
    {53, UINT64_C(9007199254740881), 5, 9, UINT64_C(9007199342424104)},
    {57, UINT64_C(144115188075855859), 5, 10, UINT64_C(144115188260706215)},
    {62, UINT64_C(4611686018427387847), 5, 3, UINT64_C(4611686019314407504)},
    {63, UINT64_C(9223372036854775783), 5, 4, UINT64_C(9223372038715522660)},
    {64, UINT64_C(18446744056529682403), 5, 19, UINT64_C(18446744051126487276)},
};

static void check_curve_order(uint64_t p, uint64_t a, uint64_t b, uint64_t n)
{
    uint64_t counted = 0;
    CHECK(ca_ec_count_points(p, a, b, &counted, NULL) == CA_OK);
    CHECK_EQ_U64(counted, n);
    /* Hasse: |n - (p + 1)| <= 2 sqrt(p), evaluated without overflow. */
    unsigned __int128 lo = (unsigned __int128)p + 1 - 2 * ((unsigned __int128)ca_isqrt(p) + 1);
    unsigned __int128 hi = (unsigned __int128)p + 1 + 2 * ((unsigned __int128)ca_isqrt(p) + 1);
    CHECK((unsigned __int128)n >= lo && (unsigned __int128)n <= hi);
    ca_group full;
    CHECK(ca_group_ec_init(&full, p, a, b, n) == CA_OK);
    for (uint64_t s = 1; s <= 4; s++) {
        ca_elem pt, t;
        ca_ec_random_point(&full, &pt, s);
        CHECK(ca_group_is_valid(&full, &pt));
        ca_group_mul(&full, &t, &pt, n, NULL);
        CHECK(ca_group_is_identity(&full, &t));
    }
}

static void test_ec_big_subgroups(void)
{
    for (size_t i = 0; i < sizeof(ec_big) / sizeof(ec_big[0]); i++) {
        uint64_t p = ec_big[i].p, n = ec_big[i].n, q = ec_big[i].q;
        CHECK(bitlen(p) == ec_big[i].w && ca_is_prime(p));
        CHECK(ca_is_prime(q) && n % q == 0 && n / q <= 8);
        check_curve_order(p, ec_big[i].a, ec_big[i].b, n);
        ca_group g;
        ca_elem gen;
        CHECK(ca_group_ec_init(&g, p, ec_big[i].a, ec_big[i].b, q) == CA_OK);
        g.cofactor = n / q;
        CHECK(ca_group_find_generator(&g, &gen, 3) == CA_OK);
        char label[48];
        snprintf(label, sizeof(label), "E(F_p) %u-bit p, q>2^50", ec_big[i].w);
        solve_intervals(&g, &gen, q, 400 + i, label);
    }
}

static void test_ec_smooth_orders(void)
{
    for (size_t i = 0; i < sizeof(ec_smooth) / sizeof(ec_smooth[0]); i++) {
        uint64_t p = ec_smooth[i].p, a = ec_smooth[i].a, b = ec_smooth[i].b, n = ec_smooth[i].n;
        CHECK(bitlen(p) == ec_smooth[i].w && ca_is_prime(p));
        check_curve_order(p, a, b, n);
        ca_factorization f;
        CHECK(ca_factorize(n, &f) == CA_OK);
        uint64_t l = f.f[f.count - 1].p;
        CHECK(l < (1ULL << 26));

        /* Whole group: a point of the largest order found, which exceeds 2^50. */
        ca_group full;
        CHECK(ca_group_ec_init(&full, p, a, b, n) == CA_OK);
        ca_elem pt;
        ca_group_identity(&full, &pt);
        uint64_t m = 0;
        for (uint64_t s = 1; s < 64 && m != n; s++) {
            ca_elem cand;
            ca_ec_random_point(&full, &cand, 1000 + s);
            uint64_t o = ca_group_elem_order(&full, &cand);
            if (o > m) {
                m = o;
                pt = cand;
            }
        }
        CHECK(m > (1ULL << 50));
        if (m == 0 || n % m != 0) {
            CHECK(0); /* no point order found: the table entry is wrong */
            continue;
        }
        ca_group g;
        CHECK(ca_group_ec_init(&g, p, a, b, m) == CA_OK);
        g.cofactor = n / m;
        ca_rng rng;
        ca_rng_seed(&rng, 500 + i);
        for (int k = 0; k < 5; k++) {
            uint64_t x = secret(&rng, m, k), got = 0;
            ca_elem h;
            fx_instance(&g, &pt, x, &h);
            CHECK(ca_dlog(&g, &pt, &h, &got, NULL) == CA_OK);
            CHECK_EQ_U64(got, x);
        }

        /* Prime subgroup of order l with full-width coordinates. */
        ca_group sub;
        ca_elem gen;
        CHECK(ca_group_ec_init(&sub, p, a, b, l) == CA_OK);
        sub.cofactor = n / l;
        CHECK(ca_group_find_generator(&sub, &gen, 5) == CA_OK);
        char label[48];
        snprintf(label, sizeof(label), "E(F_p) %u-bit p, small q", ec_smooth[i].w);
        solve_all_prime_order(&sub, &gen, l, 600 + i, label);
        printf("E(F_p) %u-bit p: order %" PRIu64 " point, Pohlig-Hellman ok\n", ec_smooth[i].w, m);
    }
}

/* ---- curve dispatch with GLV endomorphisms ------------------------------ */

static const struct {
    unsigned w;
    uint64_t p, a, b, n, q;
    ca_curve_endo endo;
} glv[] = {
    {53, UINT64_C(9007199254740847), 0, 2, UINT64_C(9007199064930339), UINT64_C(4145420677),
     CA_CURVE_ENDO_J0},
    {53, UINT64_C(9007199254740881), 3, 0, UINT64_C(9007199236715914), UINT64_C(1770421357),
     CA_CURVE_ENDO_J1728},
    {64, UINT64_C(18446744056529682403), 0, 3, UINT64_C(18446744059886038099), UINT64_C(8377462789),
     CA_CURVE_ENDO_J0},
};

static void test_glv_curves(void)
{
    for (size_t i = 0; i < sizeof(glv) / sizeof(glv[0]); i++) {
        uint64_t p = glv[i].p, n = glv[i].n, q = glv[i].q;
        CHECK(bitlen(p) == glv[i].w && ca_is_prime(p) && ca_is_prime(q) && n % q == 0);
        check_curve_order(p, glv[i].a, glv[i].b, n);
        ca_group g;
        ca_curve_info info;
        CHECK(ca_curve_group(&g, p, glv[i].a, glv[i].b, q, &info) == CA_OK);
        CHECK(info.endo == glv[i].endo);
        g.cofactor = n / q;
        ca_elem gen;
        CHECK(ca_group_find_generator(&g, &gen, 9) == CA_OK);
        ca_rng rng;
        ca_rng_seed(&rng, 700 + i);
        for (int k = 0; k < 4; k++) {
            uint64_t x = secret(&rng, q, k), got = 0;
            ca_elem h;
            fx_instance(&g, &gen, x, &h);
            CHECK(ca_curve_solve(&g, &gen, &h, 17 + (uint64_t)k, &got, &info, NULL) == CA_OK);
            CHECK_EQ_U64(got, x);
        }
        printf("GLV %s %u-bit p, q=%" PRIu64 ": curve solve ok\n",
               glv[i].endo == CA_CURVE_ENDO_J0 ? "j=0" : "j=1728", glv[i].w, q);
    }
}

/* ---- Cheon: prime order Q > 2^50, d | Q - 1 ----------------------------- */

static const struct {
    unsigned w;
    uint64_t p, Q, d;
} cheon[] = {
    {53, UINT64_C(4503721899953099), UINT64_C(2251860949976549), 33554501},
    {62, UINT64_C(4458573331013088541), UINT64_C(2251804712632873), 33554501},
    {64, UINT64_C(18442280596463229871), UINT64_C(2251804712632873), 33554501},
};

static void test_cheon(void)
{
    for (size_t i = 0; i < sizeof(cheon) / sizeof(cheon[0]); i++) {
        uint64_t p = cheon[i].p, Q = cheon[i].Q, d = cheon[i].d;
        CHECK(bitlen(p) == cheon[i].w && ca_is_prime(p) && ca_is_prime(Q));
        CHECK((p - 1) % Q == 0 && (Q - 1) % d == 0 && Q > (1ULL << 50));
        ca_group g;
        ca_elem gen;
        CHECK(ca_group_zp_init(&g, p, Q) == CA_OK);
        CHECK(ca_group_find_generator(&g, &gen, 4) == CA_OK);
        ca_rng rng;
        ca_rng_seed(&rng, 800 + i);
        for (int k = 1; k < 4; k++) {
            uint64_t alpha = secret(&rng, Q, k), got = 0;
            ca_elem ga, gad;
            CHECK(ca_cheon_make_instance(&g, &gen, alpha, d, &ga, &gad) == CA_OK);
            CHECK(ca_cheon_solve(&g, &gen, &ga, &gad, d, NULL, &got, NULL) == CA_OK);
            CHECK_EQ_U64(got, alpha);
        }
        printf("Cheon %u-bit p, Q=%" PRIu64 " (51 bits): ok\n", cheon[i].w, Q);
    }
}

int main(void)
{
    test_zp_small_subgroups();
    test_zp_full_group();
    test_zp_big_subgroups();
    test_ec_big_subgroups();
    test_ec_smooth_orders();
    test_glv_curves();
    test_cheon();
    TEST_MAIN_END();
}
