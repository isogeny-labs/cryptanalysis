#include <stddef.h>
#include <stdint.h>

#define P UINT32_C(2147483647)

static uint32_t add(uint32_t a, uint32_t b) {
    uint32_t s = a + b;
    return s >= P ? s - P : s;
}
static uint32_t sub(uint32_t a, uint32_t b) {
    return a >= b ? a-b : P-(b-a);
}
static uint32_t mul(uint32_t a, uint32_t b) {
    uint64_t z = (uint64_t)a * b;
    return add((uint32_t)(z >> 31), (uint32_t)z & P);
}

/* Scratch is disposable on rejection. steps contains (r,A,B) triples. */
int m31_batched_fiber(uint32_t *xs, size_t n, const uint32_t *steps,
                      size_t depth, uint32_t terminal) {
    if (terminal >= P) return 0;
    if (!depth) return n == 1 && xs[0] == terminal;
    for (size_t j = 0; j < depth; ++j, steps += 3) {
        uint32_t r = steps[0], a = steps[1], b = steps[2];
        if (n < 2 || n % 2 || r >= P || a >= P || !b || b >= P) return 0;
        n /= 2;
        uint32_t errors = 0;
        for (size_t i = 0; i < n; ++i) {
            uint32_t x = xs[i], y = xs[i+n];
            if (j == 0) errors |= (x >= P) | (y >= P);
            uint32_t u = sub(x,r), v = sub(y,r);
            errors |= (u == v) | (mul(u,v) ^ b);
            xs[i] = add(add(u,a),v);
        }
        if (errors) return 0;
    }
    return n == 1 && xs[0] == terminal;
}
