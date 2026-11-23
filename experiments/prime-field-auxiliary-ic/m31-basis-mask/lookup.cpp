#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <unordered_set>
#include <vector>

using Word = std::uint32_t;
constexpr Word empty = std::numeric_limits<Word>::max();

static unsigned projection(Word x) {
    constexpr unsigned bits[] = {1,2,3,6,10,12,15,21,24,26,28};
    unsigned label = 0;
    for (unsigned j = 0; j < 11; ++j)
        label |= ((x >> bits[j]) & 1u) << j;
    return label;
}

template<class Table, class Lookup>
static void scan(const Table& table, Lookup lookup, const std::vector<Word>& queries,
                 std::vector<unsigned char>& output) {
    for (std::size_t i = 0; i < queries.size(); ++i)
        output[i] = lookup(table, queries[i]);
}

int main(int argc, char** argv) {
    if (argc != 3) return 2;
    std::vector<Word> basis, queries;
    std::ifstream basis_file(argv[1]), query_file(argv[2]);
    for (Word x; basis_file >> x;) basis.push_back(x);
    for (Word x; query_file >> x;) queries.push_back(x);
    if (basis.size() != 195 || queries.size() != 32768) return 2;
    auto sorted = basis;
    std::sort(sorted.begin(), sorted.end());
    std::vector<unsigned char> expected(queries.size()), output(queries.size());
    auto binary = [](const auto& t, Word x) { return std::binary_search(t.begin(), t.end(), x); };
    scan(sorted, binary, queries, expected);
    if (std::count(expected.begin(), expected.end(), 1) != 195) return 2;
    std::array<unsigned,3> order = {0,1,2};
    std::cout << "block,arm,wall_ns\n";
    for (unsigned block = 0; block < 66; ++block) {
        for (unsigned arm : order) {
            auto start = std::chrono::steady_clock::now();
            if (arm == 0) {
                auto t = basis;
                std::sort(t.begin(), t.end());
                scan(t, binary, queries, output);
            } else if (arm == 1) {
                std::unordered_set<Word> t;
                t.reserve(basis.size());
                t.insert(basis.begin(), basis.end());
                scan(t, [](const auto& h, Word x) { return h.count(x) != 0; }, queries, output);
            } else {
                std::array<Word,2048> t;
                t.fill(empty);
                for (Word x : basis) {
                    auto slot = projection(x);
                    if (t[slot] != empty) return 3;
                    t[slot] = x;
                }
                scan(t, [](const auto& h, Word x) { return h[projection(x)] == x; }, queries, output);
            }
            auto ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
                std::chrono::steady_clock::now() - start).count();
            if (output != expected) return 4;
            if (block >= 6) std::cout << block-6 << ',' << arm << ',' << ns << '\n';
        }
        std::next_permutation(order.begin(), order.end());
    }
}
