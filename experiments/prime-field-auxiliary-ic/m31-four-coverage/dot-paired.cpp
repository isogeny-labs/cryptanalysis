// Standalone public M31 dot product. Compile with dot-blocks.cpp using the
// -DM31_PAIRED_DOT switch to select the comparison.
#include "dot-kernel.hpp"

__attribute__((noinline)) Word paired_dot(const Word* a, const Word* b, size_t n) {
    auto total = vdupq_n_u64(0);
    const auto mask = vdupq_n_u64(p);
    size_t j = 0;
    for (; n-j >= 16; j+=16) {
        auto low = vdupq_n_u64(0);
        auto high = vdupq_n_u64(0);
        for (size_t k=0; k<16; k+=4) {
            const auto x = vld1q_u32(a+j+k);
            const auto y = vld1q_u32(b+j+k);
            low = vmlal_u32(low,vget_low_u32(x),vget_low_u32(y));
            high = vmlal_high_u32(high,x,y);
        }
        auto foldedLow = vaddq_u64(vandq_u64(low,mask),vshrq_n_u64(low,31));
        auto foldedHigh = vaddq_u64(vandq_u64(high,mask),vshrq_n_u64(high,31));
        total = vaddq_u64(total,vaddq_u64(foldedLow,foldedHigh));
    }
    uint64_t result = vaddvq_u64(total) % p;
    for (; j<n; ++j) result = (result + uint64_t(a[j])*b[j]) % p;
    return Word(result);
}
