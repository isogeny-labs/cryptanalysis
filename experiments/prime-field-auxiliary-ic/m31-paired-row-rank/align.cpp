// Reconstruct only the archived public trial identifiers for matching log rows.
#include <array>
#include <cstdint>
#include <iostream>
#include <random>
#include <utility>
int main() {
    uint64_t order, seed, trials;
    if (!(std::cin >> order >> seed >> trials) || order == 0) return 1;
    std::mt19937_64 rng(20261114 + seed);
    std::array<std::pair<uint64_t,uint64_t>,32> steps;
    for (auto& [a,b]:steps) { a=rng()%order; b=rng()%order; }
    uint64_t a=rng()%order, b=rng()%order;
    for (uint64_t t=0; t<trials; ++t) {
        auto [da,db]=steps[rng()%steps.size()];
        a=(a+da)%order; b=(b+db)%order;
        std::cout << a << ' ' << b << '\n';
    }
}
