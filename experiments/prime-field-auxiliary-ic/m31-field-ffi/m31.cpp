#include "m31.h"

#if defined(__aarch64__) && defined(__ARM_NEON) && !defined(M31_PORTABLE_MULTIPLY)
#define M31_USE_NEON 1
#include <arm_neon.h>
#endif

namespace {
constexpr uint32_t prime = 2147483647;
constexpr size_t width = 64;

inline uint32_t multiply(uint32_t a, uint32_t b) {
    const uint64_t product = uint64_t(a) * b;
    const uint32_t folded = uint32_t(product & prime) + uint32_t(product >> 31);
    return folded >= prime ? folded - prime : folded;
}

#ifdef M31_USE_NEON
inline uint32x4_t canonical_words(uint32x4_t words) {
    const uint32x4_t p = vdupq_n_u32(prime);
    const uint32x4_t folded = vaddq_u32(vandq_u32(words, p), vshrq_n_u32(words, 31));
    return vminq_u32(folded, vsubq_u32(folded, p));
}

inline uint32x4_t multiply(uint32x4_t x, uint32x4_t y) {
    const uint32x4_t p = vdupq_n_u32(prime);
    const uint32x4_t low = vandq_u32(vmulq_u32(x, y), p);
    const int32x4_t high = vqdmulhq_s32(vreinterpretq_s32_u32(x), vreinterpretq_s32_u32(y));
    const uint32x4_t folded = vaddq_u32(low, vreinterpretq_u32_s32(high));
    return vminq_u32(folded, vsubq_u32(folded, p));
}
#endif

// x^(2^Bits-1), using the same addition chain as the M31 scalar control.
template<unsigned Bits, typename T>
T ones(T x) {
    if constexpr (Bits == 1) {
        return x;
    } else {
        const T half = ones<Bits / 2>(x);
        T value = half;
        for (unsigned j = 0; j < Bits / 2; ++j) value = multiply(value, value);
        value = multiply(value, half);
        if constexpr (Bits % 2) value = multiply(multiply(value, value), x);
        return value;
    }
}

template<typename T>
inline T inverse(T x) {
#ifdef M31_USE_NEON
    // The low bits contribute x^5. Four seven-bit blocks cover bits 3..30.
    // The accumulated result is independent of the next block's squarings.
    const T square = multiply(x, x);
    T result = multiply(multiply(square, square), x);
    T block = ones<7>(x);
    for (unsigned j = 0; j < 3; ++j) block = multiply(block, block);
    result = multiply(result, block);
    for (unsigned k = 1; k < 4; ++k) {
        for (unsigned j = 0; j < 7; ++j) block = multiply(block, block);
        result = multiply(result, block);
    }
    return result;
#else
    T t = ones<29>(x);
    t = multiply(t, t);
    return multiply(multiply(t, t), x);
#endif
}

template<typename T>
inline void invert_leaves(T *nodes, size_t n) {
    // Leaves occupy [n,2n). This heap also represents incomplete final tiles.
    for (size_t i = n - 1; i > 0; --i)
        nodes[i] = multiply(nodes[2*i], nodes[2*i+1]);
    nodes[1] = inverse(nodes[1]);
    for (size_t i = 1; i < n; ++i) {
        const T left = nodes[2*i], right = nodes[2*i+1];
        nodes[2*i] = multiply(nodes[i], right);
        nodes[2*i+1] = multiply(nodes[i], left);
    }
}

#ifdef M31_USE_NEON
// Keep the larger scratch arrays in the wide helper frame.
template<size_t capacity = width>
[[gnu::noinline]] void four_tiles(const uint32_t *input, uint32_t *output, size_t n = capacity, size_t last = 4) {
    uint32x4_t nodes[2 * capacity], zero_masks[capacity];
    for (size_t j = 0; j < n; ++j) {
        uint32_t padded[4] = {1, 1, 1, 1};
        const uint32_t *src = input + 4*j;
        if (last < 4 && j + 1 == n) {
            for (size_t k = 0; k < last; ++k) padded[k] = src[k];
            src = padded;
        }
        const uint32x4_t x = canonical_words(vld1q_u32(src));
        zero_masks[j] = vceqq_u32(x, vdupq_n_u32(0));
        nodes[n+j] = vbslq_u32(zero_masks[j], vdupq_n_u32(1), x);
    }
    invert_leaves(nodes, n);
    for (size_t j = 0; j < n; ++j) {
        const uint32x4_t y = vbicq_u32(nodes[n+j], zero_masks[j]);
        if (last < 4 && j + 1 == n) {
            uint32_t tmp[4];
            vst1q_u32(tmp, y);
            for (size_t k = 0; k < last; ++k) output[4*j+k] = tmp[k];
        } else {
            vst1q_u32(output + 4*j, y);
        }
    }
}
#endif

inline void tile(const uint32_t *input, uint32_t *output, size_t n) {
    uint32_t nodes[2 * width];
    for (size_t j = 0; j < n; ++j) {
        const uint32_t x = input[j] % prime;
        nodes[n + j] = x ? x : 1;
    }
    invert_leaves(nodes, n);
    for (size_t j = 0; j < n; ++j)
        output[j] = input[j] % prime ? nodes[n+j] : 0;
}
} // namespace

void m31_batch_inverse(const uint32_t *input, uint32_t *output, size_t count) {
#ifdef M31_USE_NEON
    constexpr size_t wide = 256;  // leaves per SIMD lane
    while (count >= 4 * wide) {
        four_tiles<wide>(input, output, wide);
        input += 4 * wide;
        output += 4 * wide;
        count -= 4 * wide;
    }
    if (count >= 512) {
        four_tiles<wide>(input, output, (count + 3) / 4, (count - 1) % 4 + 1);
        return;
    }
    while (count >= 4 * width) {
        four_tiles(input, output);
        input += 4 * width;
        output += 4 * width;
        count -= 4 * width;
    }
    if (count >= 65 || (count >= 4 && count % 4 == 0)) {
        const size_t vectors = count / 4, extra = count % 4;
        if (extra) four_tiles(input, output, vectors+1, extra);
        else four_tiles(input, output, vectors);
        return;
    }
#endif
    while (count >= width) {
        tile(input, output, width);
        input += width;
        output += width;
        count -= width;
    }
    if (count) tile(input, output, count);
}

void m31_batch_multiply(const uint32_t *left, const uint32_t *right,
                        uint32_t *output, size_t count) {
#ifdef M31_USE_NEON
    while (count >= 4) {
        const uint32x4_t x = canonical_words(vld1q_u32(left));
        const uint32x4_t y = canonical_words(vld1q_u32(right));
        vst1q_u32(output, multiply(x, y));
        left += 4;
        right += 4;
        output += 4;
        count -= 4;
    }
#endif
    for (size_t i = 0; i < count; ++i)
        output[i] = multiply(left[i] % prime, right[i] % prime);
}
