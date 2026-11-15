/* Inputs outside a solver's contract must end with a status, not hang or
 * trap: composite subgroup orders, targets outside the subgroup or the
 * interval, zero moduli, oversized tables, composite linear-algebra moduli.
 * Also the operation count of the checkpointed BSGS path, against the
 * operations a counting vtable sees.
 *
 * Every case that used to loop forever runs under a watchdog: SIGALRM ends
 * the process with a message naming the case, so a regression fails in
 * seconds.  CMake adds a test timeout for builds where the signal is
 * delivered late (ThreadSanitizer defers it to the next intercepted call). */
#include "test_fixtures.h"
#include "linalg.h"
#include <signal.h>
#include <unistd.h>

static const char *watch_case = "";

static void on_alarm(int sig)
{
    (void)sig;
    static const char head[] = "HANG: ";
    if (write(2, head, sizeof head - 1) > 0 && write(2, watch_case, strlen(watch_case)) > 0 &&
        write(2, "\n", 1) > 0)
        _exit(1);
    _exit(1);
}

/* Generous by default: the slowest case is seconds in a sanitizer build.
 * CA_TEST_WATCHDOG_SECONDS shortens it when checking that a case hangs. */
static unsigned watch_seconds = 120;
#define WATCH(name)                                                                                \
    do {                                                                                           \
        watch_case = (name);                                                                       \
        alarm(watch_seconds);                                                                      \
    } while (0)
#define UNWATCH() alarm(0)

static void zp_elem(const ca_group *g, ca_elem *e, uint64_t v)
{
    const uint64_t w[4] = {v, 0, 0, 0};
    CHECK(ca_group_encode(g, e, w));
}

/* ---- S-5: zero modulus -------------------------------------------------- */

static void zero_modulus(void)
{
    CHECK_EQ_U64(ca_powmod(2, 5, 0), 0);  /* plain ladder */
    CHECK_EQ_U64(ca_powmod(2, 50, 0), 0); /* exponent on the Montgomery side */
    CHECK_EQ_U64(ca_powmod(0, 0, 0), 0);
    CHECK_EQ_U64(ca_powmod(7, 3, 1), 0);
    CHECK_EQ_U64(ca_ffi_powmod(2, 5, 0), 0);
    CHECK_EQ_U64(ca_ffi_powmod(2, 50, 0), 0);
    CHECK(ca_legendre(2, 0) == 0);
    CHECK(ca_legendre(0, 0) == 0);
    CHECK_EQ_U64(ca_mult_order(2, 0), 0);
    uint64_t r = 99;
    CHECK(ca_sqrtmod_prime(1, 0, &r) == 0);
    /* unchanged answers next to the guards */
    CHECK_EQ_U64(ca_powmod(3, 100, 1000003), 189751);
    CHECK(ca_legendre(2, 7) == 1 && ca_legendre(3, 7) == -1 && ca_legendre(14, 7) == 0);
    CHECK_EQ_U64(ca_mult_order(2, 7), 3);
}

/* ---- S-1: square roots and curve detection on a composite order --------- */

