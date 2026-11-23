#include <stdint.h>
#define P UINT32_C(2147483647)
static uint32_t add(uint32_t x, uint32_t y) {
    uint32_t s = x+y;
    return s >= P ? s-P : s;
}
static uint32_t sub(uint32_t x, uint32_t y) {
    return x>=y ? x-y : P-(y-x);
}
static uint32_t mul(uint32_t x, uint32_t y) {
    uint64_t v = (uint64_t)x*y;
    return add((uint32_t)(v>>31), (uint32_t)v & P);
}
/* Return the affine x of [2^count]H only when it is finite with y = 0.
   Input x is the abscissa of an on-curve H on y²=x³+a*x²+b*x. */
uint32_t m31_kernel_x(uint32_t x, uint32_t a, uint32_t b, unsigned count) {
    uint32_t z = 1;
    for (unsigned i=0; i<count; ++i) {
        uint32_t xx=mul(x,x), xz=mul(x,z), bzz=mul(b,mul(z,z));
        uint32_t d=sub(xx,bzz);
        z=mul(add(add(xz,xz),add(xz,xz)),add(add(xx,mul(a,xz)),bzz));
        if (!z) return P;
        x=mul(d,d);
    }
    if (x && add(add(mul(x,x),mul(a,mul(x,z))),mul(b,mul(z,z)))) return P;
    if (!x || z==1) return x;
    uint32_t inv=1;
    for (uint32_t e=P-2;e;e>>=1) {
        if (e&1) inv=mul(inv,z);
        z=mul(z,z);
    }
    return mul(x,inv);
}
