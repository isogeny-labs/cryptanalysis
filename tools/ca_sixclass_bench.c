/* Paired cold toy-curve comparison of the default GLV rho and the
 * experimental Curve Smash six-class DP walk. Both solve the same planted
 * targets; all setup is inside the elapsed time. */
#include "cryptanalysis/ca_curve.h"
#include "cryptanalysis/ca_sixclass.h"

#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static double now(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (double)t.tv_sec + (double)t.tv_nsec * 1e-9;
}

int main(int argc, char **argv)
{
    unsigned trials = 20;
    if (argc > 2) { fputs("usage: ca_sixclass_bench [trials]\n", stderr); return 2; }
    if (argc == 2) {
        char *end;
        unsigned long parsed = strtoul(argv[1], &end, 10);
        if (*end || parsed < 1 || parsed > 1000) return 2;
        trials = (unsigned)parsed;
    }
    uint64_t p, a, b, n;
    if (ca_curve_by_name("glv-j0-26", &p, &a, &b, &n) != CA_OK) return 2;
    ca_group g;
    if (ca_curve_group(&g, p, a, b, n, NULL) != CA_OK) return 2;
    ca_elem base;
    if (ca_group_find_generator(&g, &base, 17) != CA_OK) return 2;
    double default_s = 0, sixclass_s = 0;
    uint64_t default_ops = 0, class_visits = 0, dps = 0, escapes = 0;
    for (unsigned i = 0; i < trials; i++) {
        uint64_t secret = 1 + (UINT64_C(12345) + UINT64_C(7919) * i) % (n - 1);
        ca_elem target;
        ca_group_mul(&g, &target, &base, secret, NULL);
        uint64_t got = 0;
        ca_stats baseline = {0};
        double t0 = now();
        ca_status rc = ca_curve_solve(&g, &base, &target, 19 + i, &got, NULL, &baseline);
        default_s += now() - t0;
        if (rc != CA_OK || got != secret) return 3;
        default_ops += baseline.group_ops;
        ca_sixclass_stats candidate;
        t0 = now();
        rc = ca_sixclass_solve(&g, &base, &target, 19 + i, 32, 4,
                                10000, &got, &candidate);
        sixclass_s += now() - t0;
        if (rc != CA_OK || got != secret) return 4;
        class_visits += candidate.class_visits;
        dps += candidate.distinguished;
        escapes += candidate.short_cycle_escapes;
    }
    printf("{\"schema\":\"ca.sixclass.paired.v1\",\"curve\":\"glv-j0-26\","
           "\"trials\":%u,\"default_seconds\":%.9f,\"sixclass_seconds\":%.9f,"
           "\"default_group_ops\":%" PRIu64 ",\"sixclass_class_visits\":%" PRIu64 ","
           "\"sixclass_dps\":%" PRIu64 ",\"sixclass_escapes\":%" PRIu64 "}\n",
           trials, default_s, sixclass_s, default_ops, class_visits, dps, escapes);
    return 0;
}
