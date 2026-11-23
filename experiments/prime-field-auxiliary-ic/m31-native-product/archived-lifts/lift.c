#include "../product.h"
#include <string.h>

#define P UINT32_C(2147483647)
#define WIDTH 32

/* Public depth-five fixture. Return P for missing points and the smaller
   square root for every affine lift. Inputs are canonical M31 coordinates. */
void m31_lift32(const uint32_t xs[WIDTH], uint32_t output[WIDTH]) {
    uint32_t rhs[WIDTH], roots[WIDTH], squares[WIDTH];
    m31_products(xs, xs, rhs, WIDTH);
    m31_products(rhs, xs, rhs, WIDTH);
    for (unsigned i = 0; i < WIDTH; ++i)
        rhs[i] = (rhs[i] + UINT64_C(2)*xs[i] + 14) % P;
    memcpy(roots, rhs, sizeof roots);
    for (unsigned j = 0; j < 29; ++j)
        m31_products(roots, roots, roots, WIDTH);
    m31_products(roots, roots, squares, WIDTH);
    for (unsigned i = 0; i < WIDTH; ++i) {
        const uint32_t other = P - roots[i];
        output[i] = squares[i] != rhs[i] ? P : (roots[i] < other ? roots[i] : other);
    }
}
