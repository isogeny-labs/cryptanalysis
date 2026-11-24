#include <algorithm>
#include <chrono>
#include <bit>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

using Word = std::uint32_t;
using Clock = std::chrono::steady_clock;

// All inputs and outputs use native little-endian uint32 words on the benchmark host.
std::vector<Word> readWords(const char* path) {
    std::ifstream file(path, std::ios::binary | std::ios::ate);
    auto bytes = file.tellg();
    if (bytes < 0 || bytes % sizeof(Word)) throw std::runtime_error("invalid word file");
    std::vector<Word> words(bytes / sizeof(Word));
    file.seekg(0);
    if (!file.read(reinterpret_cast<char*>(words.data()), bytes)) throw std::runtime_error("read failed");
    return words;
}

template<bool Indexed, bool Filtered = false>
double lookup(const std::vector<Word>& table, const std::vector<Word>& queries,
              std::vector<Word>& answers) {
    // The top 12 bits of a 31-bit key select a contiguous range.
    constexpr unsigned shift = 19;
    constexpr Word buckets = 4096;
    auto start = Clock::now();
    constexpr Word residueMask = (1u << 20) - 1;
    std::vector<std::uint64_t> present;
    if constexpr (Filtered) {
        present.resize((residueMask + 1) / 64);
        for (Word key : table)
            present[(key & residueMask) >> 6] |= std::uint64_t{1} << (key & 63);
    }
    std::vector<Word> offsets;
    if constexpr (Indexed) {
        offsets.resize(buckets + 1);
        Word pos = 0;
        for (Word prefix = 0; prefix < buckets; ++prefix) {
            offsets[prefix] = pos;
            while (pos < table.size() && (table[pos] >> shift) == prefix) ++pos;
        }
        offsets[buckets] = pos;
    }
    for (std::size_t i = 0; i < queries.size(); ++i) {
        Word key = queries[i];
        if constexpr (Filtered) {
            if (((present[(key & residueMask) >> 6] >> (key & 63)) & 1) == 0) {
                answers[i] = 0;
                continue;
            }
        }
        auto first = table.begin();
        auto last = table.end();
        if constexpr (Indexed) {
            Word prefix = key >> shift;
            first = table.begin() + offsets[prefix];
            last = table.begin() + offsets[prefix + 1];
        }
        auto found = std::lower_bound(first, last, key);
        auto end = found;
        while (end != last && *end == key) ++end;
        answers[i] = static_cast<Word>(end - found);
    }
    return std::chrono::duration<double, std::micro>(Clock::now() - start).count();
}

double hashLookup(const std::vector<Word>& table, const std::vector<Word>& queries,
                  std::vector<Word>& answers) {
    struct Entry { Word key = 0; Word count = 0; };
    auto start = Clock::now();
    // Keep at least one empty slot. Zero count marks it, so key zero is valid.
    const std::size_t capacity = std::bit_ceil(std::uint64_t{2} * table.size() + 1);
    const std::size_t mask = capacity - 1;
    std::vector<Entry> entries(capacity);
    auto locate = [&](Word key) -> Entry& {
        std::size_t slot = key & mask;
        while (entries[slot].count && entries[slot].key != key)
            slot = (slot + 1) & mask;
        return entries[slot];
    };
    for (Word key : table) {
        Entry& entry = locate(key);
        entry.key = key;
        ++entry.count;
    }
    for (std::size_t i = 0; i < queries.size(); ++i)
        answers[i] = locate(queries[i]).count;
    return std::chrono::duration<double, std::micro>(Clock::now() - start).count();
}

int main(int argc, char** argv) {
    if (argc != 5) return 1;
    const std::string mode = argv[1];
    if (mode != "prefix" && mode != "binary" && mode != "hash" && mode != "filtered-prefix") return 1;
    auto table = readWords(argv[2]);
    auto queries = readWords(argv[3]);
    auto outOfRange = [](Word key) { return key >= (1u << 31); };
    if (table.size() > std::numeric_limits<Word>::max() || !std::is_sorted(table.begin(), table.end())
        || std::any_of(table.begin(), table.end(), outOfRange)
        || std::any_of(queries.begin(), queries.end(), outOfRange)) return 2;
    std::vector<Word> answers(queries.size());
    double us;
    if (mode == "hash") us = hashLookup(table, queries, answers);
    else if (mode == "filtered-prefix") us = lookup<true, true>(table, queries, answers);
    else if (mode == "prefix") us = lookup<true>(table, queries, answers);
    else us = lookup<false>(table, queries, answers);
    std::ofstream output(argv[4], std::ios::binary);
    output.write(reinterpret_cast<const char*>(answers.data()), answers.size() * sizeof(Word));
    output.close();
    if (!output) return 3;
    std::cout << us << '\n';
}
