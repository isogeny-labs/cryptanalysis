#include <cstdio>
#include <random>

int main() {
    constexpr unsigned long long order=2147505293;
    for (int seed=0;seed<3;++seed) {
        std::mt19937_64 rng(20261115+seed);
        for (int i=0;i<32;++i) {
            auto a=rng()%order;
            auto b=rng()%order;
            std::printf("%d %llu %llu\n",seed,a,b);
        }
    }
}
