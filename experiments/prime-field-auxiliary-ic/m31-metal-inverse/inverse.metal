#include <metal_stdlib>
using namespace metal;
constant uint p = 2147483647u;

inline uint mul31(uint a, uint b) {
    uint lo = a*b;
    uint high31 = (mulhi(a,b)<<1) | (lo>>31);
    uint folded = (lo&p) + high31;
    return folded >= p ? folded-p : folded;
}

template<uint bits>
inline uint ones(uint x) {
    if constexpr (bits==1) return x;
    else {
        uint halfPower=ones<bits/2>(x), v=halfPower;
        for (uint i=0;i<bits/2;++i) v=mul31(v,v);
        v=mul31(v,halfPower);
        if constexpr (bits%2) v=mul31(mul31(v,v),x);
        return v;
    }
}

inline uint inverse31(uint x) {
    uint v=ones<29>(x);
    v=mul31(v,v);
    return mul31(mul31(v,v),x);
}

kernel void individual(device const uint *x [[buffer(0)]], device uint *y [[buffer(1)]],
                       constant uint &n [[buffer(2)]], uint i [[thread_position_in_grid]]) {
    if (i<n) y[i]=inverse31(x[i]%p);
}

kernel void batch8(device const uint *x [[buffer(0)]], device uint *y [[buffer(1)]],
                   constant uint &n [[buffer(2)]], uint i [[thread_position_in_grid]]) {
    uint stride=n/8+uint(n%8!=0);
    if (i>=stride) return;
    uint a[8], prefix[8], product=1;
    for (uint j=0;j<8;++j) {
        ulong k=ulong(i)+ulong(j)*stride;
        a[j]=k<n ? x[k]%p : 0;
        prefix[j]=product;
        product=mul31(product,a[j] ? a[j] : 1);
    }
    uint carry=inverse31(product);
    for (uint j=8;j>0;--j) {
        uint slot=j-1;
        ulong k=ulong(i)+ulong(slot)*stride;
        if (k<n) y[k]=a[slot] ? mul31(carry,prefix[slot]) : 0;
        carry=mul31(carry,a[slot] ? a[slot] : 1);
    }
}
