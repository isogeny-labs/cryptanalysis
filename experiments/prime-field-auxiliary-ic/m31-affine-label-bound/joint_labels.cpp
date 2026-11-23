// clang++ -O3 -std=c++17 joint_labels.cpp -o joint_labels
// Enumerate nonzero squares once, then classify the two cubics at every x.
#include <array>
#include <cstdint>
#include <cstdio>
#include <vector>

constexpr uint32_t p = (1u << 31) - 1;

uint32_t addMod(uint32_t a, uint32_t b) {
    uint32_t s = a + b;
    return s >= p ? s - p : s;
}

int main() {
    std::vector<uint64_t> squares((uint64_t(p) + 63) / 64);
    uint32_t square = 0;
    for (uint32_t y = 0; y < p/2; ++y) {
        square = addMod(square, 2*y + 1);
        squares[square/64] |= uint64_t(1) << (square%64);
    }
    auto label = [&](uint32_t value) {
        return (squares[value/64] >> (value%64)) & 1;
    };

    // Forward differences of x^3+2x+14 at x=0 are 3, 6, 6.
    uint32_t first = 14, delta = 3, delta2 = 6;
    std::array<uint64_t,4> counts{};
    std::array<uint32_t,2> zeros{};
    for (uint32_t x = 0; x < p; ++x) {
        const uint32_t second = addMod(first,22);
        ++counts[2*label(first) + label(second)];
        zeros[0] += first == 0;
        zeros[1] += second == 0;
        first = addMod(first,delta);
        delta = addMod(delta,delta2);
        delta2 = addMod(delta2,6);
    }
    std::puts("lift14,lift36,coordinates");
    for (unsigned i = 0; i < counts.size(); ++i)
        std::printf("%u,%u,%llu\n", i/2, i%2, static_cast<unsigned long long>(counts[i]));
    return zeros[0] || zeros[1] || counts[2]+counts[3] != 1073752646 ||
           counts[1]+counts[3] != 1073753100;
}
