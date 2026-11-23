// clang++ -std=c++17 -O3 smooth_joint_labels.cpp -o smooth_joint_labels
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <vector>

constexpr uint64_t p = (1ULL << 31) - 1;

// Euler's criterion with the common zero convention used by the archived census.
bool square(uint64_t x) {
    uint64_t power = x;
    for (unsigned i = 0; i < 30; ++i) power = power * power % p;
    return power == x;
}

// Enumerate all odd smooth representatives, expand each orbit, then sort and
// deduplicate coordinates. Factors of two only move within a doubling orbit.
std::vector<uint32_t> populationCandidates() {
    std::vector<uint32_t> smooth{1};
    for (uint32_t q : {3,5,7,11,13,17,19,23,29,31,37,41,43,47}) {
        size_t before = smooth.size();
        for (size_t i = 0; i < before; ++i)
            for (uint64_t v = uint64_t(q)*smooth[i]; v < p; v *= q)
                smooth.push_back(static_cast<uint32_t>(v));
    }
    std::vector<uint32_t> coordinates;
    coordinates.reserve(31 * smooth.size());
    for (uint32_t v : smooth) {
        uint64_t x = v;
        do {
            coordinates.push_back(static_cast<uint32_t>(x));
            x = (2*x) % p;
        } while (x != v);
    }
    std::sort(coordinates.begin(), coordinates.end());
    coordinates.erase(std::unique(coordinates.begin(), coordinates.end()), coordinates.end());
    return coordinates;
}

int main() {
    std::array<unsigned, 4> counts{};
    for (uint64_t x : populationCandidates()) {
        uint64_t xx = x*x % p;
        if (square(x) || square((xx+1)%p)) continue;
        uint64_t common = (xx*x + 2*x) % p;
        bool a = square((common+14)%p);
        bool b = square((common+36)%p);
        ++counts[2*a+b];
    }
    std::puts("lift14,lift36,coordinates");
    for (unsigned i = 0; i < counts.size(); ++i)
        std::printf("%u,%u,%u\n", i/2, i%2, counts[i]);
    // Known first-curve marginal from the separate history table.
    return counts[2]+counts[3] != 925398 || counts[0]+counts[1] != 927469;
}
