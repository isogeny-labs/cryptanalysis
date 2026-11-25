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

static inline uint32_t curve_rhs(uint64_t x) {
    return reduce(reduce(x*x)*x + 2*x + 14);
}

static inline uint32_t checked_root(uint32_t rhs, uint32_t y) {
    if (reduce((uint64_t)y*y) != rhs) return P;
    return y < P-y ? y : P-y;
}

/* For each canonical x, output the smaller square root, or P on failure. */
void lift_batch(const uint32_t *restrict xs, uint32_t *restrict ys, size_t count) {
    enum { width = 32 };
    size_t i = 0;
    for (; count-i >= width; i += width) {
        uint32_t rhs[width], y[width];
        for (size_t k = 0; k < width; ++k)
            y[k] = rhs[k] = curve_rhs(xs[i+k]);

        /* Each lane computes rhs^(2^29). Advancing the lanes together
           lets the compiler overlap the independent modular squares. */
        for (int j = 0; j < 29; ++j)
            for (size_t k = 0; k < width; ++k)
                y[k] = reduce((uint64_t)y[k]*y[k]);

        for (size_t k = 0; k < width; ++k)
            ys[i+k] = checked_root(rhs[k], y[k]);
    }

    for (; i < count; ++i) {
        uint32_t rhs = curve_rhs(xs[i]), y = rhs;
        for (int j = 0; j < 29; ++j) y = reduce((uint64_t)y*y);
        ys[i] = checked_root(rhs, y);
    }
}
