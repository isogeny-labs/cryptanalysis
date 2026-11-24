// The lower half stores one representative of each nonzero pair {a,-a}.
#include "side-kernel.hpp"
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <iostream>
#include <random>
#include <vector>

#if (defined(M31_PACK_RUNS) || defined(M31_REMAP_THREE)) && !defined(M31_QUAD_TABLE)
#error "Four-run fallback requires M31_QUAD_TABLE"
#endif
#if defined(M31_PACK_RUNS) && defined(M31_REMAP_THREE)
#error "Select only one four-run fallback"
#endif

using Clock = std::chrono::steady_clock;
struct Table {
    std::vector<uint64_t> words;
#if defined(M31_ROTATE_TABLE) || defined(M31_TRIPLE_TABLE) || defined(M31_QUAD_TABLE)
#if defined(M31_QUAD_TABLE)
    static constexpr unsigned address_bits=26;
#elif defined(M31_TRIPLE_TABLE)
    static constexpr unsigned address_bits=27;
#else
    static constexpr unsigned address_bits=28;
#endif
#ifdef M31_PACK_RUNS
    // Each nine-bit block is a walk avoiding 0000 and 1111.
    static constexpr unsigned radix=298;
    static constexpr unsigned entries=radix*radix*(radix/2);
    std::array<uint16_t,512> ranks{};
    std::vector<uint64_t> secondary=std::vector<uint64_t>((entries+63)/64);

    // The high three bits are zero and bit 27 is one. Drop the low one
    // and rank the remaining three blocks; the high rank is in [149,298).
    uint32_t packed_address(uint32_t r) const {
        unsigned a=ranks[(r>>1)&511], b=ranks[(r>>10)&511], c=ranks[r>>19];
        if(a>=radix || b>=radix || c>=radix || c<radix/2) return entries;
        return ((c-radix/2)*radix+b)*radix+a;
    }
#endif
    Table() : words(size_t(1)<<(address_bits-6)) {
#ifdef M31_PACK_RUNS
        unsigned next=0;
        for(unsigned block=0;block<512;++block) {
            bool valid=true;
            for(unsigned k=0;k<6;++k) {
                unsigned nibble=(block>>k)&15;
                if(nibble==0 || nibble==15) valid=false;
            }
            ranks[block]=valid?next++:radix;
        }
        if(next!=radix) std::abort();
#endif
        for(uint64_t y=1;y<=p/2;++y) {
            uint32_t r=y*y%p;
            if((r>>(address_bits+1))==0 && (r&1)) words[r>>7] |= uint64_t(1)<<((r>>1)&63);
#ifdef M31_PACK_RUNS
            if((r>>27)==1 && (r&1)) {
                auto address=packed_address(r);
                if(address<entries) secondary[address>>6] |= uint64_t(1)<<(address&63);
            }
#endif
        }
    }
    template<bool four=true>
    static uint32_t markers(uint32_t a) {
        uint32_t left=((a<<1)&p)|(a>>30);
        uint32_t right=(a>>1)|((a&1)<<30);
        uint32_t marks=(a^right)&~(a^left);
#if defined(M31_TRIPLE_TABLE) || defined(M31_QUAD_TABLE)
        uint32_t left2=((left<<1)&p)|(left>>30);
        marks &= ~(a^left2);
#endif
#ifdef M31_QUAD_TABLE
        uint32_t left3=((left2<<1)&p)|(left2>>30);
        if constexpr (four) marks &= ~(a^left3);
#endif
        return marks;
    }
    bool square(uint32_t a) const {
        if(a==0) return true;
        uint32_t marks=markers(a);
        bool flip=false;
#ifdef M31_PACK_RUNS
        bool second=!marks;
        if(second) marks=markers<false>(a);
#endif
#if defined(M31_QUAD_TABLE) && defined(M31_REMAP_THREE)
        if(!marks) {
            // Three is a nonsquare in M31, so reverse this character at return.
            a=uint64_t(a)*3%p;
            marks=markers(a);
            flip=true;
        }
#endif
#if defined(M31_TRIPLE_TABLE) || defined(M31_QUAD_TABLE)
        if(!marks) return reciprocity(a)!=flip;
#endif
        unsigned bit=__builtin_ctz(marks);
        bool negate=(a>>bit)&1;
        uint32_t v=negate?(p^a):a;
        unsigned shift=bit+1;
        uint32_t rotated=(v>>shift)|((v<<(31-shift))&p);
#ifdef M31_PACK_RUNS
        if(second) {
            auto address=packed_address(rotated);
            if(address==entries) std::abort();
            return bool((secondary[address>>6]>>(address&63))&1) != negate;
        }
#endif
        return bool((words[rotated>>7]>>((rotated>>1)&63))&1) != (negate != flip);
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
#ifdef M31_PACK_RUNS
    if(std::string(argv[1])=="--exhaustive") {
        Table table;
        std::vector<uint64_t> reference((uint64_t(p)+63)/64);
        for(uint64_t y=0;y<=p/2;++y) {
            uint32_t r=y*y%p;
            reference[r>>6] |= uint64_t(1)<<(r&63);
        }
        for(uint32_t a=0;a<p;++a) {
            if(table.square(a)!=bool((reference[a>>6]>>(a&63))&1)) {
                std::cerr<<"mismatch at "<<a<<"\n";
                return 6;
            }
        }
        std::cout<<p<<" inputs matched\n";
        return 0;
    }
#endif
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
#ifdef M31_COMPARE_FOLD
    constexpr auto candidate_name="complement";
    for(size_t i=0;i<hot.size();++i)
        if(classify<3>(hot[i])!=oracle[i]) return 3;
#else
    constexpr auto candidate_name="bitmap";
    Table table;
    double build=std::chrono::duration<double>(Clock::now()-start).count();
    std::cerr<<"build_seconds,"<<build<<"\n";
    for(size_t i=0;i<hot.size();++i) for(size_t j=0;j<32;++j)
        if(table.square(rhs(hot[i][j]))!=oracle[i][j]) return 3;
    if(!table.square(0) || !table.square(1) || table.square(p-1)) return 4;
#endif
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
#ifdef M31_COMPARE_FOLD
                    for(size_t i=0;i<n;++i) scalar[i]=classify<3>(inputs[i]);
#else
                    for(size_t i=0;i<n;++i) for(unsigned j=0;j<32;++j)
                        scalar[i][j]=table.square(rhs(inputs[i][j]));
#endif
                } else {
                    for(size_t i=0;i<n;++i) neon[i]=classify<1>(inputs[i]);
                }
                double ns=std::chrono::duration<double,std::nano>(Clock::now()-start).count();
                if(round>=2) std::printf("%s,%u,%s,%.4f\n",fresh?"fresh":"hot",round-2,
                    cached?candidate_name:"neon",ns/(32*n));
            }
            if(scalar!=neon) return 5;
        }
    }
}
