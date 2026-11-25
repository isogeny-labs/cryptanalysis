// clang++ -O3 -mcpu=native -std=c++17 centered_pair_bench.cpp -o centered_pair_bench
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <random>

constexpr int64_t p = 2147483647;
constexpr int64_t radius = p / 2;
constexpr int64_t bias = p * (radius + 1);
struct Input { int32_t a, b, c, d; };
using Panel = std::array<Input, 8192>;

int32_t center(int32_t x) { return x > radius ? x - p : x; }
uint64_t fold(uint64_t x) { return (x & p) + (x >> 31); }

enum Method { modReference, canonical, centered, convert };
template<Method method> uint64_t residue(Input v) {
    if constexpr (method == convert)
        v = {center(v.a), center(v.b), center(v.c), center(v.d)};
    int64_t sum = int64_t(v.a) * v.b + int64_t(v.c) * v.d;
    if constexpr (method == modReference) return sum % p;
    uint64_t s;
    if constexpr (method == canonical) s = fold(fold(sum));
    else s = fold(sum + bias);
    return s >= p ? s - p : s;
}

template<Method method>
__attribute__((noinline)) uint64_t checksum(const Panel& panel) {
    uint64_t sum = 0;
    for (auto v : panel) sum += residue<method>(v);
    return sum;
}

int main() {
    Panel raw, signedValues;
    std::mt19937 rng(1953);
    auto sample = [&]() { return static_cast<int32_t>(rng() % p); };
    for (size_t i = 0; i < raw.size(); ++i) {
        Input v{sample(), sample(), sample(), sample()};
        raw[i] = v;
        signedValues[i] = {center(v.a), center(v.b), center(v.c), center(v.d)};
        auto ref = residue<modReference>(v);
        if (ref != residue<canonical>(v) || ref != residue<centered>(signedValues[i])
            || ref != residue<convert>(v)) return 1;
    }
    const auto expected = checksum<modReference>(raw);
    std::array<uint64_t (*)(const Panel&), 4> kernels{
        checksum<modReference>, checksum<canonical>, checksum<centered>, checksum<convert>};
    std::array<int, 4> order{0,1,2,3};
    const char* names[] = {"constant_mod","canonical_two_fold","precentered","center_inline"};
    std::puts("round,method,ns_per_pair,checksum");
    for (int round = 0; round < 30; ++round) {
        std::shuffle(order.begin(), order.end(), rng);
        for (int k : order) {
            const Panel& inputs = k == centered ? signedValues : raw;
            constexpr unsigned repeats = 256;
            uint64_t sum = 0;
            auto start = std::chrono::steady_clock::now();
            for (unsigned r = 0; r < repeats; ++r) {
                asm volatile("" ::: "memory");
                sum += kernels[k](inputs);
            }
            auto elapsed = std::chrono::steady_clock::now() - start;
            if (sum != repeats * expected) return 1;
            double ns = std::chrono::duration<double, std::nano>(elapsed).count();
            std::printf("%d,%s,%.6f,%llu\n", round, names[k], ns/(inputs.size()*repeats),
                        static_cast<unsigned long long>(sum));
        }
    }
}
