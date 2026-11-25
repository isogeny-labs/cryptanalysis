// Build with clang++ -std=c++17 -O3 -mcpu=native. Supply the 17 archived
// abscissae on stdin, in any order. Times include lookup and output writes.
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <random>
#include <vector>

using Word = std::uint32_t;
constexpr Word p = 2147483647;
constexpr std::array<unsigned char,8> offsets{0,1,7,5,2,3,6,16};
unsigned slot(Word x) { return ((x >> 7) + offsets[x % 8]) % 17; }

int main() {
    std::array<Word,17> sorted{}, compact{};
    std::array<Word,64> sliced{};
    compact.fill(p);
    sliced.fill(p);
    for (auto& x : sorted) {
        if (!(std::cin >> x) || x >= p) return 1;
        const auto s = slot(x), t = (x >> 10) % 64;
        if (compact[s] != p || sliced[t] != p) return 2;
        compact[s] = sliced[t] = x;
    }
    std::sort(sorted.begin(), sorted.end());
    std::mt19937 rng(20261123);
    std::vector<Word> queries(1 << 17);
    std::vector<unsigned char> out(queries.size()), expected(out.size());
    std::cout << "hit_percent,round,kernel,ns_per_query\n";
    for (unsigned hits : {0u,50u,100u}) {
        for (std::size_t i = 0; i < queries.size(); ++i) {
            Word x;
            do { x = rng() % p; } while (std::binary_search(sorted.begin(), sorted.end(), x));
            queries[i] = i < queries.size()*hits/100 ? sorted[rng()%17] : x;
        }
        std::shuffle(queries.begin(), queries.end(), rng);
        auto scan = [&](auto lookup, auto& dst) {
            std::transform(queries.begin(), queries.end(), dst.begin(), lookup);
        };
        auto binary = [&](Word x) { return std::binary_search(sorted.begin(), sorted.end(), x); };
        scan(binary, expected);
        for (int round = 0; round < 18; ++round) {
            for (int j = 0; j < 3; ++j) {
                int arm = (round + (round/3%2 ? 2-j : j)) % 3;
                auto start = std::chrono::steady_clock::now();
                if (arm == 0) scan(binary,out);
                if (arm == 1) scan([&](Word x){return compact[slot(x)] == x;},out);
                if (arm == 2) scan([&](Word x){return sliced[(x>>10)%64] == x;},out);
                auto elapsed = std::chrono::steady_clock::now() - start;
                if (out != expected) return 3;
                if (round >= 6) std::cout << hits << ',' << round-6 << ',' <<
                    std::array{"binary","compact","slice"}[arm] << ',' <<
                    std::chrono::duration<double,std::nano>(elapsed).count()/queries.size() << '\n';
            }
        }
    }
}
