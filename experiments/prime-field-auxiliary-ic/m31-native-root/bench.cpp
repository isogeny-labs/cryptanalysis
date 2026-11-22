#include <arm_neon.h>
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <random>
#include <vector>

using Word = uint32_t;
using Vec = uint32x4_t;
constexpr Word prime = 2147483647;
constexpr size_t count = 4096;

Word square(Word x) {
    uint64_t product = uint64_t(x) * x;
    Word sum = (product & prime) + (product >> 31);
    return sum >= prime ? sum - prime : sum;
}

template<bool highMultiply>
Vec squareVector(Vec x) {
    Vec hi;
    Vec lo;
    if constexpr (highMultiply) {
        int32x4_t sx = vreinterpretq_s32_u32(x);
        hi = vreinterpretq_u32_s32(vqdmulhq_s32(sx, sx));
        lo = vmulq_u32(x, x);
    } else {
        uint64x2_t a = vmull_u32(vget_low_u32(x), vget_low_u32(x));
        uint64x2_t b = vmull_high_u32(x, x);
        lo = vcombine_u32(vmovn_u64(a), vmovn_u64(b));
        hi = vcombine_u32(vshrn_n_u64(a, 31), vshrn_n_u64(b, 31));
    }
    Vec p = vdupq_n_u32(prime);
    Vec sum = vaddq_u32(vandq_u32(lo, p), hi);
    return vsubq_u32(sum, vandq_u32(vcgeq_u32(sum, p), p));
}

// Canonical root or the field modulus as the nonsquare sentinel.
template<unsigned method>
__attribute__((noinline)) void roots(const Word* input, Word* output) {
    if constexpr (method == 0) {
        for (size_t i = 0; i < count; ++i) {
            Word x = input[i], y = x;
            for (int j = 0; j < 29; ++j) y = square(y);
            output[i] = square(y) == x ? std::min(y, prime-y) : prime;
        }
    } else {
        for (size_t i = 0; i < count; i += 4) {
            Vec x = vld1q_u32(input+i), y = x;
            for (int j = 0; j < 29; ++j) y = squareVector<method == 2>(y);
            Vec p = vdupq_n_u32(prime);
            Vec ok = vceqq_u32(squareVector<method == 2>(y), x);
            vst1q_u32(output+i, vbslq_u32(ok, vminq_u32(y, vsubq_u32(p,y)), p));
        }
    }
}

Word oracle(Word x) {
    uint64_t v=x, result=1;
    for (Word e=1u<<29; e; e>>=1) {
        if (e&1) result=result*v%prime;
        v=v*v%prime;
    }
    return result*result%prime==x ? std::min<uint64_t>(result,prime-result) : prime;
}

int main() {
    constexpr std::array methods = {roots<0>, roots<1>, roots<2>};
    std::mt19937 rng(291168);
    std::vector<Word> input(count), expected(count), output(count);
    std::array<unsigned,3> order = {0,1,2};
    std::puts("block,position,arm,elapsed_ns");
    for (int block=0; block<36; ++block) {
        for (auto& x : input) x=rng()%prime;
        input[0]=0; input[1]=1; input[2]=prime-1; input[3]=prime-2;
        std::transform(input.begin(),input.end(),expected.begin(),oracle);
        for (auto method : methods) {
            method(input.data(),output.data());
            if (output!=expected) return EXIT_FAILURE;
        }
        for (size_t pos=0; pos<order.size(); ++pos) {
            auto method=methods[order[pos]];
            auto start=std::chrono::steady_clock::now();
            for (int rep=0; rep<64; ++rep) {
                method(input.data(),output.data());
                asm volatile("" : : "r"(output.data()) : "memory");
            }
            auto ns=std::chrono::duration_cast<std::chrono::nanoseconds>(
                std::chrono::steady_clock::now()-start).count();
            if (output!=expected) return EXIT_FAILURE;
            std::printf("%d,%zu,%u,%lld\n",block,pos,order[pos],static_cast<long long>(ns));
        }
        std::next_permutation(order.begin(),order.end());
    }
}
