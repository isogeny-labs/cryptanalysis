#include "../m31-native-product/product.h"
#include <string.h>

#define P UINT32_C(2147483647)
enum { width = 32 };

static void ordinates(const uint32_t rhs[width], uint32_t root[width], uint32_t square[width]) {
    memcpy(root, rhs, width * sizeof(*root));
    for (unsigned i = 0; i < 29; ++i) m31_products(root, root, root, width);
    m31_products(root, root, square, width);
    for (unsigned i = 0; i < width; ++i)
        if (P - root[i] < root[i]) root[i] = P - root[i];
}

/* Both routines return canonical ordinates at x on E and at -x on its twist.
   P is the missing-point sentinel. Inputs are canonical M31 coordinates. */
static void lift(const uint32_t *xs, size_t n, uint32_t *target, uint32_t *twist, int shared) {
    for (size_t start = 0; start < n; start += width) {
        size_t count = n - start < width ? n - start : width;
        uint32_t x[width] = {0}, rhs[width], neg[width], root[width], square[width];
        memcpy(x, xs + start, count * sizeof(*x));
        m31_products(x, x, rhs, width);
        m31_products(rhs, x, rhs, width);
        for (unsigned j = 0; j < width; ++j) {
            rhs[j] = (rhs[j] + UINT64_C(2)*x[j] + 14) % P;
            neg[j] = rhs[j] ? P - rhs[j] : 0;
        }
        ordinates(rhs, root, square);
        for (size_t j = 0; j < count; ++j)
            target[start+j] = square[j] == rhs[j] ? root[j] : P;
        if (!shared) ordinates(neg, root, square);
        for (size_t j = 0; j < count; ++j)
            twist[start+j] = square[j] == neg[j] ? root[j] : P;
    }
}
void shared(const uint32_t *x, size_t n, uint32_t *a, uint32_t *b) { lift(x,n,a,b,1); }
void separate(const uint32_t *x, size_t n, uint32_t *a, uint32_t *b) { lift(x,n,a,b,0); }
