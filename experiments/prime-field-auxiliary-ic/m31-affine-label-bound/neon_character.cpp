// clang -O3 -mcpu=native -c ../m31-native-product/product.c -o product.o
// clang++ -std=c++17 -O3 -mcpu=native neon_character.cpp product.o -o neon_character
// Supply the 256 public structured roots as whitespace-separated decimal integers on stdin.
#include "../m31-native-product/product.h"
#include "signed_square.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <charconv>
#include <cstring>
#include <cstdint>
#include <cstdio>
#include <random>

constexpr uint32_t p = (1u << 31) - 1;
using Panel = std::array<uint32_t, 256>;

uint32_t reduce(uint32_t s) { return std::min(s, s - p); }
uint32_t multiply(uint32_t x, uint32_t y) {
    uint64_t z = uint64_t(x) * y;
    return reduce(uint32_t((z & p) + (z >> 31)));
}

uint32x4_t reduce(uint32x4_t s) { return vminq_u32(s, vsubq_u32(s, vdupq_n_u32(p))); }
uint32x4_t multiply(uint32x4_t x, uint32x4_t y) {
    auto hi = vqdmulhq_s32(vreinterpretq_s32_u32(x), vreinterpretq_s32_u32(y));
    auto lo = vandq_u32(vmulq_u32(x, y), vdupq_n_u32(p));
    return reduce(vaddq_u32(lo, vreinterpretq_u32_s32(hi)));
}

template<unsigned k, class T> T join(T a, T b) {
    for (unsigned i = 0; i < k; ++i) a = multiply(a, a);
    return multiply(a, b);
}

// y^(2^30) equals y times its quadratic character.
uint32_t fromSquare(uint32_t y, uint32_t z) {
    return y == 0 ? 0 : (z == y ? 1 : p-1);
}
uint32x4_t fromSquare(uint32x4_t y, uint32x4_t z) {
    auto nonzero = vbslq_u32(vceqq_u32(y,z), vdupq_n_u32(1), vdupq_n_u32(p-1));
    return vbicq_u32(nonzero, vceqq_u32(y,vdupq_n_u32(0)));
}

enum class Power { binary, shortened, squares };
template<Power method, class T> T character(T x, T b) {
    T y = reduce(reduce(multiply(multiply(x,x), x) + reduce(x+x)) + b);
    if constexpr (method == Power::squares) {
        T z = y;
        for (unsigned i = 0; i < 30; ++i) z = multiply(z,z);
        return fromSquare(y,z);
    } else if constexpr (method == Power::shortened) {
        auto y2 = join<1>(y,y);
        auto y3 = join<1>(y2,y);
        auto y5 = join<2>(y3,y2);
        auto y10 = join<5>(y5,y5);
        auto y15 = join<5>(y10,y5);
        return join<15>(y15,y15);
    } else {
        T result = y;
        for (unsigned i = 1; i < 30; ++i) result = join<1>(result, y);
        return result;
    }
}

template<bool vector, Power method>
__attribute__((noinline)) void evaluate(const Panel& xs, uint32_t b, Panel& out) {
    if constexpr (vector) {
        for (size_t i = 0; i < xs.size(); i += 4)
            vst1q_u32(out.data()+i, character<method>(vld1q_u32(xs.data()+i), vdupq_n_u32(b)));
    } else {
        for (size_t i = 0; i < xs.size(); ++i) out[i] = character<method>(xs[i],b);
    }
}

__attribute__((noinline)) void arraySquares(const Panel& xs, uint32_t b, Panel& out) {
    Panel y;
    for (size_t i=0;i<xs.size();++i) {
        auto x = xs[i];
        y[i] = reduce(reduce(multiply(multiply(x,x),x) + reduce(x+x)) + b);
    }
    m31_products(y.data(),y.data(),out.data(),xs.size());
    for (unsigned i=1;i<30;++i) m31_products(out.data(),out.data(),out.data(),xs.size());
    for (size_t i=0;i<xs.size();++i) out[i] = fromSquare(y[i],out[i]);
}

template<bool signedLanes>
__attribute__((noinline)) void tiledSquares(const Panel& xs, uint32_t b, Panel& out) {
    constexpr unsigned vectors = 8;
    for (size_t i=0;i<xs.size();i+=4*vectors) {
        std::array<uint32x4_t,vectors> y,z;
        for (unsigned j=0;j<vectors;++j) {
            auto x = vld1q_u32(xs.data()+i+4*j);
            y[j] = reduce(reduce(multiply(multiply(x,x),x) + reduce(x+x)) + vdupq_n_u32(b));
        }
        z = y;
        for (unsigned k=0;k<30;++k)
            for (auto& laneGroup : z) {
                if constexpr (signedLanes) laneGroup = signedSquare(laneGroup);
                else laneGroup = multiply(laneGroup,laneGroup);
            }
        for (unsigned j=0;j<vectors;++j) {
            if constexpr (signedLanes) {
                z[j] = canonicalSigned(z[j]);
            }
            vst1q_u32(out.data()+i+4*j,fromSquare(y[j],z[j]));
        }
    }
}

uint32_t reference(uint64_t x, uint32_t b) {
    uint64_t v = (x*x%p*x + 2*x + b)%p, acc = 1;
    for (uint32_t e = (p-1)/2; e; e >>= 1) {
        if (e & 1) acc = acc*v%p;
        v = v*v%p;
    }
    return acc;
}

int main(int argc, char** argv) {
    unsigned seed = 1953;
    if (argc > 2) return 1;
    if (argc == 2) {
        const char* end = argv[1] + std::strlen(argv[1]);
        auto parsed = std::from_chars(argv[1],end,seed);
        if (parsed.ec != std::errc{} || parsed.ptr != end) return 1;
    }
    Panel xs, expected, out;
    for (auto& x : xs) if (std::scanf("%u",&x) != 1 || x >= p) return 1;
    const std::array kernels = {evaluate<false,Power::binary>,evaluate<false,Power::shortened>,
                                evaluate<true,Power::binary>,evaluate<true,Power::shortened>,
                                evaluate<false,Power::squares>,evaluate<true,Power::squares>,
                                arraySquares,tiledSquares<false>,tiledSquares<true>};
    const char* names[] = {"fold_binary","fold_short","neon_binary","neon_short","fold_squares","neon_squares",
                           "array_c_abi","tiled_squares","tiled_signed_squares"};
    std::mt19937 rng(seed);
    std::array<unsigned, 9> order{0,1,2,3,4,5,6,7,8};
    std::puts("seed,curve_b,round,method,ns_per_coordinate");
    for (unsigned b : {14u,36u}) {
        for (size_t i=0;i<xs.size();++i) expected[i]=reference(xs[i],b);
        for (unsigned round=0;round<30;++round) {
            std::shuffle(order.begin(),order.end(),rng);
            for (unsigned k : order) {
                constexpr unsigned repeats = 256;
                out.fill(UINT32_MAX);
                auto start = std::chrono::steady_clock::now();
                for (unsigned r=0;r<repeats;++r) {
                    kernels[k](xs,b,out);
                    asm volatile("" ::: "memory");
                }
                auto elapsed = std::chrono::steady_clock::now()-start;
                if (out != expected) return 2;
                double ns = std::chrono::duration<double,std::nano>(elapsed).count();
                std::printf("%u,%u,%u,%s,%.6f\n", seed, b, round, names[k], ns/(repeats*xs.size()));
            }
        }
    }
}
