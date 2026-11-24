#pragma once
#include "side-kernel.hpp"

namespace m31_vector {
using V=uint32x4_t;
inline V dup(uint32_t x) { return vdupq_n_u32(x); }
inline V plus(V x,V y) {
    V s=vaddq_u32(x,y);
    return vminq_u32(s,vsubq_u32(s,dup(p)));
}
inline V minus(V x,V y) { return plus(x,vsubq_u32(dup(p),y)); }
inline V times(V x,V y) {
    V h=vreinterpretq_u32_s32(vqdmulhq_s32(vreinterpretq_s32_u32(x),vreinterpretq_s32_u32(y)));
    return plus(h,vandq_u32(vmulq_u32(x,y),dup(p)));
}
}
