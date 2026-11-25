// Nine-word sums, structure-of-arrays layout. All three paths return canonical residues.
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <random>
#include <vector>

constexpr uint32_t p = 2147483647;
using Words = std::vector<uint32_t>;
using Inputs = std::array<Words, 9>;
struct Pair { uint32_t a, b; };

inline Pair compress(uint32_t a, uint32_t b, uint32_t c) {
    uint32_t ab = a ^ b;
    uint32_t majority = (a & b) | (ab & c);
    return {ab ^ c, ((majority << 1) & p) | (majority >> 30)};
}

enum class Mode { wide, pairwise, tree };

template<Mode mode>
__attribute__((noinline)) void sum9(const Inputs& x, Words& out) {
    for (size_t i = 0; i < out.size(); ++i) {
        uint64_t t = 0;
        if constexpr (mode == Mode::tree) {
            auto u = compress(x[0][i], x[1][i], x[2][i]);
            auto v = compress(x[3][i], x[4][i], x[5][i]);
            auto w = compress(x[6][i], x[7][i], x[8][i]);
            auto a = compress(u.a, v.a, w.a);
            auto b = compress(u.b, v.b, w.b);
            auto c = compress(a.a, a.b, b.a);
            auto d = compress(c.a, c.b, b.b);
            t = d.a + d.b;
        } else if constexpr (mode == Mode::pairwise) {
            t = x[8][i];
            for (size_t j = 0; j < 8; j += 2) t += x[j][i] + x[j+1][i];
        } else {
            for (const auto& row : x) t += row[i];
        }
        uint32_t folded = uint32_t(t & p) + uint32_t(t >> 31);
        out[i] = folded >= p ? folded - p : folded;
    }
}

int main() {
    constexpr size_t count = 65536;
    Inputs inputs;
    for (auto& row : inputs) row.resize(count);
    Words out(count), expected(count);
    constexpr std::array<uint32_t,5> edges{0,1,1u<<30,p-1,p};
    constexpr std::array kernels{sum9<Mode::wide>,sum9<Mode::pairwise>,sum9<Mode::tree>};
    for (unsigned seed = 0; seed < 6; ++seed) {
        std::mt19937 rng(311200+seed);
        for (size_t i=0; i<count; ++i) {
            uint64_t sum=0;
            for (auto& row : inputs) {
                row[i] = i<edges.size() ? edges[i] : rng() & p;
                sum += row[i];
            }
            expected[i]=sum%p;
        }
        for (int round=0; round<24; ++round) for (int j=0; j<3; ++j) {
            int arm=(round+seed+j)%3;
            auto start=std::chrono::steady_clock::now();
            kernels[arm](inputs,out);
            auto elapsed=std::chrono::steady_clock::now()-start;
            if (out!=expected) return 1;
            if (round>=6) std::printf("%u,%d,%d,%.6f\n",seed,round,arm,
                std::chrono::duration<double,std::nano>(elapsed).count()/count);
        }
    }
}
