// ARM64 M31 lift-label comparison on fresh coordinates, including the cubic RHS.
#include "lift_table.h"
#include <arm_neon.h>
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

enum { N = 1 << 20 };
static uint32_t coords[N], reference[N], output[N];

static uint64_t ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000 + ts.tv_nsec;
}

static uint32_t rhs(uint32_t x) {
    uint64_t xx = (uint64_t)x * x % P;
    return (xx * x + 2ULL * x + 14) % P;
}

static uint32x4_t square(uint32x4_t x) {
    int32x4_t s = vreinterpretq_s32_u32(x);
    uint32x4_t high = vreinterpretq_u32_s32(vqdmulhq_s32(s, s));
    uint32x4_t p = vdupq_n_u32(P);
    uint32x4_t sum = vaddq_u32(high, vandq_u32(vmulq_u32(x, x), p));
    return vsubq_u32(sum, vandq_u32(vcgeq_u32(sum, p), p));
}

__attribute__((noinline)) static void direct(uint32_t *out) {
    for (unsigned i = 0; i < N; i += 32) {
        uint32_t values[32];
        uint32x4_t y[8];
        for (unsigned j = 0; j < 32; ++j) values[j] = rhs(coords[i+j]);
        for (unsigned k = 0; k < 8; ++k) y[k] = vld1q_u32(values+4*k);
        for (unsigned j = 0; j < 30; ++j)
            for (unsigned k = 0; k < 8; ++k) y[k] = square(y[k]);
        for (unsigned k = 0; k < 8; ++k)
            vst1q_u32(out+i+4*k, vshrq_n_u32(vceqq_u32(y[k], vld1q_u32(values+4*k)),31));
    }
}

__attribute__((noinline)) static void lookup(const uint64_t *table, uint32_t *out) {
    for (unsigned i = 0; i < N; ++i) out[i] = lifts(coords[i], table);
}

int main(int argc, char **argv) {
    if (argc != 2) return 1;
    uint32_t state = strtoul(argv[1], NULL, 10);
    uint64_t start = ns();
    uint64_t *table = square_table();
    uint64_t setup = ns() - start;
    if (!table) return 1;
    for (unsigned block = 0; block < 12; ++block) {
        for (unsigned i = 0; i < N; ++i) {
            do { state = (1103515245u * state + 12345u) & P; } while (state == P);
            coords[i] = state;
        }
        uint64_t times[2];
        for (unsigned j = 0; j < 2; ++j) {
            unsigned arm = (block + j) % 2;
            start = ns();
            if (arm) lookup(table, output); else direct(reference);
            times[arm] = ns() - start;
        }
        if (memcmp(reference, output, sizeof(output)) != 0) return 1;
        printf("%s,%u,%d,%" PRIu64 ",%" PRIu64 ",%" PRIu64 "\n",
               argv[1], block, N, setup, times[0], times[1]);
    }
    free(table);
}
