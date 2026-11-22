#include <algorithm>
#include <array>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <random>
#include <vector>
using U = uint64_t;
constexpr U p = (U{1}<<31)-1;
constexpr size_t width = 64;
using Block = std::array<U,width>;
inline U mul(U a,U b) {
    U product=a*b, folded=(product&p)+(product>>31);
    return folded>=p ? folded-p : folded;
}
template<unsigned B> U ones(U x) {
    if constexpr (B==1) return x;
    else {
        U half=ones<B/2>(x), v=half;
        for(unsigned j=0;j<B/2;++j) v=mul(v,v);
        v=mul(v,half);
        if constexpr(B%2) v=mul(mul(v,v),x);
        return v;
    }
}
U inv(U x) {
    U t=ones<29>(x); t=mul(t,t); return mul(mul(t,t),x);
}
inline U unit(U x) {return x ? x : 1;}
__attribute__((noinline)) void individual(const Block& a,Block& out) {
    for(size_t i=0;i<width;++i) out[i]=inv(a[i]);
}
__attribute__((noinline)) void prefix(const Block& a,Block& out) {
    Block products;
    products[0]=unit(a[0]);
    for(size_t i=1;i<width;++i) products[i]=mul(products[i-1],unit(a[i]));
    U carry=inv(products.back());
    for(size_t i=width-1;i>0;--i) {
        out[i]=a[i] ? mul(products[i-1],carry) : 0;
        carry=mul(carry,unit(a[i]));
    }
    out[0]=a[0] ? carry : 0;
}
__attribute__((noinline)) void tree(const Block& a,Block& out) {
    std::array<U,2*width> nodes;
    for(size_t i=0;i<width;++i) nodes[width+i]=unit(a[i]);
    for(size_t level=width/2;level;level/=2)
        for(size_t i=level;i<2*level;++i) nodes[i]=mul(nodes[2*i],nodes[2*i+1]);
    nodes[1]=inv(nodes[1]);
    for(size_t level=1;level<width;level*=2)
        for(size_t i=level;i<2*level;++i) {
            U left=nodes[2*i], right=nodes[2*i+1], parent=nodes[i];
            nodes[2*i]=mul(parent,right); nodes[2*i+1]=mul(parent,left);
        }
    for(size_t i=0;i<width;++i) out[i]=a[i] ? nodes[width+i] : 0;
}
void check(const Block& a,const Block& out) {
    for(size_t i=0;i<width;++i) {
        assert(out[i]<p);
        assert(a[i] ? a[i]*out[i]%p==1 : out[i]==0);
    }
}
int main() {
    constexpr void (*methods[])(const Block&,Block&)={individual,prefix,tree};
    constexpr int orders[][3]={{0,1,2},{0,2,1},{1,2,0},{1,0,2},{2,0,1},{2,1,0}};
    std::mt19937_64 rng(291151);
    std::vector<Block> input(2048), output(input.size());
    for(U constant : {U{0},U{1},p-1}) {
        Block x{},y; x.fill(constant);
        for(auto method:methods) {method(x,y);check(x,y);}
    }
    for(int block=-1;block<36;++block) {
        for(auto& a:input) for(U& x:a) x=1+rng()%(p-1);
        if(block%2==1) for(auto& a:input) for(U& x:a) if((rng()&15)==0) x=0;
        for(int m:orders[(block+6)%6]) {
            auto start=std::chrono::steady_clock::now();
            for(size_t j=0;j<input.size();++j) methods[m](input[j],output[j]);
            auto ns=std::chrono::duration_cast<std::chrono::nanoseconds>(
                std::chrono::steady_clock::now()-start).count();
            for(size_t j=0;j<input.size();++j) check(input[j],output[j]);
            if(block>=0) std::cout<<block<<','<<m<<','<<ns<<'\n';
        }
    }
}
