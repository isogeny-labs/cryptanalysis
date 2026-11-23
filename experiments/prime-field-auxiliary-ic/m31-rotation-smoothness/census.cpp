#ifdef M31_EXPLICIT_CENSUS
#include <arm_neon.h>
#endif
#ifdef M31_BATCH_CENSUS
#include "../m31-native-product/product.h"
#endif
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <unordered_set>
#include <vector>
using U = uint64_t;
constexpr U p = 2147483647;

U rotate(U x) { return ((x << 1) & p) | (x >> 30); }
// In M31, x is a square exactly when x^(2^30) equals x, including zero.
bool square(U x) {
    U value = x;
    for (unsigned i = 0; i < 30; ++i) value = value * value % p;
    return value == x;
}

int main() {
    std::vector<U> values{1};
    std::unordered_set<U> seen;
    U eligible=0, lifts=0;
    for (U prime : {3,5,7,11,13,17,19,23,29,31,37,41,43,47}) {
        const auto previous=values.size();
        for (size_t i=0; i<previous; ++i)
            for (U x=values[i]*prime; x<p; x*=prime) values.push_back(x);
        if (prime!=7 && prime!=13 && prime!=23 && prime!=47) continue;
        for (U v : values) {
            U key=v, x=rotate(v);
            while (x!=v) {key=std::min(key,x); x=rotate(x);}
            if (!seen.insert(key).second || square(key)) continue;
            // Two is a square modulo p, so the whole orbit has the same character.
#if defined(M31_BATCH_CENSUS) || defined(M31_EXPLICIT_CENSUS)
            // Every nonzero orbit has 31 elements. Pad each predicate to 32 lanes.
            uint32_t inputs[64] = {}, powers[64];
            for (unsigned j = 0; j < 31; ++j) {
                const U xx = x * x % p;
                inputs[j] = (xx + 1) % p;
                inputs[32 + j] = (xx * x + 2 * x + 14) % p;
                x = rotate(x);
            }
#ifdef M31_EXPLICIT_CENSUS
            uint32x4_t lanes[16];
            const uint32x4_t modulus = vdupq_n_u32(p);
            for (unsigned j = 0; j < 16; ++j)
                lanes[j] = vld1q_u32(inputs + 4*j);
            for (unsigned step = 0; step < 30; ++step) {
                for (auto& lane : lanes) {
                    const auto xSigned = vreinterpretq_s32_u32(lane);
                    const auto high = vreinterpretq_u32_s32(vqdmulhq_s32(xSigned, xSigned));
                    const auto low = vandq_u32(vmulq_u32(lane, lane), modulus);
                    const auto sum = vaddq_u32(high, low);
                    lane = vminq_u32(sum, vsubq_u32(sum, modulus));
                }
            }
            for (unsigned j = 0; j < 16; ++j)
                vst1q_u32(powers + 4*j, lanes[j]);
#else
            std::copy_n(inputs, 64, powers);
            for (unsigned step = 0; step < 30; ++step)
                m31_products(powers, powers, powers, 64);
#endif
            for (unsigned j = 0; j < 31; ++j) {
                const bool qualifies = inputs[j] != powers[j];
                const bool lift = inputs[32 + j] == powers[32 + j];
                eligible += qualifies;
                lifts += qualifies && lift;
            }
#else
            do {
                U xx=x*x%p;
                if (!square((xx+1)%p)) {
                    ++eligible;
                    lifts+=square((xx*x+2*x+14)%p);
                }
                x=rotate(x);
            } while (x!=v);
#endif
        }
        std::printf("%llu %zu %llu %llu\n",(unsigned long long)prime,
            seen.size(),(unsigned long long)eligible,(unsigned long long)lifts);
    }
}
