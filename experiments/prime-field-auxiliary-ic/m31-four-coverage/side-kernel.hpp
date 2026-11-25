#pragma once
#include <arm_neon.h>
#include <array>
#include <cstdint>

constexpr uint32_t p=2147483647;
using Batch=std::array<uint32_t,32>;
using Labels=std::array<uint8_t,32>;

inline uint32_t rhs(uint64_t x) { return ((x*x%p+2)*x+14)%p; }

inline bool reciprocity(uint32_t a) {
    if (!a) return true;
    uint32_t n=p;
    bool negative=false;
    while (a) {
        unsigned shift=__builtin_ctz(a);
        if ((shift&1) && ((n&7)==3 || (n&7)==5)) negative=!negative;
        a >>= shift;
        if ((a&n&3)==3) negative=!negative;
        uint32_t next=n%a;
        n=a;
        a=next;
    }
    return !negative;
}

inline int32x4_t fold(int32x4_t x) {
    auto hi=vqdmulhq_s32(x,x);
    auto mask=vdupq_n_s32(p);
    return vaddq_s32(hi,vsubq_s32(vandq_s32(vmulq_s32(x,x),mask),mask));
}

inline int32x4_t complement_square(int32x4_t lane) {
    auto high=vqdmulhq_s32(lane,lane);
    auto low=vmulq_s32(lane,lane);
    int32x4_t complement;
#ifdef M31_REGISTER_BIC
    // Keep the mask in a register for one vector BIC instruction.
    asm("bic %0.16b, %1.16b, %2.16b"
        : "=w"(complement) : "w"(vdupq_n_s32(p)), "w"(low));
#else
    complement=vbicq_s32(vdupq_n_s32(p),low);
#endif
    return vsubq_s32(high,complement);
}

// Both cubic intermediates are below 2^62. Fold each wide product
// once at bit 31, then subtract p when the representative is at least p.
inline uint32x2_t reduce_cubic_product(uint64x2_t t) {
    auto mask = vdup_n_u32(p);
    auto folded = vadd_u32(vand_u32(vmovn_u64(t), mask), vshrn_n_u64(t, 31));
    return vsub_u32(folded, vand_u32(vcge_u32(folded, mask), mask));
}

inline uint32x2_t cubic_pair(uint32x2_t x) {
    auto square = reduce_cubic_product(vmull_u32(x, x));
    auto product = vmull_u32(vadd_u32(square, vdup_n_u32(2)), x);
    return reduce_cubic_product(vaddq_u64(product, vdupq_n_u64(14)));
}

template<int arm, bool input_is_rhs=false>
__attribute__((noinline)) Labels classify(const Batch& x) {
    static_assert(!input_is_rhs || arm==3);
    Labels out{};
    if constexpr (arm==0) {
        for (size_t i=0;i<x.size();++i) out[i]=reciprocity(rhs(x[i]));
    } else {
        Batch r;
        if constexpr (input_is_rhs) {
            r=x;
        } else if constexpr (arm==4) {
            for (size_t i=0;i<x.size();i+=2)
                vst1_u32(&r[i], cubic_pair(vld1_u32(&x[i])));
        } else {
            for (size_t i=0;i<x.size();++i) r[i]=rhs(x[i]);
        }
        int32x4_t state[8];
        for (int j=0;j<8;++j) state[j]=vreinterpretq_s32_u32(vld1q_u32(&r[4*j]));
        for (int k=0;k<30;++k) for (auto& lane:state) {
            if constexpr (arm==3 || arm==4) {
                lane=complement_square(lane);
            } else lane=fold(lane);
        }
        for (int j=0;j<8;++j) {
            auto t=state[j];
            auto sign=vshrq_n_s32(t,31);
            auto input=vreinterpretq_s32_u32(vld1q_u32(&r[4*j]));
            uint32x4_t bit;
            if constexpr (arm==1 || arm==3 || arm==4) {
                auto canonical=vaddq_s32(t,vandq_s32(sign,vdupq_n_s32(p)));
                bit=vshrq_n_u32(vceqq_s32(canonical,input),31);
            } else {
                auto difference=veorq_s32(veorq_s32(t,sign),input);
                bit=vandq_u32(vreinterpretq_u32_s32(vmvnq_s32(difference)),vdupq_n_u32(1));
            }
            uint32_t tmp[4];
            vst1q_u32(tmp,bit);
            for(int k=0;k<4;++k) out[4*j+k]=tmp[k];
        }
    }
    return out;
}
