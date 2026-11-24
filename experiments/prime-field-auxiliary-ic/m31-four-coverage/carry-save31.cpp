// Compare canonical sums of three public 31-bit words, including the word p.
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <random>
#include <vector>

constexpr uint32_t p = 2147483647;
using Words = std::vector<uint32_t>;

template<bool carrySave>
__attribute__((noinline)) void sums(const Words& a, const Words& b, const Words& c, Words& out) {
    for (size_t i = 0; i < out.size(); ++i) {
        if constexpr (carrySave) {
            uint32_t ab = a[i] ^ b[i];
            uint32_t m = (a[i] & b[i]) | (ab & c[i]);
            uint32_t t = (ab ^ c[i]) + (((m << 1) & p) | (m >> 30));
            t = (t & p) + (t >> 31);
            out[i] = t == p ? 0 : t;
        } else {
            uint64_t t = uint64_t(a[i]) + b[i] + c[i];
            uint32_t folded = uint32_t(t & p) + uint32_t(t >> 31);
            out[i] = folded >= p ? folded - p : folded;
        }
    }
}

int main() {
    constexpr size_t count = 65536;
    Words a(count), b(count), c(count), expected(count), out(count);
    for (unsigned seed = 0; seed < 6; ++seed) {
        std::mt19937 rng(311100 + seed);
        constexpr std::array<uint32_t,5> edge{0,1,1u << 30,p-1,p};
        for (size_t i = 0; i < count; ++i) {
            a[i] = i < 125 ? edge[i % 5] : rng() & p;
            b[i] = i < 125 ? edge[i / 5 % 5] : rng() & p;
            c[i] = i < 125 ? edge[i / 25] : rng() & p;
            expected[i] = (uint64_t(a[i]) + b[i] + c[i]) % p;
        }
        for (int round = 0; round < 24; ++round) {
            for (int arm = 0; arm < 2; ++arm) {
                bool carry = (arm + round + seed) % 2;
                auto start = std::chrono::steady_clock::now();
                if (carry) sums<true>(a,b,c,out);
                else sums<false>(a,b,c,out);
                auto elapsed = std::chrono::steady_clock::now() - start;
                if (out != expected) return 1;
                if (round >= 4) std::printf("%u,%d,%d,%.5f\n",seed,round,int(carry),
                    std::chrono::duration<double,std::nano>(elapsed).count() / count);
            }
        }
    }
}
