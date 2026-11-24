// Standalone NEON comparison on canonical public M31 words.
#include <arm_neon.h>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <random>
#include <vector>

constexpr uint64_t p = 2147483647;
using Word = uint32_t;
using Kernel = Word (*)(const Word*, const Word*, size_t);

template<bool partial>
__attribute__((noinline)) Word dot(const Word* a, const Word* b, size_t n) {
    auto total = vdupq_n_u64(0);
    auto mask = vdupq_n_u64(p);
    size_t j = 0;
    for (; j+8 <= n; j+=8) {
        auto s = vdupq_n_u64(0);
        for (size_t k=0; k<8; k+=2)
            s = vmlal_u32(s,vld1_u32(a+j+k),vld1_u32(b+j+k));
        s = vaddq_u64(vandq_u64(s,mask),vshrq_n_u64(s,31));
        if constexpr (!partial) {
            s = vaddq_u64(vandq_u64(s,mask),vshrq_n_u64(s,31));
            s = vsubq_u64(s,vandq_u64(vcgeq_u64(s,mask),mask));
        }
        total = vaddq_u64(total,s);
    }
    uint64_t result = vaddvq_u64(total) % p;
    for (; j<n; ++j) result = (result + uint64_t(a[j])*b[j]) % p;
    return Word(result);
}

int main(int argc,char** argv) {
    if (argc!=2) return 1;
    std::mt19937 rng(std::stoul(argv[1]));
    constexpr size_t rows=4096;
    std::puts("terms,round,method,ns_per_dot");
    for (size_t n : {8,17,32,64,128,257}) {
        std::vector<Word> a(rows*n), b(rows*n), expected(rows), out(rows);
        for (size_t r=0; r<rows; ++r) {
            __uint128_t sum=0;
            for (size_t k=0;k<n;++k) {
                size_t i=r*n+k;
                a[i]=r==0?p-1:r==1?0:rng()%p;
                b[i]=r==0?p-1:rng()%p;
                sum+=uint64_t(a[i])*b[i];
            }
            expected[r]=sum%p;
        }
        for (int round=0;round<16;++round) for (int j=0;j<2;++j) {
            int method=(round+j)%2;
            Kernel run=method?dot<true>:dot<false>;
            auto start=std::chrono::steady_clock::now();
            for (size_t r=0;r<rows;++r) out[r]=run(a.data()+r*n,b.data()+r*n,n);
            double ns=std::chrono::duration<double,std::nano>(std::chrono::steady_clock::now()-start).count();
            if (out!=expected) return 2;
            if (round>=4) std::printf("%zu,%d,%s,%.4f\n",n,round-4,method?"partial":"canonical",ns/rows);
        }
    }
}
