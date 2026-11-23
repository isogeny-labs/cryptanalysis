// clang++ -O3 -mcpu=native -std=c++17 fold_bench.cpp -o fold_bench
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <random>

constexpr uint64_t modulus = (1ULL << 31) - 1;
using Values = std::array<uint32_t, 16384>;

inline uint64_t fold(uint64_t x) { return (x & modulus) + (x >> 31); }

template<int folds>
__attribute__((noinline)) uint64_t checksum(const Values& a, const Values& b) {
    uint64_t sum = 0;
    for (size_t i = 0; i < a.size(); ++i) {
        uint64_t product = uint64_t(a[i]) * b[i];
        if constexpr (folds == 0) {
            sum += product % modulus;
        } else {
            uint64_t reduced = fold(product);
            if constexpr (folds == 2) reduced = fold(reduced);
            sum += reduced >= modulus ? reduced - modulus : reduced;
        }
    }
    return sum;
}

int main() {
    Values a, b;
    std::mt19937 rng(1953);
    for (auto& x : a) x = rng() % modulus;
    for (auto& x : b) x = rng() % modulus;
    auto expected = checksum<0>(a, b);
    std::array<uint64_t (*)(const Values&, const Values&), 3> kernels{
        checksum<0>, checksum<1>, checksum<2>};
    std::array<int, 3> order{0, 1, 2};
    std::puts("round,folds,ns_per_product,checksum");
    for (int round = 0; round < 30; ++round) {
        std::shuffle(order.begin(), order.end(), rng);
        for (int k : order) {
            constexpr unsigned repeats = 256;
            uint64_t sum = 0;
            auto start = std::chrono::steady_clock::now();
            for (unsigned r = 0; r < repeats; ++r) {
                asm volatile("" ::: "memory");
                sum += kernels[k](a, b);
            }
            auto elapsed = std::chrono::steady_clock::now() - start;
            if (sum != expected * repeats) return 1;
            double ns = std::chrono::duration<double, std::nano>(elapsed).count();
            std::printf("%d,%d,%.6f,%llu\n", round, k, ns / (a.size() * repeats),
                        static_cast<unsigned long long>(sum));
        }
    }
}
