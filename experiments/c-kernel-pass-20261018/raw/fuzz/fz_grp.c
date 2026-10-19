#include "cryptanalysis/cryptanalysis.h"
#include "ca_internal.h"
#include <stdio.h>
static ca_rng R;
static uint64_t rnd(void) { return ca_rng_next(&R); }
static int fails;
#define F(...)                                                                                     \
    do {                                                                                           \
        fails++;                                                                                   \
        if (fails < 60) {                                                                          \
            printf(__VA_ARGS__);                                                                   \
            printf("\n");                                                                          \
        }                                                                                          \
    } while (0)
static const char *nm(ca_status s) { return ca_status_string(s); }
/* does a solution in [lo,hi] exist? */
static int exists(const ca_group *g, const ca_elem *b, const ca_elem *t, uint64_t lo, uint64_t hi)
{
    ca_elem c;
    ca_group_mul(g, &c, b, lo, NULL);
    for (uint64_t k = lo;; k++) {
        if (ca_group_equal(g, &c, t)) return 1;
        if (k == hi) break;
        ca_group_op(g, &c, &c, b);
    }
    return 0;
}
static void check_interval(const ca_group *g, const ca_elem *b, const ca_elem *t, uint64_t lo,
                           uint64_t hi, const char *tag, int solver)
{
    uint64_t x = 0;
    ca_stats st;
    memset(&st, 0, sizeof st);
    ca_status rc;
    ca_kangaroo_params kp;
    ca_kangaroo_params_default(&kp);
    kp.seed = rnd() | 1;
    kp.max_ops = 2000000;
    ca_grumpy_params gp;
    ca_grumpy_params_default(&gp);
    gp.max_ops = 2000000;
    ca_rho_params rp;
    ca_rho_params_default(&rp);
    rp.seed = rnd() | 1;
    rp.max_ops = 2000000;
    switch (solver) {
    case 0: rc = ca_bsgs_solve(g, b, t, lo, hi, NULL, &x, &st); break;
    case 1: rc = ca_kangaroo_solve(g, b, t, lo, hi, &kp, &x, &st); break;
    case 2: rc = ca_grumpy_solve(g, b, t, lo, hi, &gp, &x, &st); break;
    default: {
        ca_dlog_params dp;
        ca_dlog_params_default(&dp);
        dp.solver = CA_SOLVER_AUTO;
        rc = ca_dlog_prime_order(g, b, t, lo, hi, &dp, &x, &st);
    }
    }
    int ex = exists(g, b, t, lo, hi);
    if (rc == CA_OK) {
        ca_elem c;
        ca_group_mul(g, &c, b, x, NULL);
        if (!ca_group_equal(g, &c, t))
            F("%s solver%d WRONG x=%llu lo=%llu hi=%llu", tag, solver, (unsigned long long)x,
              (unsigned long long)lo, (unsigned long long)hi);
        else if (x < lo || x > hi)
            F("%s solver%d OUT OF RANGE x=%llu lo=%llu hi=%llu n=%llu", tag, solver,
              (unsigned long long)x, (unsigned long long)lo, (unsigned long long)hi,
              (unsigned long long)g->order);
    } else if (ex && rc != CA_ERR_LIMIT)
        F("%s solver%d MISSED rc=%s lo=%llu hi=%llu n=%llu", tag, solver, nm(rc),
          (unsigned long long)lo, (unsigned long long)hi, (unsigned long long)g->order);
    else if (ex)
        F("%s solver%d LIMIT lo=%llu hi=%llu n=%llu", tag, solver, (unsigned long long)lo,
          (unsigned long long)hi, (unsigned long long)g->order);
    else if (!ex && rc == CA_OK)
        F("impossible");
}
static void run_group(ca_group *g, const char *tag, int iters)
{
    /* random base/target */
    for (int it = 0; it < iters; it++) {
        ca_elem base, tgt;
        uint64_t k;
        if (g->kind == CA_GROUP_ZP) {
            uint64_t w[4] = {1 + rnd() % (g->p - 1), 0, 0, 0};
            ca_group_encode(g, &base, w);
            if (g->cofactor > 1) ca_group_mul(g, &base, &base, g->cofactor, NULL);
        } else {
            ca_ec_random_point(g, &base, rnd() | 1);
            if (g->cofactor > 1) ca_group_mul(g, &base, &base, g->cofactor, NULL);
        }
        uint64_t n = g->order;
        k = rnd() % (n ? n : 1);
        ca_group_mul(g, &tgt, &base, k, NULL);
        uint64_t lo, hi;
        switch (it % 4) {
        case 0:
            lo = 0;
            hi = 0;
            break;
        case 1:
            lo = rnd() % n;
            hi = lo + rnd() % (n - lo);
            break;
        case 2:
            lo = k > 3 ? k - rnd() % 4 : 0;
            hi = k + rnd() % 6;
            if (hi >= n) hi = n - 1;
            break;
        default:
            lo = rnd() % n;
            hi = lo + rnd() % 300;
            if (hi >= n) hi = n - 1;
        }
        if (lo == 0 && hi == 0 && it % 4 != 0) hi = 1; /* avoid the (0,0)=whole group convention */
        if (hi < lo) hi = lo;
        for (int s = 0; s < 4; s++) {
            /* for the whole-group convention, exists() must scan [0,n-1] */
            uint64_t l = lo, h = hi;
            if (lo == 0 && hi == 0) { h = n - 1; }
            uint64_t x = 0;
            ca_stats st;
            memset(&st, 0, sizeof st);
            (void)x;
            (void)st;
            check_interval(g, &base, &tgt, l == 0 && h == n - 1 ? 0 : l, h, tag,
                           s); /* explicit full interval */
        }
    }
}
int main(int argc, char **argv)
{
    ca_rng_seed(&R, argc > 1 ? atoll(argv[1]) : 777);
    int mult = argc > 2 ? atoi(argv[2]) : 1;
    /* Zp subgroups */
    uint64_t ps[] = {7, 11, 13, 31, 101, 211, 1009, 10007, 65537, 1000003, 4294967311ULL};
    for (size_t i = 0; i < sizeof ps / 8; i++) {
        uint64_t p = ps[i];
        ca_factorization f;
        ca_factorize(p - 1, &f);
        for (unsigned d = 0; d <= f.count; d++) {
            uint64_t ord = (d == f.count) ? p - 1 : f.f[d].p;
            ca_group g;
            if (ca_group_zp_init(&g, p, ord) != CA_OK) {
                F("zp init");
                continue;
            }
            char tag[64];
            snprintf(tag, 64, "zp p=%llu n=%llu", (unsigned long long)p, (unsigned long long)ord);
            if (ord <= 300000) run_group(&g, tag, 40 * mult);
        }
    }
    /* EC small */
    uint64_t cp[] = {5, 7, 11, 13, 17, 101, 211, 1009, 10007};
    for (size_t i = 0; i < sizeof cp / 8; i++) {
        for (int c = 0; c < 6; c++) {
            uint64_t p = cp[i], a = rnd() % p, b = rnd() % p;
            uint64_t n;
            if (ca_ec_count_points(p, a, b, &n, NULL) != CA_OK) { continue; }
            ca_group g;
            if (ca_group_ec_init(&g, p, a, b, n) != CA_OK) continue;
            ca_factorization f;
            ca_factorize(n, &f);
            for (unsigned d = 0; d <= f.count; d++) {
                uint64_t ord = (d == f.count) ? n : f.f[d].p;
                ca_group gg;
                ca_group_ec_init(&gg, p, a, b, ord);
                gg.cofactor = n / ord; /* non-cyclic possible */
                /* only valid if group cyclic-ish: base = cofactor*random point has order dividing
                 * ord */
                char tag[96];
                snprintf(tag, 96, "ec p=%llu a=%llu b=%llu n=%llu sub=%llu", (unsigned long long)p,
                         (unsigned long long)a, (unsigned long long)b, (unsigned long long)n,
                         (unsigned long long)ord);
                run_group(&gg, tag, 20 * mult);
            }
        }
    }
    printf("done fails=%d\n", fails);
    return fails != 0;
}
