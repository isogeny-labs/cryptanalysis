#include <stddef.h>
#include <stdint.h>

#define P UINT32_C(2147483647)

static uint32_t multiply(uint32_t a, uint32_t b) {
    uint64_t product = (uint64_t)a * b;
    uint32_t sum = (uint32_t)(product >> 31) + ((uint32_t)product & P);
    return sum >= P ? sum - P : sum;
}

static uint32_t add(uint32_t a, uint32_t b) {
    uint32_t sum = a + b;
    return sum >= P ? sum - P : sum;
}

/* All input residues must be below P. Each output is the smaller ordinate
   of a point above xs[i], or P if the curve equation has no solution. */
void lift_ordinates(const uint32_t *xs, size_t count, uint32_t a, uint32_t b,
                    uint32_t *ordinates) {
    for (size_t i = 0; i < count; ++i) {
        uint32_t x = xs[i];
        uint32_t rhs = add(multiply(add(multiply(x, x), a), x), b);
        uint32_t y = rhs;
        for (unsigned j = 0; j < 29; ++j) y = multiply(y, y);
        uint32_t other = P - y;
        ordinates[i] = multiply(y, y) == rhs ? (y < other ? y : other) : P;
    }
}
