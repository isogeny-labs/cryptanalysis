/* Coordinate representative for the order-six j=0 rho quotient.
 * Internal to the curve solver and its correctness tests. */
#ifndef CA_CURVE_INTERNAL_H
#define CA_CURVE_INTERNAL_H

#include "cryptanalysis/ca_group.h"
#include "ca_internal.h"

/* Precondition: g carries psi(x,y)=(beta*x,-y), with beta of order three.
 * Return k such that the replacement point is psi^k of the input. */
static inline uint32_t ca_j0_coordinate_class_reduce(const ca_group *g, ca_elem *Y)
{
    if (Y->w[2]) return 0;

    uint64_t x0 = Y->w[0];
    uint64_t x1 = ca_mont_mul(&g->mont, g->endo_c_mont, x0);
    uint64_t x2 = ca_mont_mul(&g->mont, g->endo_c_mont, x1);
    uint64_t best = x0;
    uint32_t j = 0;
    if (x1 < best) { best = x1; j = 1; }
    if (x2 < best) { best = x2; j = 2; }

    uint64_t y = Y->w[1];
    uint64_t minus_y = y ? g->p - y : 0;
    uint32_t neg = minus_y < y;
    Y->w[0] = best;
    if (neg) Y->w[1] = minus_y;
    Y->w[2] = 0;
    Y->w[3] = 0;

    /* psi^j has sign (-1)^j; psi^(j+3) has the opposite sign. */
    return j + 3u * ((j & 1u) ^ neg);
}

/* Same hash-minimum representative and strict k-order tie break as the
 * legacy loop. Factor the six hashes into three x words and two y words.
 *
 * x2 = beta^2 x0 is formed as -(x0 + x1) mod p rather than a second field
 * multiplication: beta is a primitive cube root of unity (cube_root_unity in
 * curve.c, or any test value with beta^3 = 1, beta != 1), so 1 + beta +
 * beta^2 = 0 and x0 + x1 + x2 = 0 mod p, and Montgomery form x -> xR is
 * linear.  ca_mont_mul returns the canonical residue in [0, p) for canonical
 * inputs, and so does the negated sum, so the word is bitwise the one the
 * multiplication gave.  *hash_out (when not NULL) receives the chosen
 * point's ca_group_hash, ca_ec_hash_words of the returned words, so the
 * caller need not hash it again. */
static inline uint32_t ca_j0_factored_hash_class_reduce_h(const ca_group *g, ca_elem *Y,
                                                          uint64_t *hash_out)
{
    if (Y->w[2]) {
        if (hash_out) *hash_out = ca_ec_hash_words(Y->w[0], Y->w[1], Y->w[2]);
        return 0;
    }
    uint64_t x[3];
    x[0] = Y->w[0];
    x[1] = ca_mont_mul(&g->mont, g->endo_c_mont, x[0]);
    {
        const uint64_t s = ca_addmod(x[0], x[1], g->p);
        x[2] = s ? g->p - s : 0;
    }
    const uint64_t y[2] = {Y->w[1], Y->w[1] ? g->p - Y->w[1] : 0};
    const uint64_t yh[2] = {ca_mix64(y[0]), ca_mix64(y[1])};
    uint64_t best_hash = ca_mix64(x[0] * UINT64_C(0x9E3779B97F4A7C15) ^ yh[0]);
    uint32_t best_k = 0;
    for (uint32_t k = 1; k < 6; k++) {
        uint64_t h = ca_mix64(x[k % 3] * UINT64_C(0x9E3779B97F4A7C15) ^ yh[k & 1]);
        if (h < best_hash) { best_hash = h; best_k = k; }
    }
    Y->w[0] = x[best_k % 3];
    Y->w[1] = y[best_k & 1];
    if (best_k) {
        Y->w[2] = 0;
        Y->w[3] = 0;
    }
    if (hash_out) *hash_out = best_hash;
    return best_k;
}

static inline uint32_t ca_j0_factored_hash_class_reduce(const ca_group *g, ca_elem *Y)
{
    return ca_j0_factored_hash_class_reduce_h(g, Y, NULL);
}

/* Private sixfold j=0 orbit representative.  Returns k such that the
 * resulting point is psi^k of its input. */
uint32_t ca_ec_j0_coord_canonicalize(const ca_group *g, ca_elem *Y);

#endif
