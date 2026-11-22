#include "m31.h"

namespace {
constexpr uint32_t prime = 2147483647;
constexpr size_t width = 64;

inline uint32_t multiply(uint32_t a, uint32_t b) {
    const uint64_t product = uint64_t(a) * b;
    const uint32_t folded = uint32_t(product & prime) + uint32_t(product >> 31);
    return folded >= prime ? folded - prime : folded;
}

// x^(2^Bits-1), using the same addition chain as the M31 scalar control.
template<unsigned Bits>
uint32_t ones(uint32_t x) {
    if constexpr (Bits == 1) {
        return x;
    } else {
        const uint32_t half = ones<Bits / 2>(x);
        uint32_t value = half;
        for (unsigned j = 0; j < Bits / 2; ++j) value = multiply(value, value);
        value = multiply(value, half);
        if constexpr (Bits % 2) value = multiply(multiply(value, value), x);
        return value;
    }
}

inline uint32_t inverse(uint32_t x) {
    uint32_t t = ones<29>(x);
    t = multiply(t, t);
    return multiply(multiply(t, t), x);
}

inline void tile(const uint32_t *input, uint32_t *output, size_t n) {
    uint32_t nodes[2 * width];
    for (size_t j = 0; j < n; ++j) {
        const uint32_t x = input[j] % prime;
        nodes[n + j] = x ? x : 1;
    }
    // Leaves occupy [n,2n). This heap also represents incomplete final tiles.
    for (size_t i = n - 1; i > 0; --i)
        nodes[i] = multiply(nodes[2*i], nodes[2*i+1]);
    nodes[1] = inverse(nodes[1]);
    for (size_t i = 1; i < n; ++i) {
        const uint32_t left = nodes[2*i], right = nodes[2*i+1];
        nodes[2*i] = multiply(nodes[i], right);
        nodes[2*i+1] = multiply(nodes[i], left);
    }
    for (size_t j = 0; j < n; ++j)
        output[j] = input[j] % prime ? nodes[n+j] : 0;
}
} // namespace

void m31_batch_inverse(const uint32_t *input, uint32_t *output, size_t count) {
    while (count >= width) {
        tile(input, output, width);
        input += width;
        output += width;
        count -= width;
    }
    if (count) tile(input, output, count);
}