static void sqrtmod_terminates(void)
{
    uint64_t r = 0;
    WATCH("ca_sqrtmod_prime(24, 25)");
    CHECK(ca_sqrtmod_prime(24, 25, &r) == 0);
    /* every modulus below 3000, composite or not, with the residues the
     * eigenvalue search asks for (n - 1, n - 3) and a few more */
    WATCH("ca_sqrtmod_prime over all moduli below 3000");
    for (uint64_t n = 1; n < 3000; n++) {
        const uint64_t as[] = {n - 1, n >= 3 ? n - 3 : 0, 1, 2, 4, n / 2, n / 3 + 1};
        for (size_t i = 0; i < sizeof as / sizeof as[0]; i++) {
            uint64_t a = as[i] % n;
            r = n; /* out of range unless written */
            int ok = ca_sqrtmod_prime(a, n, &r);
            if (!ca_is_prime(n)) continue; /* outside the contract: only termination */
            /* a prime modulus keeps its answers */
            if (ok)
                CHECK_EQ_U64(ca_mulmod(r, r, n), a);
            else
                CHECK(n > 2 && ca_legendre(a, n) == -1);
        }
    }
    /* composites near 2^64 and with large prime factors */
    WATCH("ca_sqrtmod_prime on large composites");
    const uint64_t big[] = {UINT64_MAX,
                            UINT64_MAX - 2,
                            1000003ULL * 1000033ULL,
                            4294967291ULL * 4294967279ULL,
                            (1ULL << 63) + 1,
                            (1ULL << 62),
                            561,
                            1105,
                            1729,
                            2465,
                            3215031751ULL};
    for (size_t i = 0; i < sizeof big / sizeof big[0]; i++) {
        if (ca_is_prime(big[i])) continue;
        (void)ca_sqrtmod_prime(big[i] - 1, big[i], &r);
        (void)ca_sqrtmod_prime(big[i] - 3, big[i], &r);
        (void)ca_sqrtmod_prime(4, big[i], &r);
    }
    UNWATCH();
}

/* A point of exact order n on the full curve group, if this seed gives one. */
static int point_of_order(const ca_group *full, uint64_t N, uint64_t n, ca_elem *P)
{
    ca_factorization f;
    ca_factorize(n, &f);
    for (uint64_t seed = 1; seed < 200; seed++) {
        ca_ec_random_point(full, P, seed);
        ca_group_mul(full, P, P, N / n, NULL);
        int exact = !ca_group_is_identity(full, P);
        for (unsigned i = 0; exact && i < f.count; i++) {
            ca_elem t;
            ca_group_mul(full, &t, P, n / f.f[i].p, NULL);
            if (ca_group_is_identity(full, &t)) exact = 0;
        }
        if (exact) return 1;
    }
    return 0;
}

static void composite_order_curve(uint64_t p, uint64_t a, uint64_t b, uint64_t n)
{
    char label[96];
    snprintf(label, sizeof label,
             "ca_curve_detect/group p=%" PRIu64 " a=%" PRIu64 " b=%" PRIu64 " order=%" PRIu64, p, a,
             b, n);
    uint64_t N = 0;
    CHECK(ca_ec_count_points(p, a, b, &N, NULL) == CA_OK);
    CHECK(N % n == 0 && !ca_is_prime(n));
    WATCH(label);
    ca_curve_info info;
    memset(&info, 0xff, sizeof info);
    CHECK(ca_curve_detect(p, a, b, n, &info) == CA_OK);
    CHECK(info.endo == CA_CURVE_ENDO_NONE);
    CHECK_EQ_U64(info.aut_order, 2);
    ca_group g;
    memset(&info, 0xff, sizeof info);
    CHECK(ca_curve_group(&g, p, a, b, n, &info) == CA_OK);
    /* the plain path: negation only, no endomorphism left on the group */
    CHECK(info.endo == CA_CURVE_ENDO_NONE);
    CHECK_EQ_U64(info.aut_order, 2);
    CHECK_EQ_U64(g.endo_kind, 0);
    CHECK_EQ_U64(g.endo_lambda, 0);
    CHECK_EQ_U64(g.order, n);
    /* and it still solves in that subgroup */
    ca_group full;
    ca_elem P, Q;
    CHECK(ca_group_ec_init(&full, p, a, b, N) == CA_OK);
    if (point_of_order(&full, N, n, &P)) {
        for (uint64_t k = 0; k < n; k += n / 7 + 1) {
            uint64_t x = UINT64_MAX;
            ca_group_mul(&g, &Q, &P, k, NULL);
            CHECK(ca_curve_solve(&g, &P, &Q, 1 + k, &x, NULL, NULL) == CA_OK);
            CHECK_EQ_U64(x, k);
        }
    }
    UNWATCH();
}

