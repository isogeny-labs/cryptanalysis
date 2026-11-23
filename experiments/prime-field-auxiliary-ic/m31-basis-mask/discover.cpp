#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <string_view>
#include <unordered_set>
#include <vector>

using Word = std::uint32_t;
using Clock = std::chrono::steady_clock;

static Word discover(const std::vector<Word>& basis, bool deduplicate) {
    std::vector<Word> pairs;
    pairs.reserve(basis.size() * (basis.size() - 1) / 2);
    for (std::size_t i = 0; i < basis.size(); ++i)
        for (std::size_t j = 0; j < i; ++j)
            pairs.push_back(basis[i] ^ basis[j]);
    if (deduplicate) {
        std::sort(pairs.begin(), pairs.end());
        pairs.erase(std::unique(pairs.begin(), pairs.end()), pairs.end());
    }
    Word mask = 0;
    while (!pairs.empty()) {
        std::array<unsigned,31> counts{};
        for (unsigned j = 0; j < counts.size(); ++j)
            for (Word x : pairs) counts[j] += (x >> j) & 1u;
        auto best = std::max_element(counts.begin(), counts.end());
        if (*best == 0) return 0;
        Word bit = 1u << (best - counts.begin());
        mask |= bit;
        pairs.erase(std::remove_if(pairs.begin(), pairs.end(),
                    [bit](Word x) { return (x & bit) != 0; }), pairs.end());
    }
    return mask;
}

struct Projection {
    std::array<std::array<unsigned,256>,4> bytes{};
    std::array<Word,2048> slots;
    explicit Projection(Word mask) {
        slots.fill(UINT32_MAX);
        unsigned position = 0;
        for (unsigned bit = 0; bit < 31; ++bit) {
            if (!(mask & (1u << bit))) continue;
            for (unsigned v = 0; v < 256; ++v)
                bytes[bit / 8][v] |= ((v >> (bit % 8)) & 1u) << position;
            ++position;
        }
    }
    unsigned label(Word x) const {
        return bytes[0][x & 255] | bytes[1][(x >> 8) & 255] |
               bytes[2][(x >> 16) & 255] | bytes[3][x >> 24];
    }
};

// Integer-key baseline using the same 2,048 key slots as the projection.
struct FlatSet {
    std::array<Word,2048> slots;
    FlatSet() { slots.fill(UINT32_MAX); }
    unsigned locate(Word x) const {
        unsigned i = (x * 2654435761u) >> 21;
        while (slots[i] != UINT32_MAX && slots[i] != x)
            i = (i + 1) & 2047u;
        return i;
    }
};

int main(int argc, char** argv) {
    const bool compare_pairs = argc == 4 && std::string_view(argv[3]) == "--compare-pairs";
    const bool compare_flat = argc == 4 && std::string_view(argv[3]) == "--compare-flat";
    if (argc != 3 && !compare_pairs && !compare_flat) return 2;
    std::ifstream bf(argv[1]), qf(argv[2]);
    std::vector<Word> basis, queries;
    for (Word x; bf >> x;) basis.push_back(x);
    for (Word x; qf >> x;) queries.push_back(x);
    if (basis.size() != 195 || queries.size() != 32768) return 2;
    auto sorted = basis;
    std::sort(sorted.begin(), sorted.end());
    std::vector<unsigned char> expected, result(queries.size());
    for (Word x : queries) expected.push_back(std::binary_search(sorted.begin(), sorted.end(), x));
    std::cout << "block,scans,arm,discovery_ns,total_ns\n";
    const std::array<unsigned,4> scans_per_build = compare_flat ? std::array<unsigned,4>{1,2,4,8} : std::array<unsigned,4>{1,8,16,32};
    std::array<unsigned,3> arms = {0,1,2};
    for (unsigned block = 0; block < (compare_pairs ? 66u : 26u); ++block) {
        for (unsigned scans : scans_per_build) {
            if (compare_pairs && scans != 1) continue;
            auto scan = [&](auto contains) {
                for (unsigned r = 0; r < scans; ++r) {
                    for (std::size_t i = 0; i < queries.size(); ++i)
                        result[i] = contains(queries[i]);
                    std::atomic_signal_fence(std::memory_order_seq_cst);
                }
            };
            for (unsigned order = 0; order < (compare_pairs ? 3u : 2u); ++order) {
                const unsigned arm = compare_pairs ? arms[order] : (order + block) % 2;
                auto start = Clock::now();
                long long discovery = 0;
                if (compare_flat && arm == 0) {
                    FlatSet table;
                    for (Word x : basis) table.slots[table.locate(x)] = x;
                    scan([&](Word x) { return table.slots[table.locate(x)] == x; });
                } else if (arm == 0) {
                    std::unordered_set<Word> table;
                    table.reserve(basis.size());
                    table.insert(basis.begin(), basis.end());
                    scan([&](Word x) { return table.count(x) != 0; });
                } else {
                    Word mask = discover(basis, !compare_flat && arm == 1);
                    discovery = std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-start).count();
                    if (__builtin_popcount(mask) != 11) return 3;
                    Projection table(mask);
                    for (Word x : basis) {
                        auto& slot = table.slots[table.label(x)];
                        if (slot != UINT32_MAX) return 3;
                        slot = x;
                    }
                    scan([&](Word x) { return table.slots[table.label(x)] == x; });
                }
                auto total = std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-start).count();
                if (result != expected) return 4;
                const unsigned warmups = compare_pairs ? 6u : 2u;
                if (block >= warmups) std::cout << block-warmups << ',' << scans << ',' << arm << ',' << discovery << ',' << total << '\n';
            }
        }
        if (compare_pairs) std::next_permutation(arms.begin(), arms.end());
    }
}
