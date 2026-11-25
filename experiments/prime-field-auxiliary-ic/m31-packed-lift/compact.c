#include <stdint.h>
#include <stddef.h>
#include <string.h>

enum { width = 32 };
extern void m31_lift32(const uint32_t xs[width], uint32_t ys[width]);

/* Input is read-only. Each disjoint output has space for n canonical words. */
size_t m31_lift_points(const uint32_t *xs, size_t n, uint32_t *px, uint32_t *py) {
    size_t written = 0;
    while (n) {
        size_t count = n < width ? n : width;
        uint32_t padded[width] = {0}, ys[width];
        const uint32_t *input = xs;
        if (count < width) {
            memcpy(padded, xs, count * sizeof(*xs));
            input = padded;
        }
        m31_lift32(input, ys);
        for (size_t j = 0; j < count; ++j) {
            if (ys[j] != UINT32_C(2147483647)) {
                px[written] = xs[j];
                py[written++] = ys[j];
            }
        }
        xs += count;
        n -= count;
    }
    return written;
}
