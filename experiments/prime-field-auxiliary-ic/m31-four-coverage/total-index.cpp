// clang++ -std=c++17 -O3 -mcpu=native index.cpp -o index
// stdin: 4096 rows of 17 distinct canonical public coordinates, in original order.
#include <algorithm>
#include <array>
#include <chrono>
#include <type_traits>
#include <cstdlib>
#include <cstdint>
#include <iostream>
#include <random>
#include <unordered_map>
#include <vector>
using Key = std::uint64_t;
struct Point { Key x=0,y=0; bool inf=false; };
using Base = std::array<Point,17>;
constexpr size_t miss = 17;
constexpr Key prime = 2147483647;
size_t scan(const Base& base, Key x) {
    for (size_t i=0; i<base.size(); ++i) if (base[i].x == x) return i;
    return miss;
}

struct XorIndex {
    std::array<unsigned char,128> index{};
    struct Term { unsigned bit,mask; };
    std::array<Term,24> terms{};
    unsigned term_count=0;
    explicit XorIndex(const Base& base,bool stop) {
        std::array<unsigned,17> labels{};
        for(unsigned i=0;i<17;++i) labels[i]=base[i].x & 127;
        for(unsigned b=7;b<31;++b) {
            std::array<bool,128> low{}, high{};
            bool overlaps=false, unique=true;
            for(unsigned i=0;i<17;++i) {
                bool up=(base[i].x>>b)&1;
                auto& part=up?high:low;
                auto& other=up?low:high;
                overlaps |= other[labels[i]];
                unique &= !part[labels[i]] && !other[labels[i]];
                part[labels[i]]=true;
            }
            if(stop && unique) break;
            if(!overlaps) continue;
            unsigned mask=1;
            for(;mask<128;++mask) {
                bool ok=true;
                for(unsigned i=0;i<17;++i)
                    if(((base[i].x>>b)&1) && low[labels[i]^mask]) {ok=false;break;}
                if(ok) break;
            }
            if(mask==128) std::abort();
            terms[term_count++]={b,mask};
            for(unsigned i=0;i<17;++i)
                if((base[i].x>>b)&1) labels[i]^=mask;
        }
        index.fill(miss);
        for(unsigned i=0;i<17;++i) {
            if(index[labels[i]]!=miss) std::abort();
            index[labels[i]]=i;
        }
    }
    size_t lookup(const Base& base,Key x) const {
        unsigned label=x&127;
        for(unsigned j=0;j<term_count;++j)
            if((x>>terms[j].bit)&1) label ^= terms[j].mask;
        unsigned i=index[label];
        return i!=miss && base[i].x==x ? i : miss;
    }
};

struct LutIndex : XorIndex {
    std::array<std::array<unsigned char,64>,4> lut{};
    explicit LutIndex(const Base& base) : XorIndex(base,true) {
        for (unsigned i=0;i<term_count;++i) {
            unsigned bit=terms[i].bit-7;
            lut[bit/6][1u<<(bit%6)]=terms[i].mask;
        }
        for(auto& group : lut)
            for(unsigned v=1;v<64;++v)
                group[v]=group[v & (v-1)] ^ group[v & -v];
    }
    size_t lookup(const Base& base,Key x) const {
        unsigned label=(x&127)^lut[0][(x>>7)&63]^lut[1][(x>>13)&63]
            ^lut[2][(x>>19)&63]^lut[3][(x>>25)&63];
        unsigned i=index[label];
        return i!=miss && base[i].x==x ? i : miss;
    }
};

// Build both forms from identical seven-bit labels. Neither stores build scratch.
template<bool compact>
struct Packed {
    std::array<unsigned char,compact ? 64 : 128> index;
    std::array<std::array<unsigned char,64>,4> lut;
    struct Direction {unsigned char d,pivot;};
    struct Empty {};
    [[no_unique_address]] std::conditional_t<compact,Direction,Empty> direction;
    unsigned project(unsigned x) const {
        if constexpr(compact) {
            unsigned y=x ^ ((0u-unsigned((x & direction.pivot)!=0)) & direction.d);
            unsigned below=direction.pivot-1;
            return (y & below) | ((y>>1) & ~below);
        } else return x;
    }
    unsigned address(Key x) const {
        return (x&127)^lut[0][(x>>7)&63]^lut[1][(x>>13)&63]
            ^lut[2][(x>>19)&63]^lut[3][(x>>25)&63];
    }
    explicit Packed(const Base& base) {
        LutIndex source(base);
        lut=source.lut;
        std::array<unsigned,17> labels;
        for(unsigned i=0;i<17;++i) labels[i]=address(base[i].x);
        if constexpr(compact) {
            std::array<bool,128> used{};
            for(unsigned i=0;i<17;++i)
                for(unsigned j=0;j<i;++j) used[labels[i]^labels[j]]=true;
            unsigned d=1;
            while(d<128 && used[d]) ++d;
            if(d==128) std::abort();
            direction={static_cast<unsigned char>(d),static_cast<unsigned char>(d & -d)};
        }
        index.fill(miss);
        for(unsigned i=0;i<17;++i) {
            unsigned slot=project(labels[i]);
            if(slot>=index.size() || index[slot]!=miss) std::abort();
            index[slot]=i;
        }
    }
    size_t lookup(const Base& base,Key x) const {
        unsigned i=index[project(address(x))];
        return i!=miss && base[i].x==x ? i : miss;
    }
};

