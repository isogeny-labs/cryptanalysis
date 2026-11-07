/* Wall-time panel for the GLV table rule (experiments/glv-table-walltime-above40-20261103).
 *
 *   bench_glv_panel --fixture FIXTURE   lines "p a b r k" -> lines "p a b r target_x target_y"
 *   bench_glv_panel PANEL SEED          time ca_curve_solve on every panel target
 *
 * The fixture mode builds each public target k*G outside any timer; the scalar
 * never reaches the timed mode.  The timed mode sets every group up first, then
 * starts the clock, solves each target with ca_curve_solve, and replays the
 * answer (found*G == target).  online_ms covers exactly those solves and
 * replays.  It prints one line: the panel's target count, its first target, the
 * total operation count, a 64-bit FNV-1a hash of the recovered scalars in panel
 * order (result), and verified=1 only if every replay matched. */
#define _POSIX_C_SOURCE 200809L
#include "cryptanalysis/ca_curve.h"
#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAX_TARGETS 4096

static double clock_ms(clockid_t id)
{
    struct timespec t;
    clock_gettime(id, &t);
    return 1000.0 * (double)t.tv_sec + (double)t.tv_nsec / 1000000.0;
}

static int setup(ca_group *g, ca_elem *gen, uint64_t p, uint64_t a, uint64_t b, uint64_t r)
{
    ca_curve_info info;
    if (ca_curve_group(g, p, a, b, r, &info) != CA_OK) return 0;
    if (info.endo == CA_CURVE_ENDO_NONE) return 0;
    return ca_group_find_generator(g, gen, 1) == CA_OK;
}

static int fixture(const char *path)
{
    FILE *f = fopen(path, "r");
    if (!f) return 2;
    uint64_t p, a, b, r, k;
    while (fscanf(f, "%" SCNu64 " %" SCNu64 " %" SCNu64 " %" SCNu64 " %" SCNu64, &p, &a, &b, &r, &k) == 5) {
        ca_group g;
        ca_elem gen, t;
        if (!setup(&g, &gen, p, a, b, r) || k == 0 || k >= r) return 3;
        ca_group_mul(&g, &t, &gen, k, NULL);
        uint64_t w[4];
        ca_group_decode(&g, w, &t);
        printf("%" PRIu64 " %" PRIu64 " %" PRIu64 " %" PRIu64 " %" PRIu64 " %" PRIu64 "\n", p, a, b, r, w[0], w[1]);
    }
    fclose(f);
    return 0;
}

static ca_group G[MAX_TARGETS];
static ca_elem GEN[MAX_TARGETS], TGT[MAX_TARGETS];
static uint64_t TX[MAX_TARGETS], TY[MAX_TARGETS];

int main(int argc, char **argv)
{
    if (argc == 3 && !strcmp(argv[1], "--fixture")) return fixture(argv[2]);
    if (argc != 3) return 5;
    char *end = NULL;
    errno = 0;
    uint64_t seed = strtoull(argv[2], &end, 10);
    if (errno || !end || *end) return 5;
    FILE *f = fopen(argv[1], "r");
    if (!f) return 2;
    size_t n = 0;
    uint64_t p, a, b, r, x, y;
    while (fscanf(f, "%" SCNu64 " %" SCNu64 " %" SCNu64 " %" SCNu64 " %" SCNu64 " %" SCNu64, &p, &a, &b, &r, &x, &y) == 6) {
        if (n == MAX_TARGETS || !setup(&G[n], &GEN[n], p, a, b, r)) return 3;
        uint64_t w[4] = {x, y, 0, 0};
        ca_elem check;
        if (!ca_group_encode(&G[n], &TGT[n], w) || ca_group_is_identity(&G[n], &TGT[n])) return 6;
        ca_group_mul(&G[n], &check, &TGT[n], r, NULL);
        if (!ca_group_is_identity(&G[n], &check)) return 6;
        TX[n] = x;
        TY[n] = y;
        n++;
    }
    fclose(f);
    if (n == 0) return 3;

    uint64_t hash = UINT64_C(0xcbf29ce484222325), ops = 0;
    int verified = 1;
    double cpu0 = clock_ms(CLOCK_PROCESS_CPUTIME_ID), wall0 = clock_ms(CLOCK_MONOTONIC);
    for (size_t i = 0; i < n; i++) {
        ca_stats st = {0};
        uint64_t found = 0;
        ca_status rc = ca_curve_solve(&G[i], &GEN[i], &TGT[i], seed + i, &found, NULL, &st);
        ca_elem replay;
        ca_group_mul(&G[i], &replay, &GEN[i], found, NULL);
        verified &= rc == CA_OK && ca_group_equal(&G[i], &replay, &TGT[i]);
        ops += st.group_ops;
        for (int byte = 0; byte < 8; byte++) {
            hash ^= (found >> (8 * byte)) & 0xff;
            hash *= UINT64_C(0x100000001b3);
        }
    }
    double online_ms = clock_ms(CLOCK_MONOTONIC) - wall0, cpu_ms = clock_ms(CLOCK_PROCESS_CPUTIME_ID) - cpu0;
    printf("targets=%zu first_x=%" PRIu64 " first_y=%" PRIu64 " seed=%" PRIu64 " ops=%" PRIu64
           " online_ms=%.6f cpu_ms=%.6f result=%016" PRIx64 " verified=%d\n",
           n, TX[0], TY[0], seed, ops, online_ms, cpu_ms, hash, verified);
    return verified ? 0 : 4;
}
