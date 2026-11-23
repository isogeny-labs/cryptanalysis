// Native public census of the 31 rotations of a canonical M31 coordinate.
#pragma once
#include <arm_neon.h>
#include <cstdint>

namespace orbit_simd {
using V = uint32x4_t;
constexpr uint32_t modulus = 2147483647;
inline V add(V a, V b) {
    V s = vaddq_u32(a,b);
    return vminq_u32(s, vsubq_u32(s,vdupq_n_u32(modulus)));
}
template<int k> inline V rotate(V x) {
    return vorrq_u32(vandq_u32(vshlq_n_u32(x,k),vdupq_n_u32(modulus)),vshrq_n_u32(x,31-k));
}
template<unsigned k> inline V initial(uint32_t x) {
    uint32_t lanes[4];
    for (auto& lane : lanes) {
        lane = x;
        x = ((x << k) & modulus) | (x >> (31-k));
    }
    return vld1q_u32(lanes);
}
inline V multiply(V a, V b) {
    V hi = vreinterpretq_u32_s32(vqdmulhq_s32(vreinterpretq_s32_u32(a),vreinterpretq_s32_u32(b)));
    return add(hi,vandq_u32(vmulq_u32(a,b),vdupq_n_u32(modulus)));
}
inline void square_masks(const V (&input)[8], V (&mask)[8]) {
    V y[8];
    for (int j=0;j<8;++j) y[j]=input[j];
    const V p=vdupq_n_u32(modulus);
    for (int k=0;k<30;++k) {
        for (auto& v : y) {
            auto sv=vreinterpretq_s32_u32(v);
            V hi=vreinterpretq_u32_s32(vqdmulhq_s32(sv,sv));
            v=vsubq_u32(hi,vbicq_u32(p,vmulq_u32(v,v)));
        }
    }
    for (int j=0;j<8;++j) {
        V neg=vcltq_s32(vreinterpretq_s32_u32(y[j]),vdupq_n_s32(0));
        mask[j]=vceqq_u32(vaddq_u32(y[j],vandq_u32(neg,p)),input[j]);
    }
}
template<bool rotate_powers> inline void classify(uint32_t seed, uint64_t& eligible, uint64_t& lifts) {
    V x=initial<1>(seed), x2{}, x3{};
    if constexpr (rotate_powers) {
        uint32_t s=uint64_t(seed)*seed%modulus;
        x2=initial<2>(s);
        x3=initial<3>(uint64_t(s)*seed%modulus);
    }
    V aux[8], target[8], aux_square[8], target_square[8];
    for (int j=0;j<8;++j) {
        if constexpr (!rotate_powers) { x2=multiply(x,x); x3=multiply(x,x2); }
        aux[j]=add(x2,vdupq_n_u32(1));
        target[j]=add(add(x3,rotate<1>(x)),vdupq_n_u32(14));
        x=rotate<4>(x);
        if constexpr (rotate_powers) { x2=rotate<8>(x2); x3=rotate<12>(x3); }
    }
    square_masks(aux,aux_square);
    square_masks(target,target_square);
    // Lane 31 repeats lane zero after a full orbit.
    aux_square[7]=vsetq_lane_u32(UINT32_MAX,aux_square[7],3);
    V counts=vdupq_n_u32(0), hits=vdupq_n_u32(0);
    for (int j=0;j<8;++j) {
        V accepted=vmvnq_u32(aux_square[j]);
        counts=vsubq_u32(counts,accepted);
        hits=vsubq_u32(hits,vandq_u32(accepted,target_square[j]));
    }
    eligible+=vaddvq_u32(counts);
    lifts+=vaddvq_u32(hits);
}
} // namespace orbit_simd
