#include <stdint.h>
#include <stddef.h>

#define P UINT32_C(2147483647)

/* Inputs to reduce are at most (P-1)^2 + 2(P-1) + 14. */
static inline uint32_t reduce(uint64_t z) {
#ifdef USE_REMAINDER
    return z % P;
#else
    uint32_t folded = (z & P) + (z >> 31);
    return folded >= P ? folded - P : folded;
#endif
}

/* For each canonical x, output the smaller square root, or P on failure. */
void lift_batch(const uint32_t *restrict xs, uint32_t *restrict ys, size_t count) {
    for (size_t i = 0; i < count; ++i) {
        uint64_t x = xs[i];
        uint32_t rhs = reduce(reduce(x*x)*x + 2*x + 14);
        uint64_t y = rhs;
        for (int j = 0; j < 29; ++j) y = reduce(y*y);
        ys[i] = reduce(y*y) == rhs ? (y < P-y ? y : P-y) : P;
    }
}
