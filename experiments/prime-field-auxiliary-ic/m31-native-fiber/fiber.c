#include <stdint.h>
#include <stddef.h>

#define P UINT32_C(2147483647)
static uint32_t mul(uint32_t x,uint32_t y) { return (uint64_t)x*y%P; }
static uint32_t sub(uint32_t x,uint32_t y) { return x>=y ? x-y : P-(y-x); }
static uint32_t add(uint32_t x,uint32_t y) {
    uint32_t s=x+y;
    return s>=P ? s-P : s;
}

/* All buffers contain canonical M31 residues. Output has n slots. */
int m31_reciprocals(const uint32_t *xs,uint32_t *out,size_t n) {
    uint32_t product=1;
    for (size_t i=0;i<n;++i) {
        out[i]=product;
        product=mul(product,xs[i]);
    }
    if (!product) return 0;
    uint32_t inverse=1;
    for (uint32_t e=P-2;e;e>>=1) {
        if (e&1) inverse=mul(inverse,product);
        product=mul(product,product);
    }
    for (size_t i=n;i-- > 0;) {
        out[i]=mul(out[i],inverse);
        inverse=mul(inverse,xs[i]);
    }
    return 1;
}

/* Fold a scratch copy toward the terminal. steps has 3*depth entries. */
int m31_fiber(uint32_t *xs,size_t n,const uint32_t *steps,size_t depth,uint32_t terminal) {
    for (size_t j=0;j<depth;++j,steps+=3) {
        if (n<2 || n%2 || !steps[2]) return 0;
        n/=2;
        for (size_t i=0;i<n;++i) {
            uint32_t u=sub(xs[i],steps[0]), v=sub(xs[i+n],steps[0]);
            if (mul(u,v)!=steps[2]) return 0;
            xs[i]=add(add(u,steps[1]),v);
        }
    }
    return n==1 && xs[0]==terminal;
}