static void composite_order_curves(void)
{
    /* the review's input: y^2 = x^3 + 9x over F_89, #E = 100, order 25 */
    composite_order_curve(89, 9, 0, 25);
    /* every composite divisor n = 1 mod 4 (j = 1728) or 1 mod 3 (j = 0) of
     * the group order, on small curves of both shapes */
    for (uint64_t p = 13; p < 200; p = ca_next_prime(p)) {
        for (uint64_t c = 1; c < 6; c++) {
            for (int shape = 0; shape < 2; shape++) {
                uint64_t a = shape ? c : 0, b = shape ? 0 : c, N = 0;
                if (p % (shape ? 4 : 3) != 1) continue;
                if (ca_ec_count_points(p, a, b, &N, NULL) != CA_OK) continue;
                for (uint64_t n = 4; n <= N; n++)
                    if (N % n == 0 && !ca_is_prime(n) && n % (shape ? 4 : 3) == 1)
                        composite_order_curve(p, a, b, n);
            }
        }
    }
    /* a prime order keeps the endomorphism */
    ca_curve_info info;
    uint64_t p, a, b, n;
    CHECK(ca_curve_by_name("glv-j0-26", &p, &a, &b, &n) == CA_OK && ca_is_prime(n));
    CHECK(ca_curve_detect(p, a, b, n, &info) == CA_OK);
    CHECK(info.endo == CA_CURVE_ENDO_J0 && info.aut_order == 6 && info.lambda > 1);
    CHECK(ca_curve_by_name("glv-j1728-26", &p, &a, &b, &n) == CA_OK && ca_is_prime(n));
    CHECK(ca_curve_detect(p, a, b, n, &info) == CA_OK);
    CHECK(info.endo == CA_CURVE_ENDO_J1728 && info.aut_order == 4 && info.lambda > 1);
}

/* ---- S-2: rho with a target outside <base> ------------------------------ */

static void rho_target_outside_subgroup(void)
{
    /* Z_p^*, n = p - 1 composite, base g^2, target g: n * target = 1 passes
     * the membership test, and no logarithm exists. */
    const uint64_t p = 1000003;
    ca_group g;
    CHECK(ca_group_zp_init(&g, p, 0) == CA_OK);
    const uint64_t root = ca_primitive_root(p);
    ca_elem base, target;
    zp_elem(&g, &base, ca_powmod(root, 2, p));
    zp_elem(&g, &target, root);
    /* the built-in guard, with room for the batch that crosses it and the
     * multiplier/start-up operations counted beside the walk */
    const uint64_t guard = 64 * (ca_isqrt(p - 1) + 1) + (1u << 20);
    const uint64_t slack = 1u << 18;
    uint64_t x = 0;

    /* bounded by the caller: the explicit limit and its status are unchanged */
    ca_rho_params rp;
    ca_rho_params_default(&rp);
    rp.seed = 3;
    rp.max_ops = 20000;
    ca_stats st = {0};
    WATCH("ca_rho_solve unsolvable, max_ops = 20000");
    CHECK(ca_rho_solve(&g, &base, &target, &rp, &x, &st) == CA_ERR_LIMIT);
    CHECK(st.group_ops > 20000 && st.group_ops < 20000 + slack);

    /* default parameters: the runaway guard ends the walk */
    memset(&st, 0, sizeof st);
    WATCH("ca_rho_solve unsolvable, default parameters (NULL)");
    CHECK(ca_rho_solve(&g, &base, &target, NULL, &x, &st) == CA_ERR_NOT_FOUND);
    CHECK(st.group_ops > guard && st.group_ops < guard + slack);

    /* an explicit dp_bits widens the guard by 64 * walks * 2^dp = 16384 and no more */
    ca_rho_params_default(&rp);
    rp.seed = 5;
    rp.dp_bits = 6;
    rp.walks_per_thread = 4;
    memset(&st, 0, sizeof st);
    WATCH("ca_rho_solve unsolvable, dp_bits = 6");
    CHECK(ca_rho_solve(&g, &base, &target, &rp, &x, &st) == CA_ERR_NOT_FOUND);
    CHECK(st.group_ops > guard + 16384u && st.group_ops < guard + 16384u + slack);

    /* two threads share the guard */
    ca_rho_params_default(&rp);
    rp.seed = 7;
    rp.threads = 2;
    memset(&st, 0, sizeof st);
    WATCH("ca_rho_solve unsolvable, 2 threads");
    CHECK(ca_rho_solve(&g, &base, &target, &rp, &x, &st) == CA_ERR_NOT_FOUND);
    CHECK(st.group_ops > guard && st.group_ops < guard + 8192u + 2 * slack);

    /* the generic dispatcher on the same instance */
    WATCH("ca_dlog unsolvable");
    CHECK(ca_dlog(&g, &base, &target, &x, NULL) != CA_OK);

    /* solvable instances in the same composite-order group are untouched:
     * bases of order n, n/2 and n/6, default limit */
    WATCH("ca_rho_solve solvable, composite order");
    ca_rng rng;
    ca_rng_seed(&rng, 17);
    for (int i = 0; i < 24; i++) {
        const uint64_t e = i % 3 == 0 ? 2 : (i % 3 == 1 ? 6 : 1);
        const uint64_t k = ca_rng_below(&rng, p - 1);
        const uint64_t bv = ca_powmod(root, e, p), tv = ca_powmod(bv, k, p);
        zp_elem(&g, &base, bv);
        zp_elem(&g, &target, tv);
        ca_rho_params_default(&rp);
        rp.seed = 100 + (uint64_t)i;
        memset(&st, 0, sizeof st);
        CHECK(ca_rho_solve(&g, &base, &target, &rp, &x, &st) == CA_OK);
        CHECK_EQ_U64(ca_powmod(bv, x, p), tv);
        CHECK(st.group_ops < guard / 4); /* nowhere near the guard */
    }
    UNWATCH();
}

