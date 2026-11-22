#include "product.h"
#if defined(__aarch64__)
#include <arm_neon.h>
#endif

#define P UINT32_C(2147483647)

void m31_products(const uint32_t *a, const uint32_t *b, uint32_t *out, size_t n) {
    size_t i = 0;
#if defined(__aarch64__) && !defined(M31_PORTABLE)
    const uint32x4_t p = vdupq_n_u32(P);
    for (; n - i >= 4; i += 4) {
        uint32x4_t x = vld1q_u32(a+i), y = vld1q_u32(b+i);
#ifdef M31_WIDEN
        uint64x2_t u = vmull_u32(vget_low_u32(x), vget_low_u32(y));
        uint64x2_t v = vmull_high_u32(x,y);
        uint32x4_t lo = vcombine_u32(vmovn_u64(u), vmovn_u64(v));
        uint32x4_t hi = vcombine_u32(vshrn_n_u64(u,31), vshrn_n_u64(v,31));
#else
        uint32x4_t lo = vmulq_u32(x,y);
        uint32x4_t hi = vreinterpretq_u32_s32(vqdmulhq_s32(
            vreinterpretq_s32_u32(x), vreinterpretq_s32_u32(y)));
#endif
        uint32x4_t sum = vaddq_u32(vandq_u32(lo,p),hi);
        vst1q_u32(out+i,vminq_u32(sum,vsubq_u32(sum,p)));
    }
#endif
    for (; i < n; ++i) {
        uint64_t product = (uint64_t)a[i] * b[i];
        uint32_t sum = (product & P) + (product >> 31);
        out[i] = sum >= P ? sum-P : sum;
    }
}
