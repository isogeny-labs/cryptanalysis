// Compare three input contracts for one aggregate public character per orbit.
#include "side-kernel.hpp"
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <numeric>
#include <random>
#include <vector>

using Word=uint32_t;

constexpr Word mul(Word a,Word b) { return uint64_t(a)*b%p; }
constexpr Word add(Word a,Word b) { Word s=a+b; return s>=p?s-p:s; }
constexpr Word sub(Word a,Word b) { return a>=b?a-b:a+(p-b); }
Word power(Word x,Word n) {
    Word acc=1;
    while(n) { if(n&1) acc=mul(acc,x); x=mul(x,x); n>>=1; }
    return acc;
}
bool square(Word x) {
    Word v=x;
    for(unsigned k=0;k<30;++k) v=mul(v,v);
    return x==v;
}
struct Step { Word t,A,B; };
constexpr std::array<Step,5> steps={{{0,0,1},{2,6,8},{262150,786438,3145792},
  {135006214,403445766,562160130},{199756251,1939860868,1327400300}}};
constexpr std::array<Word,4> f={1330410815,368863965,1911999596,1606038711};
struct Row { std::array<Word,32> xs; Word terminal; bool expected; };

Word cubic(Word x) { return add(mul(add(mul(x,x),2),x),14); }
Word terminal_cubic(Word x) { return add(mul(add(mul(add(mul(f[0],x),f[1]),x),f[2]),x),f[3]); }

bool projective(Word x) {
    Word u=x,v=1;
    for(auto [t,A,B]:steps) {
        Word w=sub(u,mul(t,v));
        Word den=mul(w,v);
        u=add(add(mul(w,w),mul(A,den)),mul(B,mul(v,v)));
        v=den;
    }
    Word vv=mul(v,v);
    Word val=add(mul(add(mul(f[0],u),mul(f[1],v)),mul(u,u)),
                 mul(vv,add(mul(f[2],u),mul(f[3],v))));
    return square(mul(val,v));
}

template<unsigned method> __attribute__((noinline)) bool evaluate(const Row& row) {
    if constexpr(method==3) {
        auto labels=classify<3>(row.xs);
        unsigned parity=0;
        for(auto bit:labels) parity^=1-bit;
        return parity==0;
    }
    if constexpr(method==1) return projective(row.xs[0]);
    if constexpr(method==2) return square(terminal_cubic(row.terminal));
    Word prod=1;
    for(Word x:row.xs) prod=mul(prod,cubic(x));
    return square(prod);
}

#include "orbit-norm-batch.hpp"

int main(int argc,char** argv) {
    bool first=argc==5 && std::string(argv[3])=="first-batch";
    if(!first && argc!=3 && !(argc==4 && (std::string(argv[3])=="batch" || std::string(argv[3])=="check-batch"))) return 1;
    unsigned seed=std::stoul(argv[1]);
    std::ifstream in(argv[2]);
    std::vector<Row> rows(1024);
    for(auto& row:rows) {
        unsigned parity=0; Word prod=1;
        for(auto& x:row.xs) {
            unsigned bit;
            if(!(in>>x>>bit) || x>=p || bit>1 || !cubic(x)) return 2;
            parity^=1-bit;
            prod=mul(prod,cubic(x));
        }
        Word y=row.xs[0];
        for(auto [t,A,B]:steps) {
            Word w=sub(y,t);
            if(!w) return 3;
            y=add(add(w,A),mul(B,power(w,p-2)));
        }
        if(terminal_cubic(y)!=prod) return 4;
        row.terminal=y;
        row.expected=parity==0;
    }
    std::mt19937 gen(seed);
    std::shuffle(rows.begin(),rows.end(),gen);
    if(argc==4 && std::string(argv[3])=="check-batch") {
        std::vector<uint8_t> bits(rows.size());
        for(unsigned index=0;index<32;++index) {
            for(auto& row:rows) std::rotate(row.xs.begin(),row.xs.begin()+1,row.xs.end());
            for(size_t i=0;i<rows.size();i+=32)
                orbit_batch::vector_batch<true>(rows.data()+i,bits.data()+i);
            for(size_t i=0;i<rows.size();++i) if(bits[i]!=rows[i].expected) return 5;
        }
        std::cout<<32*rows.size()<<" orbit starts matched\n";
        return 0;
    }
    if(first) {
        unsigned method=std::stoul(argv[4]);
        if(method>=4) return 1;
        return batch_bench(rows,seed,method);
    }
    if(argc==4) return batch_bench(rows,seed);
    std::vector<uint8_t> result(rows.size());
    std::array<unsigned,4> order={0,1,2,3};
    for(unsigned k=0;k<seed%24;++k) std::next_permutation(order.begin(),order.end());
    for(auto method:order) {
        auto fn=std::array{evaluate<0>,evaluate<1>,evaluate<2>,evaluate<3>}[method];
        auto start=std::chrono::steady_clock::now();
        for(unsigned pass=0;pass<32;++pass) {
            for(size_t i=0;i<rows.size();++i) result[i]=fn(rows[i]);
            asm volatile("" : : "r"(result.data()) : "memory");
        }
        auto elapsed=std::chrono::duration<double,std::nano>(std::chrono::steady_clock::now()-start);
        for(size_t i=0;i<rows.size();++i) if(result[i]!=rows[i].expected) return 5;
        std::cout<<method<<','<<elapsed.count()/(32*rows.size())<<'\n';
    }
}
