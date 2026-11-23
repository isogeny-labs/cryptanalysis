#include <metal_stdlib>
using namespace metal;
constant uint p=2147483647u;

// Split-word M31 reduction from ../m31-metal-inverse/inverse.metal.
inline uint product(uint a,uint b) {
    uint lo=a*b;
    uint high=(mulhi(a,b)<<1)|(lo>>31);
    uint s=(lo&p)+high;
    return min(s,s-p);
}
inline uint normalize(uint x) { return min(x,x-p); }

inline uint lift(uint x) {
    uint rhs=normalize(product(x,normalize(product(x,x)+2u))+14u);
    uint v=rhs;
    for (uint j=0;j<30;++j) v=product(v,v);
    return uint(v==rhs);
}

kernel void labels(device uint *data [[buffer(0)]],uint i [[thread_position_in_grid]]) {
    data[i]=lift(data[i]);
}

// One batch covers at most 2^26 words. 65536 workers partition its offsets.
kernel void field_totals(device uint4 *out [[buffer(0)]], constant uint2 &range [[buffer(1)]],
                         uint id [[thread_position_in_grid]], uint lane [[thread_index_in_threadgroup]],
                         uint group [[threadgroup_position_in_grid]]) {
    uint4 value=0;
    for (uint j=id; j<range.y; j+=65536u) {
        uint x=range.x+j, yes=lift(x);
        value.x+=yes;
        value.y^=x*(yes);
        value.z+=yes*uint((x&4u)==0);
        ++value.w;
    }
    threadgroup uint4 scratch[256];
    scratch[lane]=value;
    for (uint stride=128; stride; stride>>=1) {
        threadgroup_barrier(mem_flags::mem_threadgroup);
        if (lane<stride) {
            uint4 other=scratch[lane+stride], v=scratch[lane];
            scratch[lane]=uint4(v.x+other.x,v.y^other.y,v.z+other.z,v.w+other.w);
        }
    }
    if (lane==0) out[group]=scratch[0];
}
