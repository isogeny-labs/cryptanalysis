#pragma once
#include <arm_neon.h>
#include <cstddef>
#include <cstdint>

constexpr uint64_t p = 2147483647;
using Word = uint32_t;

inline uint32x2_t load_pair(const uint64_t* x) {
    return vmovn_u64(vld1q_u64(x));
}
inline uint32x2_t load_pair(const Word* x) {
    return vld1_u32(x);
}

template<bool partial, class Input>
__attribute__((noinline)) Word dot(const Input* a, const Input* b, size_t n) {
    auto total = vdupq_n_u64(0);
    auto mask = vdupq_n_u64(p);
    size_t j = 0;
    for (; j+8 <= n; j+=8) {
        auto s = vdupq_n_u64(0);
        for (size_t k=0; k<8; k+=2)
            s = vmlal_u32(s,load_pair(a+j+k),load_pair(b+j+k));
        s = vaddq_u64(vandq_u64(s,mask),vshrq_n_u64(s,31));
        if constexpr (!partial) {
            s = vaddq_u64(vandq_u64(s,mask),vshrq_n_u64(s,31));
            s = vsubq_u64(s,vandq_u64(vcgeq_u64(s,mask),mask));
        }
        total = vaddq_u64(total,s);
    }
    uint64_t result = vaddvq_u64(total) % p;
    for (; j<n; ++j) result = (result + uint64_t(a[j])*b[j]) % p;
    return Word(result);
}
