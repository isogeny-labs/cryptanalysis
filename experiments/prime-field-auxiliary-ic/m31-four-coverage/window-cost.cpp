#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <random>
#include <vector>

using Word = std::uint32_t;
using Keys = std::array<Word,17>;
constexpr Word prime = 2147483647;
constexpr std::array<int,10> offsets{0,1,3,4,9,12,15,17,19,21};

bool scan(const Keys& keys, Word x) {
    Word found = 0;
    for (Word k : keys) found |= (k == x);
    return found != 0;
}

int choose(const Keys& keys) {
    for (int shift : offsets) {
        std::array<std::uint64_t,2> seen{};
        bool collision = false;
        for (Word x : keys) {
            Word slot = (x >> shift) & 127;
            auto mask = UINT64_C(1) << (slot & 63);
            auto& word = seen[slot >> 6];
            if (word & mask) { collision = true; break; }
            word |= mask;
        }
        if (!collision) return shift;
    }
    return -1;
}

int main(int argc, char** argv) {
    if (argc != 2) return 1;
    std::mt19937 rng(std::stoul(argv[1]));
    std::vector<Keys> bases(4096);
    for (auto& keys : bases)
        for (auto& x : keys)
            if (!(std::cin >> x) || x >= prime) return 2;
    std::shuffle(bases.begin(), bases.end(), rng);
    std::cout << "queries,round,method,ns_per_base\n";
    for (int count : {1,4,16,64,256,1024}) {
        std::vector<Word> queries(bases.size()*count);
        std::vector<unsigned char> expected(queries.size()), out(queries.size());
        for (size_t i=0; i<queries.size(); ++i) {
            const auto& keys = bases[i/count];
            Word x = (rng() & 1) ? keys[rng()%keys.size()] : rng()%prime;
            queries[i] = x;
            expected[i] = std::find(keys.begin(),keys.end(),x) != keys.end();
        }
        for (int round=0; round<9; ++round) for (int j=0; j<3; ++j) {
            int arm = (round + (round/3%2 ? 2-j : j))%3;
            auto start = std::chrono::steady_clock::now();
            for (size_t b=0; b<bases.size(); ++b) {
                const auto& keys = bases[b];
                auto apply = [&](auto lookup) {
                    for (int i=0; i<count; ++i) out[b*count+i] = lookup(queries[b*count+i]);
                };
                if (arm==0) apply([&](Word x){return scan(keys,x);});
                if (arm==1) {
                    auto sorted = keys;
                    std::sort(sorted.begin(),sorted.end());
                    apply([&](Word x){return std::binary_search(sorted.begin(),sorted.end(),x);});
                }
                if (arm==2) {
                    int shift = choose(keys);
                    if (shift<0) { apply([&](Word x){return scan(keys,x);}); continue; }
                    std::array<Word,128> table;
                    table.fill(prime);
                    for (Word x : keys) table[(x>>shift)&127] = x;
                    apply([&](Word x){return table[(x>>shift)&127] == x;});
                }
            }
            auto elapsed = std::chrono::steady_clock::now()-start;
            if (expected!=out) return 3;
            if (round>=3) std::cout << count << ',' << round-3 << ',' <<
                std::array{"scan","sort","window"}[arm] << ',' <<
                std::chrono::duration<double,std::nano>(elapsed).count()/bases.size() << '\n';
        }
    }
}
