// Full-width reference arithmetic shared by CUDA, Metal and host emulation.
// Five little-endian 32-bit limbs hold the complete 131-bit fields AND tags.
// No floating point, native 128-bit integers, truncated point keys or folding.
#ifndef CERTICOM_ARITHMETIC_H
#define CERTICOM_ARITHMETIC_H
#if defined(__CUDACC__)
#define CC_HD __host__ __device__ inline
#else
#define CC_HD inline
#endif
typedef unsigned int cc_u32;
struct CcInteger { cc_u32 v[5]; };
struct CcPoint { CcInteger x, y; cc_u32 infinity; };
struct CcCurve {
    cc_u32 binary;
    CcInteger modulus, a, b, order;
    CcPoint generator, target;
};
struct CcWalk { CcPoint point; CcInteger a, b; };
struct CcRho {
    CcWalk tortoise, hare;
    cc_u32 iterations_lo, iterations_hi, collision;
};

CC_HD CcInteger cc_zero() { CcInteger r = {{0,0,0,0,0}}; return r; }
CC_HD CcInteger cc_one() { CcInteger r = {{1,0,0,0,0}}; return r; }
CC_HD bool cc_eq(CcInteger a, CcInteger b) {
    cc_u32 diff = 0;
    for (int i = 0; i < 5; ++i) diff |= a.v[i] ^ b.v[i];
    return diff == 0;
}
CC_HD bool cc_is_zero(CcInteger a) { return cc_eq(a, cc_zero()); }
CC_HD int cc_cmp(CcInteger a, CcInteger b) {
    for (int i = 4; i >= 0; --i)
        if (a.v[i] != b.v[i]) return a.v[i] > b.v[i] ? 1 : -1;
    return 0;
}
CC_HD CcInteger cc_xor(CcInteger a, CcInteger b) {
    for (int i = 0; i < 5; ++i) a.v[i] ^= b.v[i];
    return a;
}
// Callers keep integer sums below 2^132, so the 160-bit container cannot wrap.
CC_HD CcInteger cc_add(CcInteger a, CcInteger b) {
    CcInteger r; cc_u32 carry = 0;
    for (int i = 0; i < 5; ++i) {
        cc_u32 s = a.v[i] + b.v[i], t = s + carry;
        carry = (s < a.v[i]) | (t < s); r.v[i] = t;
    }
    return r;
}
CC_HD CcInteger cc_sub(CcInteger a, CcInteger b) {
    CcInteger r; cc_u32 borrow = 0;
    for (int i = 0; i < 5; ++i) {
        cc_u32 d = a.v[i] - b.v[i], t = d - borrow;
        borrow = (a.v[i] < b.v[i]) | (d < borrow); r.v[i] = t;
    }
    return r;
}
CC_HD CcInteger cc_shl(CcInteger a) {
    for (int i = 4; i > 0; --i) a.v[i] = (a.v[i] << 1) | (a.v[i-1] >> 31);
    a.v[0] <<= 1; return a;
}
CC_HD CcInteger cc_shr(CcInteger a) {
    for (int i = 0; i < 4; ++i) a.v[i] = (a.v[i] >> 1) | (a.v[i+1] << 31);
    a.v[4] >>= 1; return a;
}
CC_HD CcInteger cc_addmod(CcInteger a, CcInteger b, CcInteger n) {
    CcInteger r = cc_add(a,b); return cc_cmp(r,n) >= 0 ? cc_sub(r,n) : r;
}
CC_HD CcInteger cc_submod(CcInteger a, CcInteger b, CcInteger n) {
    return cc_cmp(a,b) >= 0 ? cc_sub(a,b) : cc_sub(n,cc_sub(b,a));
}
CC_HD CcInteger cc_mulmod(CcInteger a, CcInteger b, CcInteger n) {
    CcInteger r = cc_zero();
    for (int i = 0; i < 131; ++i) {
        if ((b.v[i/32] >> (i%32)) & 1u) r = cc_addmod(r,a,n);
        a = cc_addmod(a,a,n);
    }
    return r;
}
CC_HD CcInteger cc_invmod(CcInteger a, CcInteger n) {
    if (cc_is_zero(a)) return cc_zero();
    CcInteger u=a, v=n, x=cc_one(), y=cc_zero();
    // Binary extended Euclid, with coefficient halving modulo the odd prime.
    while (!cc_eq(u,cc_one()) && !cc_eq(v,cc_one())) {
        while (!(u.v[0]&1u)) {
            u=cc_shr(u); x=cc_shr((x.v[0]&1u) ? cc_add(x,n) : x);
        }
        while (!(v.v[0]&1u)) {
            v=cc_shr(v); y=cc_shr((y.v[0]&1u) ? cc_add(y,n) : y);
        }
        if (cc_cmp(u,v)>=0) {u=cc_sub(u,v); x=cc_submod(x,y,n);}
        else {v=cc_sub(v,u); y=cc_submod(y,x,n);}
    }
    return cc_eq(u,cc_one()) ? x : y;
}
CC_HD CcInteger cc_gf_shift(CcInteger a, CcInteger polynomial) {
    a=cc_shl(a); if (a.v[4]&8u) a=cc_xor(a,polynomial); return a;
}
CC_HD CcInteger cc_gf_mul(CcInteger a, CcInteger b, CcInteger polynomial) {
    CcInteger r=cc_zero();
    for (int i=0;i<131;++i) {
        if ((b.v[i/32]>>(i%32))&1u) r=cc_xor(r,a);
        a=cc_gf_shift(a,polynomial);
    }
    return r;
}
CC_HD int cc_degree(CcInteger a) {
    for (int i=159;i>=0;--i) if ((a.v[i/32]>>(i%32))&1u) return i;
    return -1;
}
CC_HD CcInteger cc_gf_inv(CcInteger a, CcInteger polynomial) {
    if (cc_is_zero(a)) return cc_zero();
    CcInteger u=a,v=polynomial,x=cc_one(),y=cc_zero();
    while (!cc_eq(u,cc_one())) {
        int j=cc_degree(u)-cc_degree(v);
        if (j<0) {
            CcInteger t=u; u=v; v=t; t=x; x=y; y=t; j=-j;
        }
        CcInteger shifted=v, coefficient=y;
        for (int k=0;k<j;++k) {
            shifted=cc_shl(shifted);
            coefficient=cc_gf_shift(coefficient,polynomial);
        }
        u=cc_xor(u,shifted); x=cc_xor(x,coefficient);
    }
    return x;
}
CC_HD CcInteger cc_fadd(CcCurve c,CcInteger a,CcInteger b) {
    return c.binary ? cc_xor(a,b) : cc_addmod(a,b,c.modulus);
}
CC_HD CcInteger cc_fsub(CcCurve c,CcInteger a,CcInteger b) {
    return c.binary ? cc_xor(a,b) : cc_submod(a,b,c.modulus);
}
CC_HD CcInteger cc_fmul(CcCurve c,CcInteger a,CcInteger b) {
    return c.binary ? cc_gf_mul(a,b,c.modulus) : cc_mulmod(a,b,c.modulus);
}
CC_HD CcInteger cc_finv(CcCurve c,CcInteger a) {
    return c.binary ? cc_gf_inv(a,c.modulus) : cc_invmod(a,c.modulus);
}
CC_HD CcPoint cc_infinity() {
    CcPoint p; p.x=cc_zero();p.y=cc_zero();p.infinity=1;return p;
}
CC_HD bool cc_point_eq(CcPoint p,CcPoint q) {
    if (p.infinity || q.infinity) return p.infinity==q.infinity;
    return cc_eq(p.x,q.x) && cc_eq(p.y,q.y);
}
CC_HD CcPoint cc_point_add(CcCurve c,CcPoint p,CcPoint q) {
    if (p.infinity) return q;
    if (q.infinity) return p;
    bool same_x=cc_eq(p.x,q.x);
    CcInteger slope;
    if (c.binary) {
        if (same_x) {
            if (!cc_eq(p.y,q.y) || cc_is_zero(p.x)) return cc_infinity();
            slope=cc_fadd(c,p.x,cc_fmul(c,p.y,cc_finv(c,p.x)));
        } else {
            slope=cc_fmul(c,cc_fadd(c,p.y,q.y),cc_finv(c,cc_fadd(c,p.x,q.x)));
        }
        CcPoint r; r.infinity=0;
        r.x=cc_fadd(c,cc_fadd(c,cc_fmul(c,slope,slope),slope),c.a);
        if (same_x) {
            r.y=cc_fadd(c,cc_fmul(c,p.x,p.x),cc_fmul(c,cc_fadd(c,slope,cc_one()),r.x));
        } else {
            r.x=cc_fadd(c,r.x,cc_fadd(c,p.x,q.x));
            r.y=cc_fadd(c,cc_fadd(c,cc_fmul(c,slope,cc_fadd(c,p.x,r.x)),r.x),p.y);
        }
        return r;
    }
    if (same_x) {
        if (!cc_eq(p.y,q.y) || cc_is_zero(p.y)) return cc_infinity();
        CcInteger x2=cc_fmul(c,p.x,p.x);
        slope=cc_fmul(c,cc_fadd(c,cc_fadd(c,cc_fadd(c,x2,x2),x2),c.a),
                       cc_finv(c,cc_fadd(c,p.y,p.y)));
    } else {
        slope=cc_fmul(c,cc_fsub(c,q.y,p.y),cc_finv(c,cc_fsub(c,q.x,p.x)));
    }
    CcPoint r;r.infinity=0;
    r.x=cc_fsub(c,cc_fsub(c,cc_fmul(c,slope,slope),p.x),q.x);
    r.y=cc_fsub(c,cc_fmul(c,slope,cc_fsub(c,p.x,r.x)),p.y);
    return r;
}
CC_HD CcPoint cc_point_mul(CcCurve c,CcPoint p,CcInteger k) {
    CcPoint r=cc_infinity();
    for (int i=130;i>=0;--i) {
        r=cc_point_add(c,r,r);
        if ((k.v[i/32]>>(i%32))&1u) r=cc_point_add(c,r,p);
    }
    return r;
}
CC_HD CcWalk cc_walk_step(CcCurve c,CcWalk w) {
    cc_u32 hash=2166136261u;
    for (int i=0;i<5;++i) {
        hash=(hash^w.point.x.v[i])*16777619u;
        hash=(hash^w.point.y.v[i])*16777619u;
    }
    hash=(hash^w.point.infinity)*16777619u;
    cc_u32 bucket=hash%3u;
    if (bucket==0) {
        w.point=cc_point_add(c,w.point,c.generator);
        w.a=cc_addmod(w.a,cc_one(),c.order);
    } else if (bucket==1) {
        w.point=cc_point_add(c,w.point,c.target);
        w.b=cc_addmod(w.b,cc_one(),c.order);
    } else {
        w.point=cc_point_add(c,w.point,w.point);
        w.a=cc_addmod(w.a,w.a,c.order);w.b=cc_addmod(w.b,w.b,c.order);
    }
    return w;
}
CC_HD CcRho cc_rho_advance(CcCurve c,CcRho r,cc_u32 steps) {
    for (cc_u32 i=0;i<steps && !r.collision;++i) {
        r.tortoise=cc_walk_step(c,r.tortoise);
        r.hare=cc_walk_step(c,cc_walk_step(c,r.hare));
        if (++r.iterations_lo==0) ++r.iterations_hi;
        if (cc_point_eq(r.tortoise.point,r.hare.point)) r.collision=1;
    }
    return r;
}
#endif
