// clang++ -std=c++17 -O3 -mcpu=native neon_product.cpp -o neon_product
#include <arm_neon.h>
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <random>

constexpr uint32_t p = (1u << 31) - 1;
constexpr unsigned count = 16384;
using Panel = std::array<uint32_t, count>;

enum class Method { modulo, folded, neon };

template<Method method>
__attribute__((noinline)) void products(const uint32_t* __restrict a,
                                        const uint32_t* __restrict b,
                                        uint32_t* __restrict out) {
    if constexpr (method == Method::neon) {
        const auto mask = vdupq_n_u32(p);
        for (unsigned i = 0; i < count; i += 4) {
            auto x = vld1q_u32(a + i);
            auto y = vld1q_u32(b + i);
            auto hi = vqdmulhq_s32(vreinterpretq_s32_u32(x), vreinterpretq_s32_u32(y));
            auto lo = vandq_u32(vmulq_u32(x, y), mask);
            auto sum = vaddq_u32(lo, vreinterpretq_u32_s32(hi));
            vst1q_u32(out + i, vminq_u32(sum, vsubq_u32(sum, mask)));
        }
    } else {
        for (unsigned i = 0; i < count; ++i) {
            uint64_t z = uint64_t(a[i]) * b[i];
            if constexpr (method == Method::modulo) out[i] = z % p;
            else {
                uint64_t sum = (z & p) + (z >> 31);
                out[i] = sum >= p ? sum - p : sum;
            }
        }
    }
}

int main() {
    std::mt19937 rng(1953);
    Panel a, b, reference, out;
    for (auto& x : a) x = rng() % p;
    for (auto& x : b) x = rng() % p;
    const uint32_t edges[] = {0, 1, 2, 65535, 65536, 1u<<30, p-2, p-1};
    unsigned pos = 0;
    for (auto x : edges) for (auto y : edges) {
        a[pos] = x;
        b[pos++] = y;
    }
    products<Method::modulo>(a.data(), b.data(), reference.data());
    const std::array kernels = {products<Method::modulo>, products<Method::folded>,
                                products<Method::neon>};
    const char* names[] = {"modulo", "widen_fold", "neon_high"};
    std::array<unsigned, 3> order{0, 1, 2};
    std::puts("round,method,ns_per_product");
    for (unsigned round = 0; round < 30; ++round) {
        std::shuffle(order.begin(), order.end(), rng);
        for (auto k : order) {
            constexpr unsigned repeats = 256;
            std::fill(out.begin(), out.end(), UINT32_MAX);
            auto start = std::chrono::steady_clock::now();
            for (unsigned r = 0; r < repeats; ++r) {
                kernels[k](a.data(), b.data(), out.data());
                asm volatile("" ::: "memory");
            }
            auto elapsed = std::chrono::steady_clock::now() - start;
            if (reference != out) return 1;
            double ns = std::chrono::duration<double, std::nano>(elapsed).count();
            std::printf("%u,%s,%.6f\n", round, names[k], ns / (count * repeats));
        }
    }
}
