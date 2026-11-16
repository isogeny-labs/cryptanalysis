/* Private bounded rational reconstruction for native IC descent. */
#ifndef CA_IC_RATIONAL_H
#define CA_IC_RATIONAL_H
#include "cryptanalysis/ca_modarith.h"

/* Euclidean rational reconstruction: a = signed_b * value (mod p).
 * Stop when the numerator is at most floor(sqrt(p)); the corresponding
 * denominator has magnitude at most p/(floor(sqrt(p))+1). All coefficient
 * arithmetic is signed 128-bit; the Euclidean remainders stay in a word. */
static inline void ca_ic_rational_split(uint64_t value, uint64_t p, uint64_t bound,
                                        uint64_t *numerator, uint64_t *denominator, int *negative)
{
    uint64_t r0 = p, r1 = value;
    ca_i128 t0 = 0, t1 = 1;
    while (r1 > bound) {
        uint64_t q = r0 / r1;
        uint64_t r2 = r0 - q * r1;
        ca_i128 t2 = t0 - (ca_i128)q * t1;
        r0 = r1;
        r1 = r2;
        t0 = t1;
        t1 = t2;
    }
    *numerator = r1;
    *negative = t1 < 0;
    *denominator = (uint64_t)(t1 < 0 ? -t1 : t1);
}

#endif
