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
static uint32_t inverse_power(uint32_t value) {
    uint32_t inv=1;
    for (uint32_t e=P-2;e;e>>=1) {
        if (e&1) inv=mul(inv,value);
        value=mul(value,value);
    }
    return inv;
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
    return mul(x,inverse_power(z));
}

/* Extended Euclidean inverse on nonzero canonical inputs. All coefficients
   are bounded in magnitude by P and intermediates use signed 64-bit words. */
static uint32_t inverse_euclid(uint32_t value) {
    uint32_t a = P, b = value;
    int64_t u = 0, v = 1;
    while (b) {
        uint32_t q = a/b, rem = a-q*b;
        int64_t next = u-(int64_t)q*v;
        a=b; b=rem; u=v; v=next;
    }
    return (uint32_t)(u<0 ? u+P : u);
}

static uint32_t affine(uint32_t x, uint32_t y, uint32_t a, uint32_t b,
                       unsigned count, int euclid) {
    for (unsigned i=0; i<count; ++i) {
        if (!y) return P;
        uint32_t xx=mul(x,x), ax=mul(a,x);
        uint32_t numerator=add(add(xx,add(xx,xx)),add(b,add(ax,ax)));
        uint32_t denominator=add(y,y);
        uint32_t slope=mul(numerator,euclid ? inverse_euclid(denominator) : inverse_power(denominator));
        uint32_t next=sub(sub(mul(slope,slope),a),add(x,x));
        y=sub(mul(slope,sub(x,next)),y);
        x=next;
    }
    return y ? P : x;
}

uint32_t m31_affine_power(uint32_t x, uint32_t y, uint32_t a, uint32_t b, unsigned count) {
    return affine(x,y,a,b,count,0);
}
uint32_t m31_affine_euclid(uint32_t x, uint32_t y, uint32_t a, uint32_t b, unsigned count) {
    return affine(x,y,a,b,count,1);
}
