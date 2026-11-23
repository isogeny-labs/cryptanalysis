#pragma once
#include <arm_neon.h>
#include <cstddef>
#include <cstdint>

namespace m31root {
using Word = std::uint32_t;
using Vec = uint32x4_t;
constexpr Word prime = 2147483647;
template<bool balanced>
inline Vec step(Vec x) {
    Vec p = vdupq_n_u32(prime);
    Vec hi = vreinterpretq_u32_s32(vqdmulhq_s32(vreinterpretq_s32_u32(x),
                                                 vreinterpretq_s32_u32(x)));
    Vec lo = vmulq_u32(x, x);
    if constexpr (balanced) return vsubq_u32(hi, vbicq_u32(p, lo));
    Vec sum = vaddq_u32(hi, vandq_u32(p, lo));
    return vminq_u32(sum, vsubq_u32(sum, p));
}

template<bool balanced, unsigned chains>
__attribute__((noinline)) void scheduled(const Word* input, Word* output, size_t count) {
    Vec p = vdupq_n_u32(prime);
    for (size_t i = 0; i < count; i += 4 * chains) {
        Vec y[chains];
        for (unsigned j = 0; j < chains; ++j) y[j] = vld1q_u32(input+i+4*j);
        for (unsigned k = 0; k < 29; ++k)
            for (unsigned j = 0; j < chains; ++j) y[j] = step<balanced>(y[j]);
        for (unsigned j = 0; j < chains; ++j) {
            Vec square = step<balanced>(y[j]);
            Vec magnitude = y[j];
            if constexpr (balanced) {
                // The signed fold is in [-p,p), so both operations fit.
                magnitude = vreinterpretq_u32_s32(vabsq_s32(vreinterpretq_s32_u32(y[j])));
                square = vaddq_u32(square, vandq_u32(p, vcltq_s32(
                    vreinterpretq_s32_u32(square), vdupq_n_s32(0))));
            }
            Vec ok = vceqq_u32(square, vld1q_u32(input+i+4*j));
            Vec root = vminq_u32(magnitude, vsubq_u32(p, magnitude));
            vst1q_u32(output+i+4*j, vbslq_u32(ok, root, p));
        }
    }
}

} // namespace m31root
