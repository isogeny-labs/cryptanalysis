// Independent enumeration of square values of x^3 + 2x +/- 14 over F_p.
// Build with c++ -std=c++17 -O3 twist-overlap.cpp -o /tmp/twist-overlap
#include <cstdint>
#include <iostream>
#include <vector>

constexpr std::uint32_t p = 2147483647;

std::uint32_t add(std::uint32_t a, std::uint32_t b) {
    const auto sum = a + b;
    return sum >= p ? sum - p : sum;
}

int main() {
    std::vector<std::uint64_t> squares((p + 63ULL) / 64);
    for (std::uint64_t y = 1; y <= p / 2; ++y) {
        const auto residue = y * y % p;
        squares[residue / 64] |= std::uint64_t{1} << (residue % 64);
    }
    const auto square = [&](std::uint32_t value) {
        return (squares[value / 64] >> (value % 64)) & 1;
    };

    std::uint32_t cubic = 0, delta = 3, second = 6;
    std::uint64_t left = 0, right = 0, both = 0, zeros = 0;
    for (std::uint32_t x = 0; x < p; ++x) {
        const auto a = add(cubic, 14), b = add(cubic, p - 14);
        const auto l = square(a), r = square(b);
        left += l;
        right += r;
        both += l & r;
        zeros += (a == 0 || b == 0);
        // Forward differences for x^3 + 2x start at 0, 3, 6, 6.
        cubic = add(cubic, delta);
        delta = add(delta, second);
        second = add(second, 6);
    }
    std::cout << "left " << left << " right " << right << " both " << both
              << " zero abscissae " << zeros << '\n';
    return !(left == 1073752646 && right == 1073731001 && both == 536844426 && zeros == 0);
}
