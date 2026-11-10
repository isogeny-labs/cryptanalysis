#include "cryptanalysis/ca_modarith.h"
#include "ca_internal.h"
#include "test_util.h"

/* The extended Euclid ca_invmod used before 2026-11-10 (64-bit division,
 * signed 128-bit coefficients), kept as the reference for the binary xgcd
 * that replaced it for odd moduli: the inverse is unique, and the zero /
 * non-invertible results must match exactly. */
static uint64_t invmod_reference(uint64_t a, uint64_t m)
{
    if (m == 0) return 0;
    a %= m;
    if (a == 0) return 0;
    ca_i128 t = 0, newt = 1;
    uint64_t r = m, newr = a;
    while (newr) {
        uint64_t q = r / newr;
        ca_i128 tmp = t - (ca_i128)q * newt;
        t = newt;
        newt = tmp;
        uint64_t tr = r - q * newr;
        r = newr;
        newr = tr;
    }
    if (r != 1) return 0;
    if (t < 0) t += (ca_i128)m;
    return (uint64_t)t;
}

static void invmod_vs_reference(void)
{
    static const uint64_t edge[] = {0,
                                    1,
                                    2,
                                    3,
                                    4,
                                    5,
                                    7,
                                    8,
                                    9,
                                    15,
                                    16,
                                    17,
                                    65537,
                                    (1ULL << 32) - 1,
                                    1ULL << 32,
                                    (1ULL << 32) + 1,
                                    (1ULL << 61) - 1,
                                    (1ULL << 63) - 1,
                                    1ULL << 63,
                                    (1ULL << 63) + 1,
                                    18446744073709551557ULL,
                                    UINT64_MAX - 1,
                                    UINT64_MAX};
    const size_t ne = sizeof(edge) / sizeof(edge[0]);
    for (size_t i = 0; i < ne; i++)
        for (size_t j = 0; j < ne; j++) {
            CHECK_EQ_U64(ca_invmod(edge[i], edge[j]), invmod_reference(edge[i], edge[j]));
            CHECK_EQ_U64(ca_invmod(edge[i] + 1, edge[j]), invmod_reference(edge[i] + 1, edge[j]));
            CHECK_EQ_U64(ca_invmod(edge[j] - 1, edge[j]), invmod_reference(edge[j] - 1, edge[j]));
        }
    for (uint64_t m = 0; m < 300; m++)
        for (uint64_t a = 0; a <= 2 * m + 1; a++)
            CHECK_EQ_U64(ca_invmod(a, m), invmod_reference(a, m));
    /* random moduli of every bit length, odd and even, reduced and unreduced
     * a, and a sharing a small factor with m (non-invertible) */
    ca_rng rng;
    ca_rng_seed(&rng, 0x1a7e5);
    for (int bits = 2; bits <= 64; bits++) {
        for (int t = 0; t < 4000; t++) {
            uint64_t m = ca_rng_next(&rng);
            if (bits < 64) m &= (1ULL << bits) - 1;
            m |= 1ULL << (bits - 1);
            if (t & 1) m |= 1;
            uint64_t a = ca_rng_next(&rng);
            if (t % 3 == 1) a %= m;
            if (t % 3 == 2) a = (a % m) / 3 * 3;
            uint64_t got = ca_invmod(a, m), want = invmod_reference(a, m);
            CHECK_EQ_U64(got, want);
            if (got) CHECK_EQ_U64(ca_mulmod(a % m, got, m), 1);
        }
    }
}

