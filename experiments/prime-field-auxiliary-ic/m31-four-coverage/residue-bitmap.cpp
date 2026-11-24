// The lower half stores one representative of each nonzero pair {a,-a}.
#include "side-kernel.hpp"
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <iostream>
#include <random>
#include <vector>

using Clock = std::chrono::steady_clock;
struct Table {
    std::vector<uint64_t> words;
#if defined(M31_ROTATE_TABLE) || defined(M31_TRIPLE_TABLE)
#ifdef M31_TRIPLE_TABLE
    static constexpr unsigned address_bits=27;
#else
    static constexpr unsigned address_bits=28;
#endif
    Table() : words(size_t(1)<<(address_bits-6)) {
        for(uint64_t y=1;y<=p/2;++y) {
            uint32_t r=y*y%p;
            if((r>>(address_bits+1))==0 && (r&1)) words[r>>7] |= uint64_t(1)<<((r>>1)&63);
        }
    }
    bool square(uint32_t a) const {
        if(a==0) return true;
        uint32_t left=((a<<1)&p)|(a>>30);
        uint32_t right=(a>>1)|((a&1)<<30);
        uint32_t marks=(a^right)&~(a^left);
#ifdef M31_TRIPLE_TABLE
        uint32_t left2=((left<<1)&p)|(left>>30);
        marks &= ~(a^left2);
        if(!marks) return reciprocity(a);
#endif
        unsigned bit=__builtin_ctz(marks);
        bool negate=(a>>bit)&1;
        uint32_t v=negate?(p^a):a;
        unsigned shift=bit+1;
        uint32_t rotated=(v>>shift)|((v<<(31-shift))&p);
        return bool((words[rotated>>7]>>((rotated>>1)&63))&1) != negate;
    }
#else
    Table() : words((size_t(p)/2+64)/64) {
        words[0]=1;
        for(uint64_t y=1;y<=p/2;++y) {
            uint32_t r=y*y%p;
            if(r<=p/2) words[r>>6] |= uint64_t(1)<<(r&63);
        }
    }
    bool square(uint32_t a) const {
        bool negate=a>p/2;
        uint32_t k=negate?p-a:a;
        return bool((words[k>>6]>>(k&63))&1) != negate;
    }
#endif
};

// Permute 31-bit inputs. The single excluded field word p maps to zero below.
uint32_t coordinate(uint32_t i) {
    i^=i>>15;
    i=(i*0x45d9f3bu)&p;
    i^=i>>13;
    i=(i*0x119de1f3u)&p;
    i^=i>>16;
    return i==p?0:i;
}

int main(int argc,char** argv) {
    if(argc!=2) return 1;
    unsigned seed=std::stoul(argv[1]);
    std::vector<Batch> hot(1024);
    std::vector<Labels> oracle(hot.size());
    for(size_t i=0;i<hot.size();++i) for(size_t j=0;j<32;++j) {
        unsigned x,b;
        if(!(std::cin>>x>>b) || x>=p || b>1) return 2;
        hot[i][j]=x;
        oracle[i][j]=b;
    }
    auto start=Clock::now();
    Table table;
    double build=std::chrono::duration<double>(Clock::now()-start).count();
    std::cerr<<"build_seconds,"<<build<<"\n";
    for(size_t i=0;i<hot.size();++i) for(size_t j=0;j<32;++j)
        if(table.square(rhs(hot[i][j]))!=oracle[i][j]) return 3;
    if(!table.square(0) || !table.square(1) || table.square(p-1)) return 4;
    std::mt19937 rng(seed);
    std::shuffle(hot.begin(),hot.end(),rng);
    std::puts("stream,round,method,ns_per_coordinate");
    for(bool fresh : {false,true}) {
        size_t n=fresh?131072:hot.size();
        std::vector<Batch> inputs(n);
        std::vector<Labels> scalar(n),neon(n);
        if(!fresh) inputs=hot;
        for(unsigned round=0;round<8;++round) {
            if(fresh) for(size_t i=0;i<n;++i) for(unsigned j=0;j<32;++j)
                inputs[i][j]=coordinate((seed%32)*33554432u+round*4194304u+i*32+j);
            for(unsigned k=0;k<2;++k) {
                bool cached=(round+k+seed)%2;
                start=Clock::now();
                if(cached) {
                    for(size_t i=0;i<n;++i) for(unsigned j=0;j<32;++j)
                        scalar[i][j]=table.square(rhs(inputs[i][j]));
                } else {
                    for(size_t i=0;i<n;++i) neon[i]=classify<1>(inputs[i]);
                }
                double ns=std::chrono::duration<double,std::nano>(Clock::now()-start).count();
                if(round>=2) std::printf("%s,%u,%s,%.4f\n",fresh?"fresh":"hot",round-2,
                    cached?"bitmap":"neon",ns/(32*n));
            }
            if(scalar!=neon) return 5;
        }
    }
}