/* The same instance on the GPU solver's host emulator. */
static void gpu_rho_target_outside_subgroup(void)
{
    const uint64_t p = 1000003;
    ca_group g;
    CHECK(ca_group_zp_init(&g, p, 0) == CA_OK);
    const uint64_t root = ca_primitive_root(p);
    ca_elem base, target;
    zp_elem(&g, &base, ca_powmod(root, 2, p));
    zp_elem(&g, &target, root);
    uint64_t x = 0;
    ca_gpu_rho_params gp;
    ca_gpu_rho_params_default(&gp);
    gp.backend = CA_GPU_BACKEND_EMULATE;
    gp.seed = 3;
    gp.max_ops = 20000;
    ca_stats st = {0};
    WATCH("ca_gpu_rho_solve unsolvable, max_ops = 20000");
    CHECK(ca_gpu_rho_solve(&g, &base, &target, &gp, &x, &st) == CA_ERR_LIMIT);
    gp.max_ops = 0;
    memset(&st, 0, sizeof st);
    WATCH("ca_gpu_rho_solve unsolvable, default max_ops");
    CHECK(ca_gpu_rho_solve(&g, &base, &target, &gp, &x, &st) == CA_ERR_NOT_FOUND);
    /* at least the 64 sqrt(n) + 2^20 floor of the guard, and not far past it */
    CHECK(st.group_ops > 64 * (ca_isqrt(p - 1) + 1) + (1u << 20));
    CHECK(st.group_ops < (uint64_t)1 << 23);
    WATCH("ca_gpu_rho_solve solvable, composite order");
    for (int i = 0; i < 6; i++) {
        const uint64_t k = 1 + 166661 * (uint64_t)i, tv = ca_powmod(root, k, p);
        zp_elem(&g, &base, root);
        zp_elem(&g, &target, tv);
        gp.seed = 40 + (uint64_t)i;
        CHECK(ca_gpu_rho_solve(&g, &base, &target, &gp, &x, NULL) == CA_OK);
        CHECK_EQ_U64(ca_powmod(root, x, p), tv);
    }
    UNWATCH();
}

/* ---- S-3: kangaroo with the logarithm outside the interval -------------- */

