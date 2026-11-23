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

kernel void labels(device uint *data [[buffer(0)]],uint i [[thread_position_in_grid]]) {
    uint x=data[i];
    uint rhs=normalize(product(x,normalize(product(x,x)+2u))+14u);
    uint v=rhs;
    for (uint j=0;j<30;++j) v=product(v,v);
    data[i]=uint(v==rhs);
}
