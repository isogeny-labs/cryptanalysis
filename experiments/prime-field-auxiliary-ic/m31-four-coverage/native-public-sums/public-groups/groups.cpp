#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <utility>
#include <vector>

namespace {
using Row = std::pair<uint64_t, uint32_t>;

void prune(std::vector<Row>& rows, unsigned shift) {
    constexpr size_t slots = 1u << 20;
    const auto tag = [shift](const Row& row) {
        return (row.first >> shift) & (slots - 1);
    };
    std::vector<uint8_t> count(slots);
    for (const Row& row : rows) {
        auto& frequency = count[tag(row)];
        if (frequency < 2) ++frequency;
    }
    rows.erase(std::remove_if(rows.begin(), rows.end(), [&](const Row& row) {
        return count[tag(row)] < 2;
    }), rows.end());
}

void radix_sort(std::vector<Row>& rows) {
    std::vector<Row> scratch(rows.size());
    std::vector<size_t> offsets(1u << 16);
    for (unsigned shift = 0; shift < 64; shift += 16) {
        const auto tag = [shift](const Row& row) { return (row.first >> shift) & 65535; };
        std::fill(offsets.begin(), offsets.end(), 0);
        for (const Row& row : rows) ++offsets[tag(row)];
        size_t next = 0;
        for (size_t& offset : offsets) {
            const size_t count = offset;
            offset = next;
            next += count;
        }
        for (const Row& row : rows) scratch[offsets[tag(row)]++] = row;
        rows.swap(scratch);
    }
}
} // namespace

// Writes indices of repeated full keys ordered by (key, original index).
// Caller supplies n input keys and room for n output indices. Returns count,
// or -1 on invalid arguments or allocation failure. Mode 0 is the radix control.
extern "C" int64_t group_indices(const uint64_t* keys, uint32_t n, uint32_t* output,
                                 unsigned mode) noexcept {
    if (mode > 1 || (n && (!keys || !output))) return -1;
    if (n < 2) return 0;
    try {
        std::vector<Row> rows;
        rows.reserve(n);
        for (uint32_t i = 0; i < n; ++i) rows.emplace_back(keys[i], i);
        if (mode == 1) {
            prune(rows, 0);
            prune(rows, 31);
            std::sort(rows.begin(), rows.end());
        } else {
            radix_sort(rows);
        }
        size_t written = 0;
        for (size_t begin = 0, end; begin < rows.size(); begin = end) {
            end = begin + 1;
            while (end < rows.size() && rows[end].first == rows[begin].first) ++end;
            if (end - begin > 1) {
                for (size_t j = begin; j < end; ++j) output[written++] = rows[j].second;
            }
        }
        return written;
    } catch (...) {
        return -1;
    }
}