static void kangaroo_log_outside_interval(void)
{
    const uint64_t p = 1000003, lo = 1000, hi = 101000;
    ca_group g;
    CHECK(ca_group_zp_init(&g, p, 0) == CA_OK);
    const uint64_t root = ca_primitive_root(p);
    ca_elem base, target;
    zp_elem(&g, &base, root);
    zp_elem(&g, &target, ca_powmod(root, 900000, p));
    const uint64_t guard = 256 * (ca_isqrt(hi - lo) + 1) + (1u << 20);
    const uint64_t slack = 1u << 18;
    uint64_t x = 0;

    ca_kangaroo_params kp;
    ca_kangaroo_params_default(&kp);
    kp.seed = 3;
    kp.max_ops = 20000;
    ca_stats st = {0};
    WATCH("ca_kangaroo_solve outside interval, max_ops = 20000");
    CHECK(ca_kangaroo_solve(&g, &base, &target, lo, hi, &kp, &x, &st) == CA_ERR_LIMIT);
    CHECK(st.group_ops > 20000 && st.group_ops < 20000 + slack);

    memset(&st, 0, sizeof st);
    WATCH("ca_kangaroo_solve outside interval, default parameters (NULL)");
    CHECK(ca_kangaroo_solve(&g, &base, &target, lo, hi, NULL, &x, &st) == CA_ERR_NOT_FOUND);
    CHECK(st.group_ops > guard && st.group_ops < guard + slack);

    /* a caller's jump table adds 4 * width to the guard */
    ca_kangaroo_params_default(&kp);
    kp.seed = 5;
    kp.jumps = 4;
    memset(&st, 0, sizeof st);
    WATCH("ca_kangaroo_solve outside interval, jumps = 4");
    CHECK(ca_kangaroo_solve(&g, &base, &target, lo, hi, &kp, &x, &st) == CA_ERR_NOT_FOUND);
    CHECK(st.group_ops > guard + 4 * (hi - lo) && st.group_ops < guard + 4 * (hi - lo) + slack);

    /* logarithms inside the interval, its ends included, are untouched */
    WATCH("ca_kangaroo_solve inside interval");
    ca_rng rng;
    ca_rng_seed(&rng, 23);
    for (int i = 0; i < 24; i++) {
        const uint64_t k = i == 0 ? lo : (i == 1 ? hi : lo + ca_rng_below(&rng, hi - lo + 1));
        zp_elem(&g, &target, ca_powmod(root, k, p));
        ca_kangaroo_params_default(&kp);
        kp.seed = 200 + (uint64_t)i;
        memset(&st, 0, sizeof st);
        CHECK(ca_kangaroo_solve(&g, &base, &target, lo, hi, &kp, &x, &st) == CA_OK);
        CHECK_EQ_U64(x, k);
        CHECK(st.group_ops < guard / 4);
    }
    UNWATCH();
}

/* ---- S-4: checkpointed BSGS counts each baby step once ------------------- */

static const ca_group_vtable *count_inner;
static uint64_t count_ops;

static void count_op(const ca_group *g, ca_elem *r, const ca_elem *a, const ca_elem *b)
{
    count_ops++;
    count_inner->op(g, r, a, b);
}

static void count_dbl(const ca_group *g, ca_elem *r, const ca_elem *a)
{
    count_ops++;
    count_inner->dbl(g, r, a);
}

static void count_batch(const ca_group *g, ca_elem *r, const ca_elem *a, const ca_elem *b, size_t n,
                        uint64_t *scratch)
{
    count_ops += n;
    count_inner->batch_op(g, r, a, b, n, scratch);
}

