#include <stdint.h>
#include <stddef.h>
#define P UINT32_C(2147483647)
#ifndef M31_LANES
#define M31_LANES 4
#endif
static inline uint32_t mul(uint32_t x,uint32_t y) {
    uint64_t z=(uint64_t)x*y;
#ifdef M31_USE_REMAINDER
    return z % P;
#else
    uint32_t sum=(uint32_t)(z>>31)+((uint32_t)z&P);
    return sum >= P ? sum-P : sum;
#endif
}
static inline uint32_t sub(uint32_t x,uint32_t y) {
    return x>=y?x-y:P-(y-x);
}
static uint32_t inverse(uint32_t a) {
    uint32_t r=1;
    for(uint32_t e=P-2;e;e>>=1) {
        if(e&1) r=mul(r,a);
        a=mul(a,a);
    }
    return r;
}
extern int scalar_translate(size_t,uint32_t*,uint32_t*,uint32_t*,uint32_t,uint32_t);
extern int scalar_reciprocals(const uint32_t*,uint32_t*,size_t);
int m31_reciprocals(const uint32_t *xs,uint32_t *out,size_t n) {
    if(n%M31_LANES || n<64) return scalar_reciprocals(xs,out,n);
    uint32_t product[M31_LANES];
    for(unsigned j=0;j<M31_LANES;++j) product[j]=1;
    for(size_t i=0;i<n;i+=M31_LANES)
        for(unsigned j=0;j<M31_LANES;++j) {
            out[i+j]=product[j];
            product[j]=mul(product[j],xs[i+j]);
        }
    for(unsigned j=0;j<M31_LANES;++j) {
        if(!product[j]) return 0;
        product[j]=inverse(product[j]);
    }
    for(size_t end=n;end;end-=M31_LANES)
        for(unsigned j=0;j<M31_LANES;++j) {
            size_t i=end-M31_LANES+j;
            out[i]=mul(out[i],product[j]);
            product[j]=mul(product[j],xs[i]);
        }
    return 1;
}
int m31_translate(size_t n,uint32_t *xs,uint32_t *ys,uint32_t *prefix,uint32_t u,uint32_t v) {
    if(n%M31_LANES || n<64) return scalar_translate(n,xs,ys,prefix,u,v);
    uint32_t product[M31_LANES];
    for(unsigned j=0;j<M31_LANES;++j) product[j]=1;
    for(size_t i=0;i<n;i+=M31_LANES)
        for(unsigned j=0;j<M31_LANES;++j) {
            prefix[i+j]=product[j];
            product[j]=mul(product[j],sub(u,xs[i+j]));
        }
    for(unsigned j=0;j<M31_LANES;++j) {
        if(!product[j]) return 0;
        product[j]=inverse(product[j]);
    }
    for(size_t end=n;end;end-=M31_LANES)
        for(unsigned j=0;j<M31_LANES;++j) {
            size_t i=end-M31_LANES+j;
            uint32_t x=xs[i],y=ys[i];
            uint32_t slope=mul(sub(v,y),mul(prefix[i],product[j]));
            product[j]=mul(product[j],sub(u,x));
            uint32_t z=sub(sub(mul(slope,slope),x),u);
            xs[n+i]=z;
            ys[n+i]=sub(mul(slope,sub(x,z)),y);
        }
    return 1;
}
