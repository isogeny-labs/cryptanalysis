/* Private fixed-divisor arithmetic for IC smoothness checks. */
#ifndef CA_IC_TRIAL_H
#define CA_IC_TRIAL_H

#include <stdint.h>

typedef struct ca_ic_divisor {
    uint64_t inverse;             /* q^-1 modulo 2^64, for odd q */
    uint64_t limit;               /* floor((2^64 - 1) / q) */
} ca_ic_divisor;

/* q is a factor-base prime. Setup divisions are paid once per context. */
static inline ca_ic_divisor ca_ic_divisor_init(uint32_t q)
{
    ca_ic_divisor d = {0, UINT64_MAX / q};
    if (q & 1) {
        uint64_t x = 1;
        for (unsigned i = 0; i < 6; ++i) x *= 2 - (uint64_t)q * x;
        d.inverse = x;
    }
    return d;
}

/* For odd q, t = v*q^-1 (mod 2^64) is <= floor(UINT64_MAX/q)
 * exactly when q divides v; in that case t is the exact quotient.
 * Unsigned wraparound is intentional. No wide multiply or ISA extension
 * is required. q=2 uses shifts. v must be nonzero. */
static inline int32_t ca_ic_remove_prime(uint64_t *v, uint32_t q,
                                       const ca_ic_divisor *d)
{
    int32_t e = 0;
    if (q == 2) {
        e = (int32_t)__builtin_ctzll(*v);
        *v >>= e;
    } else {
        uint64_t t = *v * d->inverse;
        while (t <= d->limit) {
            *v = t;
            ++e;
            t = *v * d->inverse;
        }
    }
    return e;
}

#endif
