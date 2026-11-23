#include <cstdint>
#include <cstdio>
#include <cstring>
#include <unordered_map>
#include <vector>

namespace {
using Word = std::uint32_t;
using Wide = std::uint64_t;
constexpr Word p = 2147483647;
constexpr Word primes[] = {3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89};

Word multiply(Word a, Word b) {
    const Wide product = Wide(a) * b;
    const Word folded = Word(product >> 31) + Word(product & p);
    return folded >= p ? folded - p : folded;
}

Word power(Word x, Word e) {
    Word result = 1;
    for (; e; e >>= 1) {
        if (e & 1) result = multiply(result, x);
        x = multiply(x, x);
    }
    return result;
}

struct Entry {
    std::int32_t signed_value;
    Word key;
    Word inverse_key;
};

#ifdef M31_FLAT_INDEX
// A zero key marks an empty slot. Every orbit key is a power of a nonzero
// field element. Keep the ordinal in the low word for last-value updates.
class OrbitIndex {
    std::vector<Wide> slots;
    std::size_t mask;

    std::size_t locate(Word key) const {
        std::size_t i = key & mask;
        while (slots[i] && Word(slots[i] >> 32) != key)
            i = (i + 1) & mask;
        return i;
    }

public:
    explicit OrbitIndex(std::size_t max_keys) {
        std::size_t capacity = 1;
        while (capacity <= max_keys) capacity *= 2;
        slots.resize(capacity);
        mask = capacity - 1;
    }

    void record(Entry e, std::vector<Entry>& groups) {
        Wide& slot = slots[locate(e.key)];
        if (slot) {
            groups[Word(slot)] = e;
        } else {
            slot = (Wide(e.key) << 32) | groups.size();
            groups.push_back(e);
        }
    }

    bool contains(Word key) const { return slots[locate(key)] != 0; }
};
#endif
}

int main(int argc, char** argv) {
    const bool audit = argc == 2 && std::strcmp(argv[1], "--representatives") == 0;
    if (argc != 1 && !audit) return 2;
    std::vector<Entry> smooth{{1, 1, 1}};
    for (Word q : primes) {
#ifndef M31_RECOMPUTE_KEYS
        const Word factor = power(q, 31);
        const Word inverse = power(factor, p-2);
#endif
        const auto signed_q = power(q, (p-1)/2) == p-1 ? -std::int64_t(q) : std::int64_t(q);
        const auto count = smooth.size();
        for (std::size_t i = 0; i < count; ++i) {
            Entry e = smooth[i];
            auto product = e.signed_value * signed_q;
            while (-std::int64_t(p) < product && product < p) {
                e.signed_value = std::int32_t(product);
#ifndef M31_RECOMPUTE_KEYS
                e.key = multiply(e.key, factor);
                e.inverse_key = multiply(e.inverse_key, inverse);
#endif
                smooth.push_back(e);
                product *= signed_q;
            }
        }
    }

    // Python dict retains first insertion order and the last value for a key.
#ifdef M31_FLAT_INDEX
    OrbitIndex position(smooth.size());
#else
    std::unordered_map<Word, std::size_t> position;
#ifdef M31_RESERVE_INDEX
    position.reserve(smooth.size());
#endif
#endif
    std::vector<Entry> groups;
    for (Entry e : smooth) {
        if (e.signed_value >= 0) continue;
#ifdef M31_RECOMPUTE_KEYS
        e.key = power(Word(-e.signed_value), 31);
        e.inverse_key = power(e.key, p-2);
#endif
#ifdef M31_FLAT_INDEX
        position.record(e, groups);
#else
        const auto [it, inserted] = position.emplace(e.key, groups.size());
        if (inserted) groups.push_back(e);
        else groups[it->second] = e;
#endif
    }
    const auto contains = [&](Word key) {
#ifdef M31_FLAT_INDEX
        return position.contains(key);
#else
        return position.count(key) != 0;
#endif
    };
    for (const Entry& e : groups) {
        if (audit) std::printf("%u %d\n", e.key, -e.signed_value);
        else if (e.key < e.inverse_key && contains(e.inverse_key))
            std::printf("%d\n", -e.signed_value);
    }
    return std::fflush(stdout) != 0;
}