static void bsgs_checkpointed_count(const ca_group *g0, const ca_elem *gen, const char *name)
{
    ca_group g = *g0;
    ca_group_vtable vt = *g0->vt;
    count_inner = g0->vt;
    vt.op = count_op;
    vt.dbl = count_dbl;
    vt.batch_op = count_batch;
    g.vt = &vt;
    const uint64_t n = g0->order;
    const uint64_t ks[] = {n - 5, n / 2, n / 3 + 1, 7};
    /* What the checkpointed path may differ by from the operations performed
     * and from the plain path: O(log n) scalar-multiplication set-up, and
     * the up to BSGS_LANES - 1 lane elements computed past the last one
     * used at the end of each phase (64 lanes).  The double count this
     * guards against was m = sqrt(n) operations, thousands here. */
    const uint64_t tol = 2 * 64 + 4 * 64;
    for (size_t i = 0; i < sizeof ks / sizeof ks[0]; i++) {
        ca_elem h;
        uint64_t x = 0;
        ca_stats plain = {0}, ck = {0};
        ca_group_mul(g0, &h, gen, ks[i], NULL);
        CHECK(ca_bsgs_solve(&g, gen, &h, 0, n - 1, NULL, &x, &plain) == CA_OK);
        CHECK_EQ_U64(x, ks[i]);
        count_ops = 0;
        CHECK(ca_bsgs_solve_checkpointed(&g, gen, &h, 0, n - 1, NULL, NULL, 0, 0, 0, &x, &ck) ==
              CA_OK);
        CHECK_EQ_U64(x, ks[i]);
        const uint64_t performed = count_ops, reported = ck.group_ops;
        CHECK(reported <= performed + tol && performed <= reported + tol);
        /* the plain path leaves out the one advance per 64-lane giant block
         * that the checkpointed path charges: 1/64 of the giant steps */
        CHECK(reported <= plain.group_ops + plain.group_ops / 32 + tol &&
              plain.group_ops <= reported + tol);
        if (i == 0)
            printf("%-22s checkpointed bsgs reported/performed = %" PRIu64 "/%" PRIu64
                   " = %.4f (plain %" PRIu64 ")\n",
                   name, reported, performed, (double)reported / (double)performed,
                   plain.group_ops);
    }
}

static void bsgs_resume_count(void)
{
    /* Stop in the baby phase, resume from the file: the solve completes and
     * the total stays within one resume's set-up of an uninterrupted run. */
    ca_group g;
    ca_elem gen, h;
    fx_zp_safe(&g, &gen, 2000000579ULL);
    const uint64_t n = g.order, k = n - 12345;
    fx_instance(&g, &gen, k, &h);
    char path[] = "/tmp/ca_test_robustness_bsgs_XXXXXX";
    int fd = mkstemp(path);
    CHECK(fd >= 0);
    if (fd < 0) return;
    close(fd);
    remove(path);
    uint64_t x = 0;
    ca_stats whole = {0}, part = {0}, rest = {0};
    CHECK(ca_bsgs_solve_checkpointed(&g, &gen, &h, 0, n - 1, NULL, NULL, 0, 0, 0, &x, &whole) ==
          CA_OK);
    ca_bsgs_params bp;
    ca_bsgs_params_default(&bp);
    bp.max_ops = 5000;
    CHECK(ca_bsgs_solve_checkpointed(&g, &gen, &h, 0, n - 1, &bp, path, 0, 0, 0, &x, &part) ==
          CA_ERR_LIMIT);
    CHECK(part.group_ops > 5000 && part.group_ops <= 5000 + 64);
    bp.max_ops = 0;
    CHECK(ca_bsgs_solve_checkpointed(&g, &gen, &h, 0, n - 1, &bp, path, 0, 0, 0, &x, &rest) ==
          CA_OK);
    CHECK_EQ_U64(x, k);
    /* the resumed call reports the cumulative count */
    CHECK(rest.group_ops >= whole.group_ops && rest.group_ops <= whole.group_ops + 256u);
    remove(path);
    char side[sizeof path + 16];
    snprintf(side, sizeof side, "%s.progress.json", path);
    remove(side);
}

/* ---- S-6: hash tables larger than the address space --------------------- */

static void oversized_tables(void)
{
    ca_htab t;
    ca_htab1 t1;
    const size_t sizes[] = {SIZE_MAX / 4 + 1, SIZE_MAX / 2, SIZE_MAX / 2 + 1, SIZE_MAX};
    WATCH("ca_htab_init / ca_htab1_init above SIZE_MAX / 4");
    for (size_t i = 0; i < sizeof sizes / sizeof sizes[0]; i++) {
        CHECK(ca_htab_init(&t, sizes[i]) == CA_ERR_NOMEM);
        CHECK(t.e == NULL);
        ca_htab_free(&t);
        CHECK(ca_htab1_init(&t1, sizes[i]) == CA_ERR_NOMEM);
        CHECK(t1.e == NULL);
        ca_htab1_free(&t1);
    }
    /* small tables still come up */
    CHECK(ca_htab_init(&t, 0) == CA_OK);
    ca_htab_free(&t);
    CHECK(ca_htab1_init(&t1, 100) == CA_OK);
    ca_htab1_free(&t1);
    UNWATCH();
}

