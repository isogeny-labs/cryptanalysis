#ifdef M31_EXPLICIT_CENSUS
#include <arm_neon.h>
#endif
#ifdef M31_BATCH_CENSUS
#include "../m31-native-product/product.h"
#endif
#ifdef M31_PROJECTED_CENSUS
#if !defined(M31_BATCH_CENSUS) || defined(M31_EXPLICIT_CENSUS)
#error "Projected classification requires the batch product kernel"
#endif
#include "../m31-projection-label/table.h"
#endif
#include <algorithm>
#include <cstdint>
#include <cstdio>
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

struct SmoothValue {
    uint32_t value;
    bool nonsquare;
};

// Each stable pass orders one more byte, from least to most significant.
void sortKeys(std::vector<uint32_t>& keys) {
    std::vector<uint32_t> scratch(keys.size());
    for (unsigned shift = 0; shift < 32; shift += 8) {
        size_t offsets[256]{};
        for (uint32_t key : keys) ++offsets[(key >> shift) & 255];
        size_t next = 0;
        for (auto& offset : offsets) {
            const size_t count = offset;
            offset = next;
            next += count;
        }
        for (uint32_t key : keys) scratch[offsets[(key >> shift) & 255]++] = key;
        keys.swap(scratch);
    }
}

#ifdef M31_PROJECTED_CENSUS
template <unsigned N>
#if defined(__clang__) || defined(__GNUC__)
__attribute__((always_inline))
#endif
inline void project(const uint32_t* inputs, uint32_t (&powers)[N]) {
    std::copy_n(inputs, N, powers);
    for (unsigned step = 0; step < 15; ++step)
        m31_products(powers, powers, powers, N);
    m31_products(powers, inputs, powers, N);
}
#endif

int main() {
#ifdef M31_PROJECTED_CENSUS
    const m31_projection::Tables table;
#endif
    std::vector<SmoothValue> values{{1, false}};
    constexpr unsigned bounds[] = {7, 13, 23, 47};
    std::vector<uint32_t> keys;
    size_t firstNew = 0;
    unsigned stage = 0;
    for (U prime : {3,5,7,11,13,17,19,23,29,31,37,41,43,47}) {
        const auto previous=values.size();
        const bool primeNonsquare = !square(prime);
        for (size_t i=0; i<previous; ++i) {
            bool nonsquare = values[i].nonsquare;
            for (U x=U(values[i].value)*prime; x<p; x*=prime) {
                // Quadratic characters multiply on these nonzero residues.
                nonsquare ^= primeNonsquare;
                values.push_back({static_cast<uint32_t>(x), nonsquare});
            }
        }
        if (prime != bounds[stage]) continue;
        keys.reserve(values.size());
        for (size_t i = firstNew; i < values.size(); ++i) {
            const auto entry = values[i];
            // Each 31-bit window is one rotation, independent of the previous window.
            const U doubled = (U(entry.value) << 31) | entry.value;
            uint32_t key = entry.value;
#ifdef __clang__
#pragma clang loop vectorize(enable)
#endif
            for (unsigned shift = 1; shift < 31; ++shift)
                key = std::min(key, static_cast<uint32_t>((doubled >> shift) & p));
            // Equal rotations have the same character. Sorting puts the earliest bound first.
            // The minimum rotation starts with zero and ends in one.
            const uint32_t middle = static_cast<uint32_t>(key >> 1);
            keys.push_back((middle << 3) | (uint32_t(entry.nonsquare) << 2) | stage);
        }
        firstNew = values.size();
        ++stage;
    }
    sortKeys(keys);
    U orbitCounts[4]{}, eligibleCounts[4]{}, liftCounts[4]{};
#ifdef M31_PROJECTED_CENSUS
    constexpr unsigned batch = 128;
    // Append a whole orbit before flushing. Each band has its own partial batch.
    uint32_t pending[4][batch + 31]{};
    unsigned used[4]{};
    auto countLifts = [&](unsigned band, unsigned count) {
        uint32_t powers[batch];
        project(pending[band], powers);
        for (unsigned j = 0; j < count; ++j)
            liftCounts[band] += table.isSquare(pending[band][j], powers[j]);
    };
#endif
    U previousKey = 0;
    for (const U packed : keys) {
        const U v = 2 * (packed >> 3) + 1;
        if (v == previousKey) continue;
        previousKey = v;
        const unsigned band = packed & 3;
        ++orbitCounts[band];
        if (!(packed & 4)) continue;
        U eligible = 0, lifts = 0;
#if defined(M31_BATCH_CENSUS) || defined(M31_EXPLICIT_CENSUS)
        // Every nonzero orbit has 31 elements. Pad each predicate to 32 lanes.
        uint32_t inputs[64] = {};
        const U square = v * v % p;
        const U cube = square * v % p;
        const U xWindow = (v << 31) | v;
        const U squareWindow = (square << 31) | square;
        const U cubeWindow = (cube << 31) | cube;
        // At lane j the three powers rotate by j, 2j, and 3j modulo 31.
        // Unrolling turns every window offset into a constant shift.
#ifdef __clang__
#pragma clang loop unroll(full)
#endif
        for (unsigned j = 0; j < 31; ++j) {
            const U x = (xWindow >> (31 - j)) & p;
            const U xx = (squareWindow >> (31 - (2*j % 31))) & p;
            const U xxx = (cubeWindow >> (31 - (3*j % 31))) & p;
            inputs[j] = (xx + 1) % p;
            inputs[32 + j] = (xxx + 2*x + 14) % p;
        }
#ifdef M31_PROJECTED_CENSUS
        uint32_t powers[32];
        project(inputs, powers);
        unsigned count = used[band];
        for (unsigned j = 0; j < 31; ++j) {
            pending[band][count] = inputs[32 + j];
            count += !table.isSquare(inputs[j], powers[j]);
        }
        eligible = count - used[band];
        if (count >= batch) {
            countLifts(band, batch);
            count -= batch;
            std::copy_n(pending[band] + batch, count, pending[band]);
        }
        used[band] = count;
#else
        uint32_t powers[64];
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
#endif
#else
        U x = v;
        do {
            U xx=x*x%p;
            if (!square((xx+1)%p)) {
                ++eligible;
                lifts+=square((xx*x+2*x+14)%p);
            }
            x=rotate(x);
        } while (x!=v);
#endif
        eligibleCounts[band] += eligible;
        liftCounts[band] += lifts;
    }
#ifdef M31_PROJECTED_CENSUS
    for (unsigned band = 0; band < 4; ++band)
        if (used[band]) countLifts(band, used[band]);
#endif
    U orbits = 0, eligible = 0, lifts = 0;
    for (unsigned band = 0; band < 4; ++band) {
        orbits += orbitCounts[band];
        eligible += eligibleCounts[band];
        lifts += liftCounts[band];
        std::printf("%u %llu %llu %llu\n", bounds[band], (unsigned long long)orbits,
            (unsigned long long)eligible, (unsigned long long)lifts);
    }
}
