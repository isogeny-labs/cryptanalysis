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
    void (*f[])(void) = {canonical, pre, in, carry, folded};
    const char *labels[] = {"two reductions", "precentered", "center on input", "carry correction", "deferred fold"};
    double ts[5][40];
    for (int k = 0; k < 5; k++) {
        f[k]();
        for (int i = 0; i < N; i++)
            if (o[i] != ref[i]) return 1;
    }
    // Cycle through both orientations to balance position and reverse the traversal order.
    for (int t = 0; t < 50; t++)
        for (int j = 0; j < 5; j++) {
            int k = (t + (t / 5 % 2 ? 4 - j : j)) % 5;
            uint64_t st = ns();
            for (int n = 0; n < PASSES; n++) {
                f[k]();
                __asm__ volatile("" ::: "memory");
            }
            double v = (double)(ns() - st) / (N * PASSES);
            if (t >= 10) ts[k][t - 10] = v;
        }
    for (int k = 0; k < 5; k++) {
        qsort(ts[k], 40, sizeof(double), cmp);
        printf("%s: %.3f ns/dot\n", labels[k], (ts[k][19] + ts[k][20]) / 2);
    }
    return 0;
}