template<bool compact,bool total=false>
struct FusedIndex {
    std::array<unsigned char,compact?64:128> index;
    std::array<unsigned char,224> lut{};
    explicit FusedIndex(const Base& base) {
        Packed<compact> source(base);
        index=source.index;
        if constexpr(total) for(auto& i : index) if(i==miss) i=0;
        for(unsigned bit=0;bit<31;++bit) {
            unsigned group=std::min(bit/5,5u);
            unsigned one=1u<<(bit-5*group);
            lut[32*group+one]=source.project(source.address(Key{1}<<bit));
        }
        for(unsigned group=0;group<6;++group) {
            auto* t=lut.data()+32*group;
            for(unsigned v=1;v<(group==5?64u:32u);++v)
                t[v]=t[v&(v-1)]^t[v&-v];
        }
    }
    size_t lookup(const Base& base,Key x) const {
        unsigned slot=lut[x&31]^lut[32+((x>>5)&31)]^lut[64+((x>>10)&31)]^
            lut[96+((x>>15)&31)]^lut[128+((x>>20)&31)]^lut[160+((x>>25)&63)];
        unsigned i=index[slot];
        if constexpr(total) return base[i].x==x ? i : miss;
        else return i!=miss && base[i].x==x ? i : miss;
    }
};

int main(int argc, char** argv) {
    if (argc!=2) return 1;
    std::cerr << sizeof(LutIndex) << " " << sizeof(Packed<false>) << " " << sizeof(Packed<true>) << " " << sizeof(FusedIndex<false>) << " " << sizeof(FusedIndex<true>) << "\n";
    std::mt19937 rng(std::stoul(argv[1]));
    std::vector<Base> bases(4096);
    for (auto& base : bases) for (auto& point : base)
        if (!(std::cin >> point.x) || point.x>=prime) return 2;
    std::shuffle(bases.begin(),bases.end(),rng);
    std::cout << "count,hit_percent,round,arm,ns_per_base\n";
    for (int count : {16,256,1024}) for (int pct : {0,50,100}) {
        std::vector<Key> q(bases.size()*count);
        std::vector<size_t> expected(q.size()),out(q.size());
        for (size_t i=0; i<q.size(); ++i) {
            const auto& base=bases[i/count];
            if (pct==100 || (pct!=0 && rng()%100 < static_cast<unsigned>(pct))) {
                expected[i]=rng()%base.size(); q[i]=base[expected[i]].x;
            } else {
                do { q[i]=rng()%prime; } while(scan(base,q[i])!=miss);
                expected[i]=miss;
            }
        }
        for(int round=0;round<12;++round) for(int j=0;j<4;++j) {
            int arm=(round+(round/4%2?3-j:j))%4;
            auto start=std::chrono::steady_clock::now();
            for(size_t b=0;b<bases.size();++b) {
                const auto& base=bases[b];
                if(arm==0) {
                    FusedIndex<false> index(base);
                    for(int k=0;k<count;++k) out[b*count+k]=index.lookup(base,q[b*count+k]);
                } else if(arm==2) {
                    FusedIndex<false,true> index(base);
                    for(int k=0;k<count;++k) out[b*count+k]=index.lookup(base,q[b*count+k]);
                } else if(arm==3) {
                    FusedIndex<true,true> index(base);
                    for(int k=0;k<count;++k) out[b*count+k]=index.lookup(base,q[b*count+k]);
                } else {
                    FusedIndex<true> index(base);
                    for(int k=0;k<count;++k) out[b*count+k]=index.lookup(base,q[b*count+k]);
                }
            }
            auto dt=std::chrono::steady_clock::now()-start;
            if(out!=expected) return 3;
            if(round>=4) std::cout<<count<<','<<pct<<','<<round-4<<','<<std::array{"fused128","fused64","total128","total64"}[arm]<<','
                <<std::chrono::duration<double,std::nano>(dt).count()/bases.size()<<'\n';
        }
    }
}
