// Replay public PRNG coefficients only. Input: seed, final query, then the
// archived coefficient pairs in receipt order. Output: one-based query, zero-based lane.
#include <array>
#include <cstdint>
#include <iostream>
#include <random>
#include <utility>
#include <vector>

int main() {
    using U = uint64_t;
    using Pair = std::pair<U,U>;
    constexpr U n = 2147505293;
    U seed, limit;
    if (!(std::cin >> seed >> limit)) return 1;
    std::vector<Pair> receipts;
    U a, b;
    while (std::cin >> a >> b) receipts.emplace_back(a,b);
    if (!std::cin.eof() || receipts.empty()) return 1;
    std::mt19937_64 rng(20261115 + seed);
    auto pair = [&]() -> Pair { return {rng()%n, rng()%n}; };
    std::array<Pair,32> steps;
    std::array<Pair,64> lanes;
    for (auto& step : steps) step = pair();
    for (auto& lane : lanes) lane = pair();
    size_t next = 0;
    for (U q=1; q<=limit; ++q) {
        size_t j = (q-1)%lanes.size();
        auto& lane = lanes[j];
        const auto& step = steps[rng()&31];
        lane.first = (lane.first+step.first)%n;
        lane.second = (lane.second+step.second)%n;
        if (lane == receipts[next]) {
            std::cout << q << ' ' << j << '\n';
            if (++next == receipts.size()) return q == limit ? 0 : 2;
        }
    }
    return 3;
}
