#include "cryptanalysis/cryptanalysis.h"
#include "ca_internal.h"
#include <stdio.h>
#include <math.h>
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
static int ok(const ca_group *g, const ca_elem *b, const ca_elem *t, uint64_t x)
{
    ca_elem c;
    ca_group_mul(g, &c, b, x, NULL);
    return ca_group_equal(g, &c, t);
}
int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    ca_rng_seed(&R, argc > 1 ? atoll(argv[1]) : 3);
    for (int gi = 0; gi < 4; gi++) {
        ca_group g;
        ca_elem base;
        if (gi == 0) {
            ca_group_zp_init(&g, 2147483783ULL, 0);
            uint64_t w[4] = {ca_primitive_root(2147483783ULL), 0, 0, 0};
            ca_group_encode(&g, &base, w);
        } else if (gi == 1) {
            ca_group_zp_init(&g, 18446744073709551557ULL, 0);
            uint64_t w[4] = {ca_primitive_root(18446744073709551557ULL), 0, 0, 0};
            ca_group_encode(&g, &base, w);
        } else {
            uint64_t p, a, b, n;
            ca_curve_by_name(gi == 2 ? "generic-26" : "glv-j0-32", &p, &a, &b, &n);
            ca_group_ec_init(&g, p, a, b, n);
            ca_group_find_generator(&g, &base, 5);
        }
        uint64_t n = g.order;
        for (int it = 0; it < 60; it++) {
            uint64_t width = 1 + (rnd() % (1ULL << (8 + rnd() % 14)));
            uint64_t lo = rnd() % (n - width);
            uint64_t x = lo + rnd() % width;
            ca_elem t;
            ca_group_mul(&g, &t, &base, x, NULL);
            uint64_t got;
            ca_stats st = {0};
            ca_status rc;
            ca_kangaroo_params kp;
            ca_kangaroo_params_default(&kp);
            kp.seed = rnd() | 1;
            kp.max_ops = 50000000;
            switch (rnd() % 5) {
            case 0: kp.herd_size = 1 + rnd() % 4; break;
            case 1: kp.jumps = 1 + rnd() % 20; break;
            case 2: kp.dp_bits = rnd() % 10; break;
            case 3:
                kp.herd_size = 1;
                kp.jumps = 1 + rnd() % 3;
                kp.dp_bits = rnd() % 4;
                break;
            default: break;
            }
            rc = ca_kangaroo_solve(&g, &base, &t, lo, lo + width - 1, &kp, &got, &st);
            if (rc != CA_OK || !ok(&g, &base, &t, got) || got < lo || got > lo + width - 1)
                F("kang gi=%d w=%llu rc=%s herd=%u j=%u dp=%d", gi, (unsigned long long)width,
                  ca_status_string(rc), kp.herd_size, kp.jumps, kp.dp_bits);
            ca_grumpy_params gp;
            ca_grumpy_params_default(&gp);
            if (it % 3 == 0) gp.m = 1 + rnd() % (2 * (uint64_t)sqrt((double)width) + 2);
            if (it % 3 == 1) gp.alpha = 0.1 + (rnd() % 30) / 10.0;
            gp.max_ops = 50000000;
            memset(&st, 0, sizeof st);
            rc = ca_grumpy_solve(&g, &base, &t, lo, lo + width - 1, &gp, &got, &st);
            if (rc != CA_OK || !ok(&g, &base, &t, got) || got < lo || got > lo + width - 1)
                F("grumpy gi=%d w=%llu rc=%s m=%llu alpha=%g", gi, (unsigned long long)width,
                  ca_status_string(rc), (unsigned long long)gp.m, gp.alpha);
            ca_bsgs_params bp;
            ca_bsgs_params_default(&bp);
            if (it % 2) bp.table_size = 1 + rnd() % (width + 5);
            memset(&st, 0, sizeof st);
            rc = ca_bsgs_solve(&g, &base, &t, lo, lo + width - 1, &bp, &got, &st);
            if (rc != CA_OK || !ok(&g, &base, &t, got) || got < lo || got > lo + width - 1)
                F("bsgs gi=%d w=%llu rc=%s ts=%llu", gi, (unsigned long long)width,
                  ca_status_string(rc), (unsigned long long)bp.table_size);
            /* bsgs table reuse */
            ca_bsgs_table *tb;
            uint64_t m = 1 + rnd() % 1000;
            if (ca_bsgs_table_new(&g, &base, m, &tb) == CA_OK) {
                rc = ca_bsgs_table_solve(tb, &t, lo, lo + width - 1, &got, NULL);
                if (rc != CA_OK || !ok(&g, &base, &t, got)) F("bsgs table gi=%d", gi);
                ca_bsgs_table_free(tb);
            } else
                F("table new");
            /* precomp */
            if (width > 200 && gi != 1 && it % 6 == 0) {
                ca_precomp_params pp;
                ca_precomp_params_default(&pp);
                pp.seed = rnd() | 1;
                pp.threads = 1 + rnd() % 3;
                memset(&st, 0, sizeof st);
                rc = ca_precomp_solve(&g, &base, &t, &pp, &got, &st);
                if (rc != CA_OK || !ok(&g, &base, &t, got))
                    F("precomp gi=%d rc=%s", gi, ca_status_string(rc));
            }
        }
    }
    printf("done fails=%d\n", fails);
    return fails != 0;
}
