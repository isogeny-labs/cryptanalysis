#include <stddef.h>
#include <stdint.h>

#define P UINT32_C(2147483647)

static uint32_t sub(uint32_t a, uint32_t b) {
    return a >= b ? a-b : P-(b-a);
}
static uint32_t mul(uint32_t a, uint32_t b) {
    return ((uint64_t)a*b)%P;
}
static uint32_t inverse(uint32_t a) {
    uint32_t r=1;
    for (uint32_t k=P-2; k; k>>=1) {
        if (k&1) r=mul(r,a);
        a=mul(a,a);
    }
    return r;
}

/* Append one translate on y^2=x^3+x. The caller supplies 2*n slots for
   each coordinate array and n slots for the prefix products. */
int m31_translate(size_t n, uint32_t *xs, uint32_t *ys, uint32_t *prefix,
                  uint32_t u, uint32_t v) {
    uint32_t product=1;
    for (size_t i=0;i<n;++i) {
        prefix[i]=product;
        product=mul(product,sub(u,xs[i]));
    }
    if (!product) return 0;
    uint32_t inv=inverse(product);
    for (size_t i=n;i-- > 0;) {
        uint32_t x=xs[i], y=ys[i];
        uint32_t slope=mul(sub(v,y),mul(prefix[i],inv));
        inv=mul(inv,sub(u,x));
        uint32_t z=sub(sub(mul(slope,slope),x),u);
        xs[n+i]=z;
        ys[n+i]=sub(mul(slope,sub(x,z)),y);
    }
    return 1;
}
