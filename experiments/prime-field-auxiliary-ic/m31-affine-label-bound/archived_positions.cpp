// Locate supplied public receipt labels in the archived coefficient stream.
#include <array>
#include <cstdint>
#include <iostream>
#include <random>
#include <vector>

using Word = std::uint64_t;
constexpr Word order = 2147505293;
struct Label { Word a, b; };

int main() {
    unsigned seed, width;
    Word limit;
    if (!(std::cin >> seed >> width >> limit) || seed > 2 || (width != 1 && width != 64))
        return 1;
    std::vector<Label> wanted;
    std::array<bool,65536> prefix{};
    Label row;
    while (std::cin >> row.a >> row.b) {
        wanted.push_back(row);
        prefix[row.a % prefix.size()] = true;
    }
    if (wanted.empty()) return 1;
    std::mt19937_64 rng(20261115 + seed);
    auto fresh = [&]() -> Label { return {rng()%order, rng()%order}; };
    std::array<Label,32> steps;
    for (auto& step : steps) step = fresh();
    std::vector<Label> lanes(width);
    for (auto& lane : lanes) lane = fresh();
    for (Word q = 1; q <= limit; ++q) {
        unsigned index = (q-1) % width;
        auto& lane = lanes[index];
        auto step = steps[rng() & 31];
        lane = {(lane.a+step.a)%order, (lane.b+step.b)%order};
        if (prefix[lane.a % prefix.size()])
            for (size_t i = 0; i < wanted.size(); ++i)
                if (lane.a == wanted[i].a && lane.b == wanted[i].b)
                    std::cout << i+1 << ',' << q << ',' << index << '\n';
    }
}
