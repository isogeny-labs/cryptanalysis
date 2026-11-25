#include <algorithm>
#include <array>
#include <arm_neon.h>
#include <cstdint>
#include <cstddef>
#include <limits>

namespace {
using Word = std::uint32_t;
constexpr Word modulus = 2147483647;
constexpr Word primes[] = {3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,
    61,67,71,73,79,83,89,97,101,103,107,109,113,127,131,137,139,149,
    151,157,163,167,173,179,181,191,193,197,199,211};
struct Tables {
    std::array<Word,48> inverse{}, limit{};
    constexpr Tables() {
        for (std::size_t i=0; i<sizeof(primes)/sizeof(*primes); ++i) {
            Word inv=1;
            for (int j=0; j<5; ++j) inv*=2u-primes[i]*inv;
            inverse[i]=inv;
            limit[i]=std::numeric_limits<Word>::max()/primes[i];
        }
        // Inactive lanes produce an odd input > 0 against a zero limit.
        inverse[46]=inverse[47]=1;
    }
};
constexpr Tables table;
constexpr Word weights[]={1,2,4,8};
bool smooth(Word odd) {
    Word residual=odd;
    for (unsigned block=0; block<48; block+=16) {
        uint32x4_t flags=vdupq_n_u32(0);
        for (unsigned group=0; group<4; ++group) {
            unsigned base=block+4*group;
            auto quotient=vmulq_n_u32(vld1q_u32(&table.inverse[base]),odd);
            auto hit=vcleq_u32(quotient,vld1q_u32(&table.limit[base]));
            auto bits=vshlq_u32(vld1q_u32(weights),vdupq_n_s32(4*group));
            flags=vorrq_u32(flags,vandq_u32(hit,bits));
        }
        Word mask=vaddvq_u32(flags);
        while (mask) {
            unsigned index=block+__builtin_ctz(mask);
            Word inv=table.inverse[index], limit=table.limit[index];
            residual*=inv;
            Word quotient=residual*inv;
            while (quotient<=limit) {
                residual=quotient;
                quotient=residual*inv;
            }
            mask&=mask-1;
        }
        if (residual<=211) return true;
    }
    return false;
}
}

extern "C" std::size_t m31_prime_lanes(Word *xs,std::size_t n) {
    std::size_t kept=0;
    for (std::size_t i=0;i<n;++i) {
        Word x=xs[i], t=std::min(x,modulus-x);
        if (t && smooth(t>>__builtin_ctz(t))) xs[kept++]=x;
    }
    return kept;
}
