#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>
using W=uint32_t;
constexpr W p=2147483647;
W add(W x,W y){W z=x+y;return z>=p?z-p:z;}
W sub(W x,W y){return x>=y?x-y:x+(p-y);}
// Canonical field inputs allow a product plus 2p to fit a single Mersenne fold.
W fold(uint64_t product) {
    return add(W(product >> 31), W(product) & p);
}

W mul(W x, W y) {
#ifdef M31_BASELINE_REMAINDER
    return uint64_t(x) * y % p;
#else
    return fold(uint64_t(x) * y);
#endif
}

W inv(W x){
    if(!x)std::abort();
    W acc=1;
    for(W e=p-2;e;e>>=1){if(e&1)acc=mul(acc,x);x=mul(x,x);}
    return acc;
}

template<size_t N>
void invert_chunk(const W* input,W* output,size_t n) {
    std::array<W,N> chain;
    chain.fill(1);
    for(size_t i=0;i<n;i++) {
        output[i]=chain[i%N];
        chain[i%N]=mul(chain[i%N],input[i]);
    }
    std::array<W,N> prefix;
    W total=1;
    for(size_t j=0;j<N;j++) {
        prefix[j]=total;
        total=mul(total,chain[j]);
    }
    W reciprocal=inv(total);
    for(size_t j=N;j-->0;) {
        W next=mul(reciprocal,chain[j]);
        chain[j]=mul(reciprocal,prefix[j]);
        reciprocal=next;
    }
    for(size_t i=n;i-->0;) {
        output[i]=mul(output[i],chain[i%N]);
        chain[i%N]=mul(chain[i%N],input[i]);
    }
}
// Measurement entry point. Input is a distinct array of canonical nonzero field elements.
extern "C" void invert_panel(const W* input,W* output,size_t n,int lanes) {
    for(size_t start=0;start<n;start+=1024) {
        size_t len=std::min<size_t>(1024,n-start);
        if(lanes==1) invert_chunk<1>(input+start,output+start,len);
        else if(lanes==4) invert_chunk<4>(input+start,output+start,len);
        else invert_chunk<8>(input+start,output+start,len);
    }
}
#include <arm_neon.h>

static inline uint32x4_t field4(uint32x4_t a,uint32x4_t b) {
    const auto lo=vmull_u32(vget_low_u32(a),vget_low_u32(b));
    const auto hi=vmull_high_u32(a,b);
    const auto low=vcombine_u32(vmovn_u64(lo),vmovn_u64(hi));
    const auto high=vcombine_u32(vshrn_n_u64(lo,31),vshrn_n_u64(hi,31));
    const auto prime=vdupq_n_u32(p);
    const auto sum=vaddq_u32(vandq_u32(low,prime),high);
    return vminq_u32(sum,vsubq_u32(sum,prime));
}

template<size_t Groups>
void neon_block(const W* input,W* output,size_t n) {
    constexpr size_t width=Groups*4;
    std::array<uint32x4_t,Groups> acc;
    acc.fill(vdupq_n_u32(1));
    const size_t stop=n-n%width;
    for(size_t i=0;i<stop;i+=width) {
        for(size_t g=0;g<Groups;g++){
            vst1q_u32(output+i+4*g,acc[g]);
            acc[g]=field4(acc[g],vld1q_u32(input+i+4*g));
        }
    }
    std::array<W,width> vals,pre;
    for(size_t g=0;g<Groups;g++) vst1q_u32(vals.data()+4*g,acc[g]);
    W total=1;
    for(size_t j=0;j<width;j++){pre[j]=total; total=mul(total,vals[j]);}
    for(size_t i=stop;i<n;i++){output[i]=total;total=mul(total,input[i]);}
    W r=inv(total);
    for(size_t i=n;i-->stop;){output[i]=mul(output[i],r);r=mul(r,input[i]);}
    for(size_t j=width;j-->0;){W next=mul(r,vals[j]);vals[j]=mul(r,pre[j]);r=next;}
    for(size_t g=0;g<Groups;g++) acc[g]=vld1q_u32(vals.data()+4*g);
    for(size_t i=stop;i>0;i-=width){
        for(size_t g=0;g<Groups;g++){
            const size_t at=i-width+4*g;
            vst1q_u32(output+at,field4(vld1q_u32(output+at),acc[g]));
            acc[g]=field4(acc[g],vld1q_u32(input+at));
        }
    }
}
extern "C" void compare_panel(const W* input,W* output,size_t n,int mode) {
    if(mode==8){invert_panel(input,output,n,8);return;}
    for(size_t i=0;i<n;i+=1024) {
        size_t len=std::min<size_t>(1024,n-i);
        if(mode==16) neon_block<2>(input+i,output+i,len);
        else neon_block<4>(input+i,output+i,len);
    }
}
