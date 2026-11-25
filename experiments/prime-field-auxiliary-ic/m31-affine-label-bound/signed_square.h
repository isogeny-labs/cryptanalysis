#pragma once
#include <arm_neon.h>

// Every signed input lane is in [-p,p]. The square is nonnegative and fits
// the doubling-high operation even for -p. The new lane is in [-p,p).
inline uint32x4_t signedSquare(uint32x4_t bits) {
    auto x = vreinterpretq_s32_u32(bits);
    auto hi = vreinterpretq_u32_s32(vqdmulhq_s32(x,x));
    auto lo = vandq_u32(vmulq_u32(bits,bits), vdupq_n_u32(2147483647));
    return vsubq_u32(vaddq_u32(hi,lo), vdupq_n_u32(2147483647));
}

inline uint32x4_t canonicalSigned(uint32x4_t bits) {
    auto negative = vcltq_s32(vreinterpretq_s32_u32(bits), vdupq_n_s32(0));
    return vaddq_u32(bits, vandq_u32(negative, vdupq_n_u32(2147483647)));
}
