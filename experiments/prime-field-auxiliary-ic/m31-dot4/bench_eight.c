#if defined(__aarch64__)
#include <arm_neon.h>
#endif
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#ifndef N
#define N 2048
#endif
#define PASSES ((1048576 + N - 1) / N)
_Static_assert(N >= 8 && N <= 1048576, "panel size must include all boundary rows and fit one timing sample");
#define P UINT64_C(2147483647)
#define M 1073741823
static uint32_t a[N][8], b[N][8], o[N], ref[N];
static int32_t x[N][8], y[N][8];
static int32_t center(uint32_t v) { return (int32_t)v - (v > M ? (int32_t)P : 0); }
static uint32_t reduce(int64_t v) { return ((uint64_t)v + (P << 32)) % P; }
__attribute__((noinline)) static void canonical(void)
{
    for (int i = 0; i < N; i++) {
        uint64_t s = 0, t = 0;
        for (int j = 0; j < 4; j++) {
            s += (uint64_t)a[i][j] * b[i][j];
            t += (uint64_t)a[i][4 + j] * b[i][4 + j];
        }
        s = s % P + t % P;
        o[i] = s >= P ? s - P : s;
    }
}
__attribute__((noinline)) static void carry(void)
{
    for (int i = 0; i < N; i++) {
        uint64_t s = 0, t = 0;
        for (int j = 0; j < 4; j++) {
            s += (uint64_t)a[i][j] * b[i][j];
            t += (uint64_t)a[i][4 + j] * b[i][4 + j];
        }
        uint64_t r = s + t;
        o[i] = (r + 4 * (r < s)) % P;
    }
}
__attribute__((noinline)) static void pre(void)
{
    for (int i = 0; i < N; i++) {
        int64_t s = 0;
        for (int j = 0; j < 8; j++) s += (int64_t)x[i][j] * y[i][j];
        o[i] = reduce(s);
    }
}
__attribute__((noinline)) static void in(void)
{
    for (int i = 0; i < N; i++) {
        int64_t s = 0;
        for (int j = 0; j < 8; j++) s += (int64_t)center(a[i][j]) * center(b[i][j]);
        o[i] = reduce(s);
    }
}
__attribute__((noinline)) static void folded(void)
{
    for (int i = 0; i < N; i++) {
        uint64_t s = 0, t = 0;
        for (int j = 0; j < 4; j++) {
            s += (uint64_t)a[i][j] * b[i][j];
            t += (uint64_t)a[i][4 + j] * b[i][4 + j];
        }
        uint64_t u = (s & P) + (s >> 31) + (t & P) + (t >> 31);
        u = (u & P) + (u >> 31);
        o[i] = u >= P ? u - P : u;
    }
}
#if defined(__aarch64__)
// Each lane accumulates four canonical products, whose sum fits in 64 bits.
static inline uint64x2_t folded_lanes(const uint32_t *left, const uint32_t *right)
{
    uint32x4_t a0 = vld1q_u32(left), a1 = vld1q_u32(left + 4);
    uint32x4_t b0 = vld1q_u32(right), b1 = vld1q_u32(right + 4);
    uint64x2_t acc = vmull_u32(vget_low_u32(a0), vget_low_u32(b0));
    acc = vmlal_high_u32(acc, a0, b0);
    acc = vmlal_u32(acc, vget_low_u32(a1), vget_low_u32(b1));
    acc = vmlal_high_u32(acc, a1, b1);
    return vsraq_n_u64(vandq_u64(acc, vdupq_n_u64(P)), acc, 31);
}

__attribute__((noinline)) static void neon_rows(void)
{
    int i = 0;
    for (; i + 1 < N; i += 2) {
        uint64x2_t sums = vpaddq_u64(folded_lanes(a[i], b[i]),
                                     folded_lanes(a[i+1], b[i+1]));
        uint32x2_t v = vmovn_u64(vsraq_n_u64(vandq_u64(sums, vdupq_n_u64(P)), sums, 31));
        uint32x2_t p = vdup_n_u32(P);
        vst1_u32(o + i, vsub_u32(v, vand_u32(vcge_u32(v, p), p)));
    }
    if (i < N) {
        uint64_t u = vaddvq_u64(folded_lanes(a[i], b[i]));
        u = (u & P) + (u >> 31);
        o[i] = u >= P ? u - P : u;
    }
}
#endif
static uint64_t ns(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (uint64_t)t.tv_sec * 1000000000 + t.tv_nsec;
}
static int cmp(const void *a, const void *b)
{
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}
int main(void)
{
    uint64_t r = 0x1691;
    for (int i = 0; i < N; i++) {
        __uint128_t s = 0;
        for (int j = 0; j < 8; j++) {
            r = r * 6364136223846793005ULL + 1;
            uint32_t u = (r >> 32) % P;
            r = r * 6364136223846793005ULL + 1;
            uint32_t v = (r >> 32) % P;
            if (i < 5) {
                uint32_t e[] = {M, M + 1, P - 1, 0, M};
                u = e[i];
                v = i == 4 ? M + 1 : u;
            }
            // Construct exact total sums 2^64 - 1, 2^64, and 2^64 + 1.
            if (i >= 5 && i <= 7) {
                u = j < 5 ? P - 1 : j == 5 ? (uint32_t)(10 + i) : 0;
                v = j < 4 ? P - 1 : j == 4 ? 16 : 1;
            }
            a[i][j] = u;
            b[i][j] = v;
            x[i][j] = center(u);
            y[i][j] = center(v);
            s += (__uint128_t)u * v;
        }
        if (i >= 5 && i <= 7 && s != (((__uint128_t)1 << 64) - 1 + (i - 5))) return 1;
        ref[i] = s % P;
    }
    void (*f[])(void) = {canonical, pre, in, carry, folded
#if defined(__aarch64__)
        , neon_rows
#endif
    };
    const char *labels[] = {"two reductions", "precentered", "center on input", "carry correction", "deferred fold"
#if defined(__aarch64__)
        , "NEON row pair"
#endif
    };
    enum { arms = sizeof(f) / sizeof(f[0]), samples = 8 * arms, warmup = 2 * arms };
    _Static_assert(sizeof(labels) / sizeof(labels[0]) == arms, "missing benchmark label");
    double ts[arms][samples];
    for (int k = 0; k < arms; k++) {
        f[k]();
        for (int i = 0; i < N; i++)
            if (o[i] != ref[i]) return 1;
    }
    // Cycle through both orientations to balance position and reverse the traversal order.
    for (int t = 0; t < samples + warmup; t++)
        for (int j = 0; j < arms; j++) {
            int k = (t + (t / arms % 2 ? arms - 1 - j : j)) % arms;
            uint64_t st = ns();
            for (int n = 0; n < PASSES; n++) {
                f[k]();
                __asm__ volatile("" ::: "memory");
            }
            double v = (double)(ns() - st) / (N * PASSES);
            if (t >= warmup) ts[k][t - warmup] = v;
        }
    for (int k = 0; k < arms; k++) {
        qsort(ts[k], samples, sizeof(double), cmp);
        printf("%s: %.3f ns/dot\n", labels[k], (ts[k][samples/2 - 1] + ts[k][samples/2]) / 2);
    }
    return 0;
}
