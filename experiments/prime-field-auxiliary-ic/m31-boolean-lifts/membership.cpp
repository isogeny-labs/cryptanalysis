#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <random>

using U = uint32_t;
constexpr size_t rows = 32768;
static std::array<U, rows> inputs;
static std::array<uint8_t, rows> output, reference;
static uint64_t masks[2];

static U bit(U x, int i) { return (x >> i) & 1; }
static U six(U x) { return (x & 3) | ((x >> 4) & 28) | (bit(x,26) << 5); }
static U sparse(U x) {
    return ((x >> 1) & 3) | ((bit(x,0)^bit(x,3)^bit(x,22)) << 2)
        | ((bit(x,0)^bit(x,10)^bit(x,27)) << 3) | ((bit(x,7)^bit(x,10)^bit(x,26)) << 4);
}
template<int arm> __attribute__((noinline)) static void run() {
    for (size_t i=0; i<rows; ++i) {
        U x = inputs[i];
        if constexpr (arm==0) {
            U k = bit(x,5) | bit(x,8)<<1 | bit(x,15)<<2 | bit(x,26)<<3;
            output[i] = bit(10851,k);
        } else if constexpr (arm==1) output[i] = (masks[0] >> six(x)) & 1;
        else if constexpr (arm==2) output[i] = (masks[1] >> sparse(x)) & 1;
        else if constexpr (arm==3) {
            constexpr U m[] = {2627573428u,1248798149u,2467489457u,1987044356u,731358120u};
            U k = 0;
            for (int j=0; j<5; ++j) k |= U(__builtin_parity((x | 0x80000000u) & m[j])) << j;
            output[i] = k < 17;
        } else output[i] = __builtin_parity(x & 0x50a779d6u);
    }
}
int main(int argc,char **argv) {
    if (argc != 2) return 1;
    std::array<U,32> xs;
    std::array<unsigned,32> ys;
    for (size_t i=0; i<32; ++i) {
        if (!(std::cin >> xs[i] >> ys[i]) || ys[i]>1) return 1;
        masks[0] |= uint64_t(ys[i]) << six(xs[i]);
        masks[1] |= uint64_t(ys[i]) << sparse(xs[i]);
    }
    std::array<unsigned,rows> indices;
    for (size_t i=0; i<rows; ++i) indices[i]=i%32;
    std::mt19937 rng(std::stoul(argv[1]));
    std::shuffle(indices.begin(),indices.end(),rng);
    for (size_t i=0; i<rows; ++i) { inputs[i]=xs[indices[i]]; reference[i]=ys[indices[i]]; }
    void (*arms[])() = {run<0>,run<1>,run<2>,run<3>,run<4>};
    const char *names[] = {"four_bit","six_bit","sparse_five","grouped_five","one_parity"};
    std::array<std::array<double,40>,5> times;
    for (auto arm:arms) { arm(); if (output!=reference) return 1; }
    for (int t=0; t<50; ++t) for (int j=0; j<5; ++j) {
        int k=(t+(t/5%2 ? 4-j : j))%5;
        auto start=std::chrono::steady_clock::now();
        for (int rep=0; rep<64; ++rep) { arms[k](); asm volatile("" ::: "memory"); }
        auto elapsed=std::chrono::duration<double,std::nano>(std::chrono::steady_clock::now()-start);
        if (t>=10) times[k][t-10]=elapsed.count()/(rows*64);
    }
    for (int k=0; k<5; ++k) {
        auto &v=times[k]; std::sort(v.begin(),v.end());
        std::cout<<argv[1]<<","<<names[k]<<","<<(v[19]+v[20])/2<<"\n";
    }
}
