#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <vector>

using Word = std::uint32_t;
using Clock = std::chrono::steady_clock;
constexpr Word empty = UINT32_MAX;

// Restart a fixed, basis-independent multiplier sequence for every build.
static Word next_multiplier(Word& state) {
    state ^= state << 13;
    state ^= state >> 17;
    state ^= state << 5;
    return state | 1u;
}

template<unsigned Bits>
static unsigned run(bool perfect, const std::vector<Word>& keys,
                    const std::vector<Word>& queries, std::vector<unsigned char>& result) {
    constexpr unsigned size = 1u << Bits;
    std::array<Word,size> table;
    table.fill(empty);
    Word multiplier = 2654435761u, state = 1;
    unsigned attempts = 0;
    if (perfect) {
        std::array<unsigned,size> stamp{};
        for (;;) {
            if (++attempts > 1000000) return 0;
            multiplier = next_multiplier(state);
            bool collision = false;
            for (Word key : keys) {
                unsigned slot = (key * multiplier) >> (32 - Bits);
                if (stamp[slot] == attempts) { collision = true; break; }
                stamp[slot] = attempts;
            }
            if (!collision) break;
        }
    }
    for (Word key : keys) {
        unsigned slot = (key * multiplier) >> (32 - Bits);
        while (table[slot] != empty) slot = (slot + 1) & (size - 1);
        table[slot] = key;
    }
    for (std::size_t i = 0; i < queries.size(); ++i) {
        Word key = queries[i];
        unsigned slot = (key * multiplier) >> (32 - Bits);
        if (!perfect)
            while (table[slot] != empty && table[slot] != key) slot = (slot + 1) & (size - 1);
        result[i] = table[slot] == key;
    }
    return perfect ? attempts : 1;
}

int main(int argc, char** argv) {
    if (argc != 3) return 2;
    std::ifstream bf(argv[1]), qf(argv[2]);
    std::vector<Word> keys, queries;
    for (Word x; bf >> x;) keys.push_back(x);
    for (Word x; qf >> x;) queries.push_back(x);
    if (keys.size() != 195 || queries.size() != 32768) return 2;
    auto sorted = keys;
    std::sort(sorted.begin(), sorted.end());
    std::vector<unsigned char> expected, result(queries.size());
    for (Word x : queries) expected.push_back(std::binary_search(sorted.begin(), sorted.end(), x));
    std::cout << "block,bits,perfect,attempts,total_ns\n";
    for (unsigned b = 0; b < 50; ++b) {
        for (unsigned j = 0; j < 3; ++j) {
            unsigned bits = 11 + (b+j)%3;
            for (unsigned k = 0; k < 2; ++k) {
                bool perfect = (k+b)%2;
                auto start = Clock::now();
                unsigned tries = bits == 11 ? run<11>(perfect,keys,queries,result) :
                                 bits == 12 ? run<12>(perfect,keys,queries,result) :
                                              run<13>(perfect,keys,queries,result);
                auto ns = std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-start).count();
                if (!tries || result != expected) return 3;
                if (b >= 2) std::cout << b-2 << ',' << bits << ',' << perfect << ',' << tries << ',' << ns << '\n';
            }
        }
    }
}
