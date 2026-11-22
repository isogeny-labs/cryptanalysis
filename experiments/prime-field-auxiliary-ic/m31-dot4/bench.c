#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#define P UINT64_C(2147483647)
#define N 4096
static uint32_t a[4 * N], b[4 * N], out[N];
static double ns(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return 1e9 * t.tv_sec + t.tv_nsec;
}
#define BODY(name, op)                                                                             \
    __attribute__((noinline)) static void name(void)                                               \
    {                                                                                              \
        for (unsigned i = 0; i < N; i++) {                                                         \
            uint64_t s = 0;                                                                        \
            for (unsigned j = 4 * i; j < 4 * i + 4; j++) {                                         \
                uint64_t v = (uint64_t)a[j] * b[j];                                                \
                s += op;                                                                           \
            }                                                                                      \
            out[i] = s % P;                                                                        \
        }                                                                                          \
    }
BODY(each, v % P)
BODY(once, v)
__attribute__((noinline)) static void fold(void)
{
    for (unsigned i = 0; i < N; i++) {
        uint64_t s = 0;
        for (unsigned j = 4 * i; j < 4 * i + 4; j++) s += (uint64_t)a[j] * b[j];
        s = (s & P) + (s >> 31);
        s = (s & P) + (s >> 31);
        out[i] = s >= P ? s - P : s;
    }
}
static int cmp(const void *a, const void *b)
{
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}
int main(void)
{
    uint64_t r = 431;
    for (unsigned i = 0; i < 4 * N; i++) {
        r = r * 6364136223846793005ULL + 1;
        a[i] = (r >> 32) % P;
        r = r * 6364136223846793005ULL + 1;
        b[i] = (r >> 32) % P;
    }
    for (int i = 0; i < 4; i++) a[i] = b[i] = P - 1;
    void (*f[])(void) = {each, once, fold};
    const char *labels[] = {"reduce each product", "reduce sum once", "fold sum twice"};
    double times[3][31];
    for (int k = 0; k < 3; k++) {
        f[k]();
        for (unsigned i = 0; i < N; i++) {
            __uint128_t s = 0;
            for (unsigned j = i * 4; j < i * 4 + 4; j++) s += (__uint128_t)a[j] * b[j];
            if (out[i] != (uint32_t)(s % P)) {
                fprintf(stderr, "%s failed at vector %u\n", labels[k], i);
                return 1;
            }
        }
    }
    for (int t = 0; t < 34; t++) {
        for (int h = 0; h < 3; h++) {
            int k = (h + t) % 3;
            double st = ns();
            for (int j = 0; j < 512; j++) {
                f[k]();
                __asm__ volatile("" ::: "memory");
            }
            double end = ns();
            if (t >= 3) times[k][t - 3] = (end - st) / (512 * N);
        }
    }
    for (int k = 0; k < 3; k++) {
        qsort(times[k], 31, sizeof(double), cmp);
        printf("%s q1/median/q3 ns/dot %.3f %.3f %.3f\n", labels[k], times[k][7], times[k][15],
               times[k][23]);
    }
    return 0;
}