int main(void)
{
    invmod_vs_reference();
    /* powmod / invmod against brute force on small moduli */
    for (uint64_t m = 3; m < 200; m += 2) {
        for (uint64_t a = 1; a < m; a++) {
            uint64_t inv = ca_invmod(a, m);
            if (ca_gcd(a, m) == 1) CHECK_EQ_U64(ca_mulmod(a, inv, m), 1);
            else CHECK_EQ_U64(inv, 0);
        }
    }
    /* large modulus near 2^64 */
    uint64_t p = 18446744073709551557ULL; /* largest 64-bit prime */
    CHECK(ca_is_prime(p));
    CHECK(!ca_is_prime(p - 2));
    CHECK(ca_is_prime(2) && ca_is_prime(3) && !ca_is_prime(1) && !ca_is_prime(0));
    CHECK(!ca_is_prime(3215031751ULL)); /* strong pseudoprime to bases 2,3,5,7 */
    CHECK(!ca_is_prime(341550071728321ULL)); /* psp to first 7 bases */
    for (uint64_t a = 2; a < 50; a++) {
        CHECK_EQ_U64(ca_mulmod(a, ca_invmod(a, p), p), 1);
        CHECK_EQ_U64(ca_powmod(a, p - 1, p), 1);
    }
    /* Montgomery vs plain */
    ca_mont mo;
    CHECK(ca_mont_init(&mo, p));
    uint64_t x = 0x123456789abcdef0ULL, y = 0xfedcba9876543210ULL;
    uint64_t xm = ca_mont_to(&mo, x), ym = ca_mont_to(&mo, y);
    CHECK_EQ_U64(ca_mont_from(&mo, ca_mont_mul(&mo, xm, ym)), ca_mulmod(x, y, p));
    CHECK_EQ_U64(ca_mont_from(&mo, ca_mont_pow(&mo, xm, 12345)), ca_powmod(x, 12345, p));
    CHECK_EQ_U64(ca_mont_from(&mo, ca_mont_inv(&mo, xm)), ca_invmod(x, p));
    CHECK_EQ_U64(ca_mont_from(&mo, xm), x);
    CHECK_EQ_U64(ca_mont_from(&mo, mo.r1), 1);
    /* random Montgomery checks on several moduli */
    ca_rng rng;
    ca_rng_seed(&rng, 42);
    uint64_t mods[] = {1000003, 4294967311ULL, 1099511627791ULL, 9223372036854775837ULL, p};
    for (size_t i = 0; i < sizeof(mods) / sizeof(mods[0]); i++) {
        ca_mont m2;
        CHECK(ca_mont_init(&m2, mods[i]));
        for (int k = 0; k < 2000; k++) {
            uint64_t a = ca_rng_below(&rng, mods[i]), b = ca_rng_below(&rng, mods[i]);
            uint64_t am = ca_mont_to(&m2, a), bm = ca_mont_to(&m2, b);
            CHECK_EQ_U64(ca_mont_from(&m2, ca_mont_mul(&m2, am, bm)), ca_mulmod(a, b, mods[i]));
            if (a) CHECK_EQ_U64(ca_mont_from(&m2, ca_mont_inv(&m2, am)), ca_invmod(a, mods[i]));
        }
    }
    /* REDC against the addition form it replaced, on every modulus class
     * (tiny, 32-bit, 63-bit, the largest 64-bit prime) and on t at the
     * edges of its domain t < p * 2^64: 0, 1, p*2^64 - 1, multiples of
     * 2^64, and random products of two residues. */
    {
        uint64_t rmods[] = {3,
                            5,
                            1000003,
                            4294967311ULL,
                            9223372036854775837ULL,
                            18446744073709551557ULL,
                            18446744073709551615ULL};
        for (size_t i = 0; i < sizeof(rmods) / sizeof(rmods[0]); i++) {
            ca_mont m3;
            CHECK(ca_mont_init(&m3, rmods[i]));
            const uint64_t q = rmods[i];
            ca_u128 edge[] = {0,
                              1,
                              ((ca_u128)q << 64) - 1,
                              (ca_u128)(q - 1) << 64,
                              ((ca_u128)(q - 1) << 64) | UINT64_MAX,
                              (ca_u128)(q - 1) * (q - 1)};
            for (int k = 0; k < 20000 + 6; k++) {
                ca_u128 t;
                if (k < 6) {
                    t = edge[k];
                } else {
                    uint64_t a = ca_rng_below(&rng, q), b = ca_rng_below(&rng, q);
                    t = k & 1 ? (ca_u128)a * b
                              : ((ca_u128)ca_rng_below(&rng, q) << 64) | ca_rng_next(&rng);
                }
                uint64_t u = (uint64_t)t * m3.pinv;
                ca_u128 sum = t + (ca_u128)u * q;
                uint64_t want = (uint64_t)(sum >> 64);
                if (sum < t) want += (uint64_t)0 - q;
                if (want >= q) want -= q;
                CHECK_EQ_U64(ca_mont_redc(&m3, t), want);
            }
        }
    }
    /* ca_powmod (Montgomery for odd moduli and long exponents) against the
     * plain square-and-multiply ladder, and ca_is_prime against trial
     * division below 200000. */
    {
        uint64_t pmods[] = {3,
                            9,
                            15,
                            1000003,
                            4294967296ULL,
                            4294967311ULL,
                            9223372036854775837ULL,
                            18446744073709551557ULL,
                            18446744073709551615ULL,
                            18446744073709551614ULL};
        for (size_t i = 0; i < sizeof(pmods) / sizeof(pmods[0]); i++) {
            for (int k = 0; k < 3000; k++) {
                uint64_t b = ca_rng_next(&rng), e = k < 40 ? (uint64_t)k : ca_rng_next(&rng);
                uint64_t want = 1 % pmods[i], bb = b % pmods[i], ee = e;
                while (ee) {
                    if (ee & 1) want = ca_mulmod(want, bb, pmods[i]);
                    bb = ca_mulmod(bb, bb, pmods[i]);
                    ee >>= 1;
                }
                CHECK_EQ_U64(ca_powmod(b, e, pmods[i]), want);
            }
        }
        for (uint64_t n = 0; n < 200000; n++) {
            int naive = n >= 2;
            for (uint64_t d = 2; d * d <= n && naive; d++) naive = n % d != 0;
            CHECK(ca_is_prime(n) == naive);
        }
        CHECK(!ca_is_prime(3825123056546413051ULL)); /* spsp to bases 2..23 */
    }
    /* isqrt / iroot */
    CHECK_EQ_U64(ca_isqrt(0), 0);
    CHECK_EQ_U64(ca_isqrt(1), 1);
    CHECK_EQ_U64(ca_isqrt(15), 3);
    CHECK_EQ_U64(ca_isqrt(16), 4);
    CHECK_EQ_U64(ca_isqrt(UINT64_MAX), 4294967295ULL);
    CHECK_EQ_U64(ca_iroot(1000, 3), 10);
    CHECK_EQ_U64(ca_iroot(999, 3), 9);
    CHECK_EQ_U64(ca_iroot(UINT64_MAX, 4), 65535);
    /* sqrt mod prime */
    uint64_t ps[] = {7, 13, 17, 41, 97, 1000003, 4294967291ULL, 1000000000000000003ULL};
    for (size_t i = 0; i < sizeof(ps) / sizeof(ps[0]); i++) {
        for (int k = 0; k < 200; k++) {
            uint64_t a = ca_rng_below(&rng, ps[i]);
            uint64_t sq = ca_mulmod(a, a, ps[i]), r;
            CHECK(ca_sqrtmod_prime(sq, ps[i], &r));
            CHECK_EQ_U64(ca_mulmod(r, r, ps[i]), sq);
        }
    }
    /* factoring */
    ca_factorization f;
    CHECK(ca_factorize(2ULL * 2 * 3 * 7 * 7 * 1000003ULL * 999983ULL, &f) == CA_OK);
    CHECK_EQ_U64(f.count, 5);
    CHECK_EQ_U64(f.f[0].p, 2); CHECK_EQ_U64(f.f[0].e, 2);
    CHECK_EQ_U64(f.f[1].p, 3); CHECK_EQ_U64(f.f[1].e, 1);
    CHECK_EQ_U64(f.f[2].p, 7); CHECK_EQ_U64(f.f[2].e, 2);
    CHECK_EQ_U64(f.f[3].p, 999983); CHECK_EQ_U64(f.f[3].e, 1);
    CHECK_EQ_U64(f.f[4].p, 1000003); CHECK_EQ_U64(f.f[4].e, 1);
    CHECK(ca_factorize(999983ULL * 1000003ULL, &f) == CA_OK);
    CHECK_EQ_U64(f.count, 2);
    CHECK(ca_factorize(4294967291ULL * 4294967279ULL, &f) == CA_OK); /* two 32-bit primes */
    CHECK_EQ_U64(f.count, 2);
    CHECK_EQ_U64(f.f[0].p, 4294967279ULL);
    CHECK_EQ_U64(f.f[1].p, 4294967291ULL);
    CHECK(ca_factorize(p, &f) == CA_OK);
    CHECK_EQ_U64(f.count, 1);
    CHECK_EQ_U64(f.f[0].p, p);
    CHECK(ca_factorize(1ULL << 63, &f) == CA_OK);
    CHECK_EQ_U64(f.f[0].e, 63);
    /* random products */
    for (int k = 0; k < 200; k++) {
        uint64_t n = 1 + ca_rng_below(&rng, UINT64_MAX);
        CHECK(ca_factorize(n, &f) == CA_OK);
        uint64_t prod = 1;
        for (unsigned i = 0; i < f.count; i++) {
            CHECK(ca_is_prime(f.f[i].p));
            for (unsigned e = 0; e < f.f[i].e; e++) prod *= f.f[i].p;
        }
        CHECK_EQ_U64(prod, n);
    }
    /* primitive roots and orders */
    CHECK_EQ_U64(ca_primitive_root(7), 3);
    CHECK_EQ_U64(ca_primitive_root(1000003), 2);
    CHECK_EQ_U64(ca_mult_order(2, 7), 3);
    CHECK_EQ_U64(ca_mult_order(3, 7), 6);
    CHECK_EQ_U64(ca_next_prime(1000000), 1000003);
    CHECK_EQ_U64(ca_next_prime(18446744073709551556ULL), 18446744073709551557ULL);
    CHECK_EQ_U64(ca_next_prime(18446744073709551557ULL), 0); /* no larger 64-bit prime */
    CHECK_EQ_U64(ca_next_prime(UINT64_MAX), 0);
    /* CRT */
    CHECK_EQ_U64(ca_crt2(2, 3, 3, 5), 8);
    CHECK_EQ_U64(ca_crt2(1, 1000003, 5, 999983) % 1000003, 1);
    CHECK_EQ_U64(ca_crt2(1, 1000003, 5, 999983) % 999983, 5);
    /* an unreduced r1 is reduced first (used to give 5, outside [0, 15)) */
    CHECK_EQ_U64(ca_crt2(UINT64_MAX, 3, 1, 5), 6);
    /* Shoup fixed-factor products equal ca_mulmod for every q < 2^63
     * (curve.c's GLV coefficient update relies on it), any a < 2^64. */
    {
        CHECK(!ca_shoup_ok(0) && !ca_shoup_ok(1) && ca_shoup_ok(2));
        CHECK(ca_shoup_ok(((uint64_t)1 << 63) - 1) && !ca_shoup_ok((uint64_t)1 << 63));
        ca_rng srng;
        ca_rng_seed(&srng, 0x5409);
        const uint64_t qs[] = {2,
                               3,
                               23729779,
                               16773703,
                               4294967291ULL,
                               53624256071278747ULL,
                               (1ULL << 62) + 135,
                               ((uint64_t)1 << 63) - 25,
                               ((uint64_t)1 << 63) - 1};
        for (size_t i = 0; i < sizeof(qs) / sizeof(qs[0]); i++) {
            const uint64_t q = qs[i];
            for (int t = 0; t < 20000; t++) {
                uint64_t w = t < 3 ? (uint64_t[]){0, 1, q - 1}[t] : ca_rng_below(&srng, q);
                uint64_t wp = ca_shoup_pre(w, q);
                uint64_t a = (t & 3) == 0   ? ca_rng_next(&srng)
                             : (t & 3) == 1 ? (uint64_t)(t >> 2) % q
                             : (t & 3) == 2 ? UINT64_MAX - (uint64_t)(t >> 2)
                                            : ca_rng_below(&srng, q);
                CHECK_EQ_U64(ca_shoup_mul(a, w, wp, q), ca_mulmod(a, w, q));
            }
        }
    }
    /* sieve */
    uint32_t pr[200];
    CHECK_EQ_U64(ca_sieve_primes(100, pr, 200), 25);
    CHECK_EQ_U64(pr[24], 97);
    TEST_MAIN_END();
}
