// Read the 195 unsigned x coordinates, one per line, from standard input.
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <vector>

using Word = std::uint32_t;

// Every completion must select a bit from the first unhit pair difference.
// Partition the branches by the first such bit selected. Excluding earlier
// choices preserves completeness and avoids revisiting the same completion.
static bool can_separate(const std::vector<Word>& differences, Word chosen,
                         Word available, unsigned budget) {
    for (Word difference : differences) {
        if (difference & chosen) continue;
        if (budget == 0) return false;
        Word choices = difference & available;
        while (choices) {
            const Word bit = choices & -choices;
            choices ^= bit;
            available ^= bit;
            if (can_separate(differences, chosen | bit, available, budget - 1))
                return true;
        }
        return false;
    }
    return true;
}

int main() {
    std::vector<Word> coordinates;
    for (Word x; std::cin >> x;) coordinates.push_back(x);
    if (coordinates.size() != 195) return 2;

    std::vector<Word> differences;
    for (std::size_t i = 0; i < coordinates.size(); ++i)
        for (std::size_t j = 0; j < i; ++j)
            differences.push_back(coordinates[i] ^ coordinates[j]);
    std::sort(differences.begin(), differences.end(), [](Word a, Word b) {
        const int ac = __builtin_popcount(a), bc = __builtin_popcount(b);
        return ac == bc ? a < b : ac < bc;
    });

    constexpr Word witness = 0x1520944e;
    const bool upper = __builtin_popcount(witness) == 11 &&
        std::all_of(differences.begin(), differences.end(),
                    [](Word d) { return (d & witness) != 0; });
    const bool smaller = can_separate(differences, 0, 0x7fffffff, 10);
    std::cout << "11-bit witness valid=" << upper
              << " separating mask of at most 10 bits exists=" << smaller << '\n';
    return upper && !smaller ? 0 : 1;
}
