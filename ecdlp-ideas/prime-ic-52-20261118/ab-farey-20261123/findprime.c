/* findprime.c — first primes p <= start, p = 3 mod 4, with #E(F_p) prime for
 * E: y^2 = x^3 + 7.  Prints "p n" per hit.  Toy-scale helper only. */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
typedef unsigned __int128 u128;
static uint64_t P;
static inline uint64_t mm(uint64_t a, uint64_t b) { return (uint64_t)((u128)a * b % P); }
static uint64_t mpow(uint64_t a, uint64_t e) {
    uint64_t r = 1; while (e) { if (e & 1) r = mm(r, a); a = mm(a, a); e >>= 1; } return r;
}
static int isp(uint64_t n) {
    if (n < 2) return 0;
    if (!(n & 1)) return n == 2;
    for (uint64_t d = 3; d * d <= n; d += 2) if (n % d == 0) return 0;
    return 1;
}
int main(int argc, char **argv) {
    uint64_t start = strtoull(argv[1], 0, 10);
    int want = atoi(argv[2]);
    int found = 0;
    int64_t lo = (int64_t)start - 4000000; if (lo < 5) lo = 5;
    for (int64_t p = (int64_t)((start % 4 == 3) ? start : start - 1); p > lo && found < want; p -= 4) {
        P = p;
        if (!isp(p)) continue;
        long long sum = 0;
        for (uint64_t x = 0; x < p; x++) {
            uint64_t rhs = (mm(x, mm(x, x)) + 7) % p;
            if (rhs == 0) continue;
            sum += (mpow(rhs, (p - 1) / 2) == 1) ? 1 : -1;
        }
        long long n = (long long)p + 1 + sum;
        if (isp((uint64_t)n)) {
            printf("%llu %lld\n", (unsigned long long)p, n);
            fflush(stdout);
            found++;
        }
    }
    return 0;
}
