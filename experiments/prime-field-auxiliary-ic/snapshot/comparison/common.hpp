#pragma once
// Three-point projected index calculus over F_(2^61-1), using only public.txt.
// Relation search uses a table of pair sums, not a Groebner-basis solver.
#include <algorithm>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <stdexcept>
#include <unordered_map>
#include <vector>
using U = uint64_t;
#ifndef FIELD_BITS
#define FIELD_BITS 61
#endif
constexpr U FP = (1ULL << FIELD_BITS)-1;
using Wide = __uint128_t;
U N, A, B;
U fa(U a,U b) { U c=a+b; return c>=FP?c-FP:c; }
U fs(U a,U b) { return a>=b?a-b:a+FP-b; }
U fm(U a,U b) { Wide w=Wide(a)*b; U v=U(w&FP)+U(w>>FIELD_BITS); return v>=FP?v-FP:v; }
U nm(U a,U b) { return Wide(a)*b%N; }
U fpow(U a,U k) { U r=1; for(;k;k>>=1,a=fm(a,a)) if(k&1) r=fm(r,a); return r; }
U npow(U a,U k) { U r=1; for(;k;k>>=1,a=nm(a,a)) if(k&1) r=nm(r,a); return r; }
struct Point { U x=0,y=0; bool inf=true; };
bool eq(Point P,Point Q) { return P.inf==Q.inf && (P.inf||(P.x==Q.x&&P.y==Q.y)); }
Point neg(Point P) { if(!P.inf&&P.y) P.y=FP-P.y; return P; }
Point add(Point P,Point Q) {
    if(P.inf) return Q;
    if(Q.inf) return P;
    U num,den;
    if(P.x==Q.x) {
        if(fa(P.y,Q.y)==0) return {};
        num=fa(fm(3,fm(P.x,P.x)),A); den=fa(P.y,P.y);
    } else { num=fs(Q.y,P.y); den=fs(Q.x,P.x); }
    U slope=fm(num,fpow(den,FP-2));
    U x=fs(fs(fm(slope,slope),P.x),Q.x);
    return {x,fs(fm(slope,fs(P.x,x)),P.y),false};
}
Point mul(U k,Point P) { Point R; for(;k;k>>=1,P=add(P,P)) if(k&1) R=add(R,P); return R; }
bool oncurve(Point P) { return P.inf||fm(P.y,P.y)==fa(fa(fm(fm(P.x,P.x),P.x),fm(A,P.x)),B); }
U key(Point P) { return P.inf?UINT64_MAX:(P.x<<1)|(P.y&1); }
struct Hasher { size_t operator()(U x) const {
    x+=0x9e3779b97f4a7c15ULL;
    x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;
    x=(x^(x>>27))*0x94d049bb133111ebULL;
    return x^(x>>31);
} };
// Batch inversions: one inversion for all generic additions with fixed P.
std::vector<Point> add_batch(Point P,const std::vector<Point>& V,size_t first) {
    size_t len=V.size()-first;
    std::vector<U> prefix(len),den(len);
    std::vector<Point> out(len);
    U product=1;
    for(size_t j=0;j<len;j++) {
        prefix[j]=product;
        Point Q=V[first+j];
        if(P.inf||Q.inf||P.x==Q.x) den[j]=0;
        else { den[j]=fs(Q.x,P.x); product=fm(product,den[j]); }
    }
    U inverse=fpow(product,FP-2);
    for(size_t jj=len;jj>0;jj--) {
        size_t j=jj-1; Point Q=V[first+j];
        if(den[j]==0) { out[j]=add(P,Q); continue; }
        U inv=fm(inverse,prefix[j]); inverse=fm(inverse,den[j]);
        U slope=fm(fs(Q.y,P.y),inv);
        U x=fs(fs(fm(slope,slope),P.x),Q.x);
        out[j]={x,fs(fm(slope,fs(P.x,x)),P.y),false};
    }
    return out;
}
