// The lower half stores one representative of each nonzero pair {a,-a}.
#include "side-kernel.hpp"
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <iostream>
#include <numeric>
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
#ifdef M31_VECTOR_BUILD
    static constexpr bool default_vector_build=true;
#else
    static constexpr bool default_vector_build=false;
#endif
    explicit Table(bool vector_build=default_vector_build) : words(size_t(1)<<(address_bits-6)) {
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
        if(vector_build) {
            build_vectors();
        } else {
            for(uint64_t y=1;y<=p/2;++y) mark(uint32_t(y*y%p));
        }
    }

    void mark(uint32_t r) {
        if((r>>(address_bits+1))==0 && (r&1))
            words[r>>7] |= uint64_t(1)<<((r>>1)&63);
#ifdef M31_PACK_RUNS
        if((r>>27)==1 && (r&1)) {
            auto address=packed_address(r);
            if(address<entries) secondary[address>>6] |= uint64_t(1)<<(address&63);
        }
#endif
    }

    void build_vectors() {
        // Zero never passes the odd filter. Including it gives full 16-root blocks.
        constexpr unsigned width=16;
#ifdef M31_PACK_RUNS
        constexpr unsigned accepted_bits=28;
#else
        constexpr unsigned accepted_bits=address_bits+1;
#endif
        const auto prime=vdupq_n_u32(p);
        const auto filter=vdupq_n_u32(~((1u<<accepted_bits)-1)|1u);
        const uint32x4_t weights={1,2,4,8};
        uint32x4_t y={0,1,2,3};
        for(uint32_t base=0;base<=p/2;base+=width) {
            uint32_t residues[width];
            uint32x4_t flags=vdupq_n_u32(0);
            for(unsigned group=0;group<width/4;++group) {
                auto sy=vreinterpretq_s32_u32(y);
                auto high=vreinterpretq_u32_s32(vqdmulhq_s32(sy,sy));
                auto sum=vaddq_u32(high,vandq_u32(vmulq_u32(y,y),prime));
                auto r=vminq_u32(sum,vsubq_u32(sum,prime));
                vst1q_u32(residues+4*group,r);
                auto hit=vceqq_u32(vandq_u32(r,filter),vdupq_n_u32(1));
#if defined(M31_PACK_RUNS) && defined(M31_VECTOR_RUN_FILTER)
                // In the secondary range discard forbidden runs within each nine-bit block.
                auto equal=vmvnq_u32(veorq_u32(r,vshrq_n_u32(r,1)));
                auto three=vandq_u32(equal,vandq_u32(vshrq_n_u32(equal,1),vshrq_n_u32(equal,2)));
                auto valid=vceqzq_u32(vandq_u32(three,vdupq_n_u32(0x1f8fc7e)));
                auto primary=vcltq_u32(r,vdupq_n_u32(1u<<27));
                hit=vandq_u32(hit,vorrq_u32(primary,valid));
#endif
                flags=vorrq_u32(flags,vandq_u32(hit,vshlq_u32(weights,vdupq_n_s32(4*group))));
                y=vaddq_u32(y,vdupq_n_u32(4));
            }
            unsigned mask=vaddvq_u32(flags);
            while(mask) {
                mark(residues[__builtin_ctz(mask)]);
                mask &= mask-1;
            }
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

#ifdef M31_COORDINATE_CACHE
// Cache a declared working set of 1024 batches. An absent key recomputes the batch.
struct CoordinateCache {
    static constexpr unsigned capacity=1u<<17;
    std::vector<uint32_t> slots=std::vector<uint32_t>(capacity,p);
    unsigned probe(uint32_t key) const {
        unsigned i=(key*2654435761u)>>(32-17);
        while ((slots[i]&p)!=key && slots[i]!=p) i=(i+1)&(capacity-1);
        return i;
    }
    explicit CoordinateCache(const std::vector<Batch>& inputs) {
        if(inputs.size()>capacity/64) std::abort();
        for(const auto& batch:inputs) {
            auto labels=classify<3>(batch);
            for(unsigned j=0;j<32;++j)
                slots[probe(batch[j])]=batch[j]|(uint32_t(labels[j])<<31);
        }
    }
    Labels lookup(const Batch& batch) const {
        Labels labels{};
        for(unsigned j=0;j<32;++j) {
            uint32_t word=slots[probe(batch[j])];
            if(word==p) return classify<3>(batch);
            labels[j]=word>>31;
        }
        return labels;
    }
};
#endif

int main(int argc,char** argv) {
#ifdef M31_COORDINATE_CACHE
    if(argc!=2 && argc!=4) return 1;
#else
    if(argc!=2) return 1;
#endif
#if defined(M31_ROTATE_TABLE) || defined(M31_TRIPLE_TABLE) || defined(M31_QUAD_TABLE)
    const std::string command=argv[1];
    if(command=="--check-build") {
        Table scalar(false), vector(true);
        if(scalar.words!=vector.words) return 7;
#ifdef M31_PACK_RUNS
        if(scalar.secondary!=vector.secondary || scalar.ranks!=vector.ranks) return 7;
#endif
        std::puts("build arrays matched");
        return 0;
    }
    if(command=="--build-scalar" || command=="--build-vector") {
        auto start=Clock::now();
        Table table(command=="--build-vector");
        double seconds=std::chrono::duration<double>(Clock::now()-start).count();
        uint64_t count=0;
        for(auto word:table.words) count+=__builtin_popcountll(word);
#ifdef M31_PACK_RUNS
        for(auto word:table.secondary) count+=__builtin_popcountll(word);
#endif
        std::printf("%.9f,%llu\n",seconds,(unsigned long long)count);
        return 0;
    }
#endif
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
#if defined(M31_REGISTER_BIC) && !defined(M31_COMPARE_FOLD)
    constexpr int reference_arm=3;
    constexpr auto reference_name="neon-register";
#else
    constexpr int reference_arm=1;
    constexpr auto reference_name="neon";
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
#ifdef M31_COORDINATE_CACHE
    if(argc==4) {
        const std::string arm=argv[2];
        const unsigned passes=std::stoul(argv[3]);
        if((arm!="cache" && arm!="arithmetic") || !passes) return 2;
        std::vector<unsigned> order(hot.size());
        std::iota(order.begin(),order.end(),0);
        std::mt19937 shuffle(seed);
        std::shuffle(order.begin(),order.end(),shuffle);
        std::vector<Labels> output(hot.size());
        auto consume=[&](auto classify_batch) {
            for(unsigned pass=0;pass<passes;++pass) {
                for(auto i:order) output[i]=classify_batch(hot[i]);
                asm volatile("" : : "r"(output.data()) : "memory");
            }
        };
        auto begin=Clock::now();
        if(arm=="cache") {
            CoordinateCache cache(hot);
            consume([&](const Batch& x){return cache.lookup(x);});
        } else {
            consume([](const Batch& x){return classify<3>(x);});
        }
        auto elapsed=std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-begin);
        if(output!=oracle) return 3;
        std::cout<<elapsed.count()<<"\n";
        return 0;
    }
#endif
    auto start=Clock::now();
#ifdef M31_COMPARE_FOLD
    constexpr auto candidate_name="complement";
    for(size_t i=0;i<hot.size();++i)
        if(classify<3>(hot[i])!=oracle[i]) return 3;
#elif defined(M31_COORDINATE_CACHE)
    constexpr auto candidate_name="coordinate-cache";
    CoordinateCache cache(hot);
    double build=std::chrono::duration<double>(Clock::now()-start).count();
    std::cerr<<"build_seconds,"<<build<<"\n";
    for(size_t i=0;i<hot.size();++i)
        if(cache.lookup(hot[i])!=oracle[i]) return 3;
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
#elif defined(M31_COORDINATE_CACHE)
                    for(size_t i=0;i<n;++i) scalar[i]=cache.lookup(inputs[i]);
#else
                    for(size_t i=0;i<n;++i) for(unsigned j=0;j<32;++j)
                        scalar[i][j]=table.square(rhs(inputs[i][j]));
#endif
                } else {
                    for(size_t i=0;i<n;++i) neon[i]=classify<reference_arm>(inputs[i]);
                }
                double ns=std::chrono::duration<double,std::nano>(Clock::now()-start).count();
                if(round>=2) std::printf("%s,%u,%s,%.4f\n",fresh?"fresh":"hot",round-2,
                    cached?candidate_name:reference_name,ns/(32*n));
            }
            if(scalar!=neon) return 5;
        }
    }
}
