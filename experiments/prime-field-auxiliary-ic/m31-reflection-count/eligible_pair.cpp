// Full-field and auxiliary-eligible lift counts. Each row is ordered as
// neither, twist only, original only, both. Compile with a C++17 compiler.
#include <array>
#include <cinttypes>
#include <cstdint>
#include <cstdio>
#include <vector>

using Word = std::uint64_t;
constexpr Word p = (Word{1} << 31) - 1;

int main() {
    std::vector<Word> squares((p + 63) / 64);
    for (Word y = 0; y <= p / 2; ++y) {
        const Word value = y * y % p;
        squares[value >> 6] |= Word{1} << (value & 63);
    }
    auto square = [&](Word value) {
        return (squares[value >> 6] >> (value & 63)) & 1;
    };

    std::array<Word, 4> full{}, eligible{};
    ++full[2 * square(14) + square(p - 14)]; // Zero has no distinct partner.
    for (Word x = 1; x <= p / 2; ++x) {
        const Word xx = x * x % p;
        const Word z = (xx * x + 2 * x) % p;
        const Word original = square((z + 14) % p);
        const Word twist = square((z + p - 14) % p);
        const Word cell = 2 * original + twist;
        const Word reflected = 2 * (1 - twist) + (1 - original);
        ++full[cell];
        ++full[reflected];
        if (!square((xx + 1) % p))
            ++eligible[square(x) ? reflected : cell];
    }
    for (const auto& row : {full, eligible})
        std::printf("%" PRIu64 " %" PRIu64 " %" PRIu64 " %" PRIu64 "\n",
                    row[0], row[1], row[2], row[3]);
}
