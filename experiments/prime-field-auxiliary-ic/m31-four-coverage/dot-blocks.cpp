// Standalone NEON comparison on canonical public M31 words.
#include <arm_neon.h>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <random>
#include <vector>

constexpr uint64_t p = 2147483647;
using Word = uint32_t;
#ifdef M31_WIDE_INPUT
using Input = uint64_t;
inline uint32x2_t load_pair(const Input* x) {
    return vmovn_u64(vld1q_u64(x));
}
#else
using Input = Word;
inline uint32x2_t load_pair(const Input* x) {
    return vld1_u32(x);
}
#endif
using Kernel = Word (*)(const Input*, const Input*, size_t);

template<bool partial>
__attribute__((noinline)) Word dot(const Input* a, const Input* b, size_t n) {
    auto total = vdupq_n_u64(0);
    auto mask = vdupq_n_u64(p);
    size_t j = 0;
    for (; j+8 <= n; j+=8) {
        auto s = vdupq_n_u64(0);
        for (size_t k=0; k<8; k+=2)
            s = vmlal_u32(s,load_pair(a+j+k),load_pair(b+j+k));
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
#ifdef M31_NATIVE_PRODUCT
        constexpr int arms = 3;
        const Kernel kernels[] = {dot<false>, dot<true>, native_product};
        const char* labels[] = {"canonical", "partial", "native"};
#else
        constexpr int arms = 2;
        const char* labels[] = {"canonical", "partial"};
#endif
        for (int round=0;round<arms*8;++round) for (int j=0;j<arms;++j) {
            int method=(round+j)%arms;
#ifdef M31_NATIVE_PRODUCT
            Kernel run=kernels[method];
#else
            Kernel run=method?dot<true>:dot<false>;
#endif
            auto start=std::chrono::steady_clock::now();
            for (size_t r=0;r<rows;++r) out[r]=run(a.data()+r*n,b.data()+r*n,n);
            double ns=std::chrono::duration<double,std::nano>(std::chrono::steady_clock::now()-start).count();
            if (out!=expected) return 2;
            if (round>=2*arms) std::printf("%zu,%d,%s,%.4f\n",n,round-2*arms,labels[method],ns/rows);
        }
    }
}
