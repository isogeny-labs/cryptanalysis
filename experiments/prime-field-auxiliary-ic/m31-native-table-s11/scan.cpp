#include "m31.h"
#include <cstddef>
#include <cstdint>

namespace {
constexpr uint32_t p = 2147483647;

inline uint32_t sub(uint32_t a, uint32_t b) {
    return a >= b ? a - b : a + p - b;
}

inline uint32_t mul(uint32_t a, uint32_t b) {
    const uint64_t product = uint64_t(a) * b;
    const uint32_t folded = uint32_t(product & p) + uint32_t(product >> 31);
    return folded >= p ? folded - p : folded;
}
} // namespace

// Returns zero for valid canonical inputs. Equal-x entries use UINT32_MAX in
// out_x and are resolved by the caller's checked group law.
extern "C" int m31_sum_row(uint32_t left_x, uint32_t left_y,
                            const uint32_t *base_x, const uint32_t *base_y,
                            uint32_t *out_x, uint32_t *out_y,
                            uint32_t *den, uint32_t *inverse, size_t count) {
    if (count == 0 || count > 2026 || !base_x || !base_y || !out_x || !out_y ||
        !den || !inverse || left_x >= p || left_y >= p)
        return 1;
    for (size_t k = 0; k < count; ++k) {
        if (base_x[k] >= p || base_y[k] >= p)
            return 1;
        den[k] = sub(base_x[k], left_x);
    }
    m31_batch_inverse(den, inverse, count);
    for (size_t k = 0; k < count; ++k) {
        if (den[k] == 0) {
            out_x[k] = UINT32_MAX;
            out_y[k] = 0;
            continue;
        }
        const uint32_t slope = mul(sub(base_y[k], left_y), inverse[k]);
        const uint32_t x = sub(sub(mul(slope, slope), left_x), base_x[k]);
        out_x[k] = x;
        out_y[k] = sub(mul(slope, sub(left_x, x)), left_y);
    }
    return 0;
}

// Returns SIZE_MAX if an exceptional pair requires the Rust group-law path.
// The caller supplies room for 2*pairs output entries and a 2^22-bit bitmap.
extern "C" size_t m31_scan_pairs(uint32_t left_x, uint32_t left_y,
                                  const uint32_t *base_x, const uint32_t *base_y,
                                  const uint64_t *bitmap, uint32_t *out_index,
                                  uint32_t *out_key, size_t pairs) {
    if (pairs == 0 || pairs > 1013 || !base_x || !base_y || !bitmap || !out_index || !out_key ||
        left_x >= p || left_y >= p)
        return SIZE_MAX;
    uint32_t den[1013], inverse[1013];
    for (size_t i = 0; i < pairs; ++i) {
        const uint32_t x = base_x[2*i];
        if (x != base_x[2*i+1] || x >= p || base_y[2*i] >= p || base_y[2*i+1] >= p || x == left_x)
            return SIZE_MAX;
        den[i] = sub(x, left_x);
    }
    m31_batch_inverse(den, inverse, pairs);
    size_t output_count = 0;
    for (size_t k = 0; k < 2*pairs; ++k) {
        const uint32_t slope = mul(sub(base_y[k], left_y), inverse[k/2]);
        const uint32_t x = sub(sub(mul(slope, slope), left_x), base_x[k]);
        const size_t bit = x >> 9;
        if ((bitmap[bit >> 6] & (uint64_t(1) << (bit & 63))) == 0)
            continue;
        const uint32_t y = sub(mul(slope, sub(left_x, x)), left_y);
        out_index[output_count] = uint32_t(k);
        out_key[output_count] = (x << 1) | (y & 1);
        ++output_count;
    }
    return output_count;
}
