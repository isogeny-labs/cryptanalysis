/* dudect-style timing harness for ca_group_mul (src/group_ec.c: ca_ec_group_mul).
 * usage: ct_harness ROUTINE TEST N OUT.bin   (see README)
 * ROUTINE: prod | planted | const
 * TEST: lowhw | fixedrand | aa_fixed | aa_rand
 * Output: N records of (uint8 class, uint64 ns) after 2000 discarded warmups. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
#include "cryptanalysis/cryptanalysis.h"

static uint64_t s[2] = {0x9E3779B97F4A7C15ULL, 0xD1B54A32D192ED03ULL};
static inline uint64_t rnd(void) { /* xoroshiro128+ */
    uint64_t s0 = s[0], s1 = s[1], r = s0 + s1;
    s1 ^= s0; s[0] = ((s0 << 24) | (s0 >> 40)) ^ s1 ^ (s1 << 16);
    s[1] = (s1 << 37) | (s1 >> 27); return r;
}
static inline uint64_t now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC_RAW, &t); return (uint64_t)t.tv_sec*1000000000ULL + t.tv_nsec; }
static volatile uint64_t sink;
static ca_group G; static ca_elem BASE;
static const uint64_t K0 = 0x5A5A5A5A5A5A5A5BULL >> 1; /* fixed scalar for const/planted base cost */

static void routine(int which, uint64_t k) {
    ca_elem r;
    if (which == 0) { ca_group_mul(&G, &r, &BASE, k, NULL); }
    else if (which == 1) { /* planted leak: fixed-cost mul + one extra doubling iff k is odd */
        ca_group_mul(&G, &r, &BASE, K0, NULL);
        if (k & 1) ca_group_dbl(&G, &r, &r);
    } else { ca_group_mul(&G, &r, &BASE, K0, NULL); } /* const: ignores k */
    sink ^= r.w[0];
}
int main(int argc, char **argv) {
    if (argc < 5) return 2;
    int which = !strcmp(argv[1],"prod")?0:!strcmp(argv[1],"planted")?1:2;
    const char *test = argv[2]; long N = atol(argv[3]);
    const uint64_t p = 2305843009213693951ULL; /* 2^61-1 */
    if (ca_group_ec_init(&G, p, 1, 7, 0) != CA_OK) { fprintf(stderr,"init fail\n"); return 1; }
    for (uint64_t x = 2;; x++) { /* find base point; p = 3 mod 4 so sqrt = a^((p+1)/4) */
        uint64_t rhs = ca_addmod(ca_addmod(ca_mulmod(ca_mulmod(x,x,p),x,p), x, p), 7, p);
        uint64_t y = ca_powmod(rhs, (p+1)/4, p);
        if (ca_mulmod(y,y,p) == rhs) { uint64_t w[4]={x,y,0,0}; if (ca_group_encode(&G,&BASE,w)) break; }
    }
    uint64_t fixed = (rnd() | (1ULL<<62)) & ~(1ULL<<63);
    uint64_t lowk = 1ULL<<62;
    FILE *f = fopen(argv[4], "wb"); long W = 2000, tot = N + W;
    uint64_t *ks = malloc(sizeof(uint64_t)*tot); uint8_t *cl = malloc(tot);
    for (long i = 0; i < tot; i++) { /* inputs prepared before any timing */
        int c = rnd() >> 63; cl[i] = c;
        uint64_t rk = (rnd() | (1ULL<<62)) & ~(1ULL<<63);
        if (!strcmp(test,"lowhw")) ks[i] = c ? rk : (which==1 ? (lowk & ~1ULL) : lowk);
        else if (!strcmp(test,"fixedrand")) ks[i] = c ? rk : (which==1 ? (fixed & ~1ULL) : fixed);
        else if (!strcmp(test,"aa_fixed")) ks[i] = fixed;
        else ks[i] = rk; /* aa_rand */
    }
    /* planted: class0 is even fixed, class1 random (half odd) */
    for (long i = 0; i < tot; i++) {
        uint64_t t0 = now(); routine(which, ks[i]); uint64_t t1 = now();
        if (i >= W) { fwrite(&cl[i],1,1,f); uint64_t d = t1 - t0; fwrite(&d,8,1,f); }
    }
    fclose(f); return 0;
}
