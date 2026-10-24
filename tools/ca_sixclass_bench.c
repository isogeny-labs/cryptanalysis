/* Bounded A/B/A toy-curve comparison. Each target gets default, six-class,
 * default in that order. Setup, solve, and answer check are all timed. Raw
 * rows retain drift and failures; no production cost is inferred. */
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
    double default_before_s = 0, default_after_s = 0, sixclass_s = 0;
    uint64_t default_ops = 0, class_visits = 0, dps = 0, escapes = 0;
    printf("{\"schema\":\"ca.sixclass.paired.v2\",\"curve\":\"glv-j0-26\","
           "\"trials\":%u,\"order\":\"default/sixclass/default\",\"rows\":[", trials);
    for (unsigned i = 0; i < trials; i++) {
        uint64_t secret = 1 + (UINT64_C(12345) + UINT64_C(7919) * i) % (n - 1);
        ca_elem target;
        ca_group_mul(&g, &target, &base, secret, NULL);
        uint64_t got = 0;
        ca_stats baseline = {0}, repeat = {0};
        double t0 = now();
        ca_status rc = ca_curve_solve(&g, &base, &target, 19 + i, &got, NULL, &baseline);
        double before = now() - t0;
        default_before_s += before;
        if (rc != CA_OK || got != secret) {
            printf("],\"failure\":{\"index\":%u,\"arm\":\"default_before\","
                   "\"status\":%d,\"answer_valid\":%s}}\n",
                   i, (int)rc, got == secret ? "true" : "false");
            return 3;
        }
        default_ops += baseline.group_ops;
        ca_sixclass_stats candidate;
        t0 = now();
        rc = ca_sixclass_solve(&g, &base, &target, 19 + i, 32, 4,
                                10000, &got, &candidate);
        double middle = now() - t0;
        sixclass_s += middle;
        if (rc != CA_OK || got != secret) {
            printf("],\"failure\":{\"index\":%u,\"arm\":\"sixclass\","
                   "\"status\":%d,\"answer_valid\":%s}}\n",
                   i, (int)rc, got == secret ? "true" : "false");
            return 4;
        }
        class_visits += candidate.class_visits;
        dps += candidate.distinguished;
        escapes += candidate.short_cycle_escapes;
        t0 = now();
        rc = ca_curve_solve(&g, &base, &target, 19 + i, &got, NULL, &repeat);
        double after = now() - t0;
        default_after_s += after;
        if (rc != CA_OK || got != secret || repeat.group_ops != baseline.group_ops) {
            printf("],\"failure\":{\"index\":%u,\"arm\":\"default_after\","
                   "\"status\":%d,\"answer_valid\":%s,\"aa_work_equal\":%s}}\n",
                   i, (int)rc, got == secret ? "true" : "false",
                   repeat.group_ops == baseline.group_ops ? "true" : "false");
            return 5;
        }
        printf("%s{\"index\":%u,\"seed\":%u,\"default_before_seconds\":%.9f,"
               "\"sixclass_seconds\":%.9f,\"default_after_seconds\":%.9f,"
               "\"default_group_ops\":%" PRIu64 ",\"sixclass_class_visits\":%" PRIu64 ","
               "\"sixclass_dps\":%" PRIu64 ",\"sixclass_escapes\":%" PRIu64 "}",
               i ? "," : "", i, 19 + i, before, middle, after,
               baseline.group_ops, candidate.class_visits,
               candidate.distinguished, candidate.short_cycle_escapes);
    }
    printf("],\"default_before_seconds\":%.9f,\"default_after_seconds\":%.9f,"
           "\"sixclass_seconds\":%.9f,"
           "\"default_group_ops\":%" PRIu64 ",\"sixclass_class_visits\":%" PRIu64 ","
           "\"sixclass_dps\":%" PRIu64 ",\"sixclass_escapes\":%" PRIu64 ","
           "\"scope\":\"bounded toy curve; no production instruction cost\"}\n",
           default_before_s, default_after_s, sixclass_s,
           default_ops, class_visits, dps, escapes);
    return 0;
}