/* ---- S-7: dense solve with a composite modulus -------------------------- */

static void dense_composite_modulus(void)
{
    /* 2x = 1 (mod 6) has no solution; the pivot 2 has no inverse */
    uint64_t M1[1] = {2}, r1[1] = {1}, x1[1] = {99};
    CHECK(ca_dense_solve_mod_prime(M1, 1, r1, 6, x1) == CA_ERR_SINGULAR);
    /* a zero-divisor pivot is refused even where a solution exists */
    uint64_t M2[4] = {2, 1, 1, 1}, r2[2] = {3, 2}, x2[2] = {99, 99};
    CHECK(ca_dense_solve_mod_prime(M2, 2, r2, 6, x2) == CA_ERR_SINGULAR);
    /* the row-operation path (q >= 2^63) */
    uint64_t M3[1] = {2}, r3[1] = {1}, x3[1] = {99};
    CHECK(ca_dense_solve_mod_prime(M3, 1, r3, ((uint64_t)1 << 63) + 2, x3) == CA_ERR_SINGULAR);
    /* unit pivots modulo a composite still solve: x = (1, 1) mod 6 */
    uint64_t M4[4] = {1, 1, 0, 5}, r4[2] = {2, 5}, x4[2] = {99, 99};
    CHECK(ca_dense_solve_mod_prime(M4, 2, r4, 6, x4) == CA_OK);
    CHECK_EQ_U64(x4[0], 1);
    CHECK_EQ_U64(x4[1], 1);
    /* a prime modulus is unchanged: 2x = 1 (mod 7) */
    uint64_t M5[1] = {2}, r5[1] = {1}, x5[1] = {99};
    CHECK(ca_dense_solve_mod_prime(M5, 1, r5, 7, x5) == CA_OK);
    CHECK_EQ_U64(x5[0], 4);
}

static void bsgs_counts(void)
{
    ca_group g;
    ca_elem gen;
    fx_zp_safe(&g, &gen, 2000000579ULL);
    bsgs_checkpointed_count(&g, &gen, "zp 31-bit");
    fx_ec(&g, &gen, 1000000007ULL, 3, 11);
    bsgs_checkpointed_count(&g, &gen, "ec 28-bit");
    bsgs_resume_count();
}

/* With no argument every case runs; one argument names a single case. */
int main(int argc, char **argv)
{
    static const struct {
        const char *name;
        void (*fn)(void);
    } cases[] = {
        {"zero-modulus", zero_modulus},
        {"sqrtmod", sqrtmod_terminates},
        {"composite-order-curve", composite_order_curves},
        {"rho-outside-subgroup", rho_target_outside_subgroup},
        {"gpu-rho-outside-subgroup", gpu_rho_target_outside_subgroup},
        {"kangaroo-outside-interval", kangaroo_log_outside_interval},
        {"bsgs-count", bsgs_counts},
        {"oversized-table", oversized_tables},
        {"dense-composite", dense_composite_modulus},
    };
    const char *secs = getenv("CA_TEST_WATCHDOG_SECONDS");
    if (secs && strtoul(secs, NULL, 10) > 0) watch_seconds = (unsigned)strtoul(secs, NULL, 10);
    signal(SIGALRM, on_alarm);
    int ran = 0;
    for (size_t i = 0; i < sizeof cases / sizeof cases[0]; i++) {
        if (argc > 1 && strcmp(argv[1], cases[i].name) != 0) continue;
        cases[i].fn();
        ran++;
    }
    CHECK(ran > 0);
    TEST_MAIN_END();
}
