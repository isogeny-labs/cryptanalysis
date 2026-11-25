// Standalone NEON comparison on canonical public M31 words.
#include <arm_neon.h>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <random>
#include <vector>

#include "dot-kernel.hpp"

#ifdef M31_WIDE_INPUT
using Input = uint64_t;
#else
using Input = Word;
#endif
using Kernel = Word (*)(const Input*, const Input*, size_t);

#ifdef M31_NATIVE_PRODUCT
// The compiler chooses the instructions for the original input representation.
__attribute__((noinline)) Word native_product(const Input* a, const Input* b, size_t n) {
    uint64_t total = 0;
    size_t j = 0;
    for (; j+4<=n; j+=4) {
        uint64_t block = 0;
        for (size_t k=0;k<4;++k) block += uint64_t(a[j+k])*b[j+k];
        total += (block & p) + (block >> 31);
    }
    uint64_t result = total % p;
    for (; j<n; ++j) result = (result + uint64_t(a[j])*b[j]) % p;
    return Word(result);
}
#endif

#ifdef M31_PAIRED_DOT
Word paired_dot(const Word*, const Word*, size_t);
#endif

int main(int argc,char** argv) {
    if (argc!=2) return 1;
    std::mt19937 rng(std::stoul(argv[1]));
    constexpr size_t rows=4096;
    std::puts("terms,round,method,ns_per_dot");
    for (size_t n : {8,17,32,64,128,257}) {
        std::vector<Input> a(rows*n), b(rows*n);
        std::vector<Word> expected(rows), out(rows);
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
#if defined(M31_PAIRED_DOT)
        constexpr int arms = 2;
        const Kernel kernels[] = {dot<true>, paired_dot};
        const char* labels[] = {"partial", "paired"};
#elif defined(M31_NATIVE_PRODUCT)
        constexpr int arms = 3;
        const Kernel kernels[] = {dot<false>, dot<true>, native_product};
        const char* labels[] = {"canonical", "partial", "native"};
#else
        constexpr int arms = 2;
        const char* labels[] = {"canonical", "partial"};
#endif
        for (int round=0;round<arms*8;++round) for (int j=0;j<arms;++j) {
            int method=(round+j)%arms;
#if defined(M31_NATIVE_PRODUCT) || defined(M31_PAIRED_DOT)
            Kernel run=kernels[method];
#else
            Kernel run=method?dot<true, Input>:dot<false, Input>;
#endif
            auto start=std::chrono::steady_clock::now();
            for (size_t r=0;r<rows;++r) out[r]=run(a.data()+r*n,b.data()+r*n,n);
            double ns=std::chrono::duration<double,std::nano>(std::chrono::steady_clock::now()-start).count();
            if (out!=expected) return 2;
            if (round>=2*arms) std::printf("%zu,%d,%s,%.4f\n",n,round-2*arms,labels[method],ns/rows);
        }
    }
}
