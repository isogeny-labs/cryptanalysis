#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>
using W=uint32_t;
constexpr W p=2147483647;
W add(W x,W y){W z=x+y;return z>=p?z-p:z;}
W sub(W x,W y){return x>=y?x-y:x+(p-y);}
// Canonical field inputs allow a product plus 2p to fit a single Mersenne fold.
W fold(uint64_t product) {
    return add(W(product >> 31), W(product) & p);
}

W mul(W x, W y) {
#ifdef M31_BASELINE_REMAINDER
    return uint64_t(x) * y % p;
#else
    return fold(uint64_t(x) * y);
#endif
}

W inv(W x){
    if(!x)std::abort();
    W acc=1;
    for(W e=p-2;e;e>>=1){if(e&1)acc=mul(acc,x);x=mul(x,x);}
    return acc;
}
struct Point{W x,y;};
Point fromSlope(Point a,Point b,W m){
#if !defined(M31_BASELINE_REMAINDER) && !defined(M31_SEPARATE_CHORD)
    W x = fold(uint64_t(m)*m + (2*p - a.x - b.x));
#else
    W x=sub(sub(mul(m,m),a.x),b.x);
#endif
    return {x,sub(mul(m,sub(a.x,x)),a.y)};
}
Point twice(Point a){return fromSlope(a,a,mul(add(mul(3,mul(a.x,a.x)),2),inv(add(a.y,a.y))));}
struct Request{Point a,b;unsigned next,weight;};
struct State{Point pt;unsigned next;};
using Clock=std::chrono::steady_clock;
template<unsigned Width, bool PairedSigns = false, unsigned Lanes = 1>
std::vector<W> census(const std::array<Point,17>& basis){
    std::array<std::array<Point,5>,17> multiples{};
    std::array<std::vector<State>,4> states;
    std::vector<W> out;out.reserve(28033);
    for(unsigned i=0;i<basis.size();++i){
        auto& v=multiples[i];v[1]=basis[i];v[2]=twice(v[1]);
        v[3]=fromSlope(v[2],v[1],mul(sub(v[2].y,v[1].y),inv(sub(v[2].x,v[1].x))));
        v[4]=twice(v[2]);
        for(unsigned w=1;w<4;++w)states[w].push_back({v[w],i+1});
        out.push_back(v[4].x);
    }
    std::array<Request,Width> batch;unsigned used=0;
    auto flush=[&](){
        if(!used)return;
        std::array<W,Width> before,delta;
        static_assert(Lanes == 1 || Lanes == 4);
        std::array<W, Lanes> products;
        products.fill(1);
        for (unsigned k = 0; k < used; ++k) {
            W& product = products[k % Lanes];
            before[k] = product;
            delta[k] = sub(batch[k].a.x, batch[k].b.x);
            product = mul(product, delta[k]);
        }
        std::array<W, Lanes> reciprocals;
        if constexpr (Lanes == 1) {
            reciprocals[0] = inv(products[0]);
        } else {
            W left = mul(products[0], products[1]);
            W right = mul(products[2], products[3]);
            W rootInverse = inv(mul(left, right));
            W leftInverse = mul(right, rootInverse);
            W rightInverse = mul(left, rootInverse);
            reciprocals = {mul(products[1], leftInverse), mul(products[0], leftInverse),
                           mul(products[3], rightInverse), mul(products[2], rightInverse)};
        }
        for(unsigned k=used;k-->0;){
            const Request& r = batch[k];
            W& reciprocal = reciprocals[k % Lanes];
            W inverseDelta = mul(before[k], reciprocal);
            reciprocal = mul(reciprocal, delta[k]);
            auto emit = [&](W numerator) {
                Point c = fromSlope(r.a, r.b, mul(numerator, inverseDelta));
                if (r.weight == 4) out.push_back(c.x);
                else states[r.weight].push_back({c, r.next});
            };
            emit(sub(r.a.y, r.b.y));
            if constexpr (PairedSigns) emit(add(r.a.y, r.b.y));
        }
        used=0;
    };
    for(unsigned w=1;w<4;++w){
        for(auto s:states[w])for(unsigned j=s.next;j<basis.size();++j){
            for(unsigned m=1;m<=4-w;++m){
                Point b=multiples[j][m];
                batch[used++] = {s.pt, b, j+1, w+m};
                if (used == Width) flush();
                if constexpr (!PairedSigns) {
                    b.y = sub(0, b.y);
                    batch[used++]={s.pt,b,j+1,w+m};
                    if(used==Width)flush();
                }
            }
        }
        flush();
    }
    return out;
}
// Three stable least-significant-digit passes cover every uint32 key.
void radixSort(std::vector<W>& keys) {
    constexpr unsigned digitBits = 11;
    constexpr unsigned buckets = 1u << digitBits;
    constexpr unsigned mask = buckets - 1;
    std::vector<W> scratch(keys.size());
    for (unsigned shift = 0; shift < 32; shift += digitBits) {
        std::array<std::size_t, buckets> cursor{};
        for (W key : keys) ++cursor[(key >> shift) & mask];
        std::size_t next = 0;
        for (auto& entry : cursor) {
            std::size_t count = entry;
            entry = next;
            next += count;
        }
        for (W key : keys) scratch[cursor[(key >> shift) & mask]++] = key;
        keys.swap(scratch);
    }
}

int main(int argc,char**argv){
    if(argc < 3 || argc > 5)return 1;
    const bool multiset = argc == 5;
    if (multiset && std::string(argv[4]) != "multiset") return 1;
    const std::string sortMode = argc >= 4 ? argv[3] : "std";
    if (sortMode != "std" && sortMode != "radix") return 1;
    std::array<Point,17> basis;
    for (auto& pt : basis) {
        if (!(std::cin >> pt.x >> pt.y) || pt.x >= p || pt.y >= p) return 2;
    }
    int arm=std::atoi(argv[1]);
    bool paired = std::string(argv[1]) == "paired-512";
    bool pairedFour = std::string(argv[1]) == "paired-512-lanes4";
    auto start=Clock::now();
    std::vector<W> xs;
    if (pairedFour) xs = census<512, true, 4>(basis);
    else if (paired) xs = census<512, true>(basis);
    else switch (arm) {
        case 1: xs = census<1>(basis); break;
        case 32: xs = census<32>(basis); break;
        case 256: xs = census<256>(basis); break;
        case 512: xs = census<512>(basis); break;
        case 1024: xs = census<1024>(basis); break;
        default: xs = census<128>(basis); break;
    }
    auto elapsed=std::chrono::duration<double,std::milli>(Clock::now()-start).count();
    if (sortMode == "radix") radixSort(xs);
    else std::sort(xs.begin(),xs.end());
    auto sortedMs = std::chrono::duration<double,std::milli>(Clock::now()-start).count();
    if (xs.size() != 28033) return 3;
    if (!multiset && std::adjacent_find(xs.begin(), xs.end()) != xs.end()) return 3;
    auto f=std::fopen(argv[2],"wb");if(!f)return 4;
    if(std::fwrite(xs.data(),sizeof(W),xs.size(),f)!=xs.size()||std::fclose(f))return 5;
    std::cout << elapsed;
    if (argc >= 4) std::cout << ',' << sortedMs;
    std::cout << '\n';
    return 0;
}
