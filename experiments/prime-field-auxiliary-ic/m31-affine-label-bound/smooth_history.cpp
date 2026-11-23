// Exact conditional distribution on the existing bound-47 smooth-orbit population.
#ifdef BATCH_HISTORY
#include "../m31-native-product/product.h"
#endif
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <unordered_set>
#include <vector>

using Word = std::uint64_t;
constexpr Word p = 2147483647;
Word rotate(Word x) { return (2*x & p) | (x >> 30); }

bool square(Word x) {
#ifdef CHECK_JACOBI
    if (x == 0) return true;
    Word n = p;
    int sign = 1;
    while (x) {
        while (!(x & 1)) {
            x >>= 1;
            if (n % 8 == 3 || n % 8 == 5) sign = -sign;
        }
        if (x % 4 == 3 && n % 4 == 3) sign = -sign;
        std::swap(x, n);
        x %= n;
    }
    return sign == 1;
#else
    Word y = x;
    for (unsigned i = 0; i < 30; ++i) y = y*y % p;
    return x == y;
#endif
}

Word rhs(Word x) { return ((x*x % p)*x + 2*x + 14) % p; }

using Counts = std::array<unsigned,2048>;
#ifdef BATCH_HISTORY
void squarePowers(const uint32_t* inputs, uint32_t* powers, size_t n) {
    m31_products(inputs, inputs, powers, n);
    for (unsigned i = 1; i < 30; ++i)
        m31_products(powers, powers, powers, n);
}

class Histories {
    static constexpr size_t capacity = 32;
    std::array<uint32_t, 11*capacity> inputs, powers;
    size_t used = 0;

public:
    void append(Word x, Counts& counts) {
        Word offset = (x+p-10) % p;
        for (size_t j = 0; j < 11; ++j) {
            inputs[11*used+j] = rhs(offset);
            if (++offset == p) offset = 0;
        }
        if (++used == capacity) flush(counts);
    }

    void flush(Counts& counts) {
        if (!used) return;
        const size_t n = 11*used;
        squarePowers(inputs.data(), powers.data(), n);
        for (size_t i = 0; i < n; i += 11) {
            unsigned index = 0;
            for (size_t j = i; j < i+11; ++j)
                index = 2*index + (powers[j] == inputs[j]);
            ++counts[index];
        }
        used = 0;
    }
};
#endif

int main() {
    std::vector<Word> smooth{1};
    for (Word q : {3,5,7,11,13,17,19,23,29,31,37,41,43,47}) {
        const auto before = smooth.size();
        for (size_t i = 0; i < before; ++i)
            for (Word v = q*smooth[i]; v < p; v *= q) smooth.push_back(v);
    }
    std::unordered_set<Word> seen;
    Counts counts{};
#ifdef BATCH_HISTORY
    Histories histories;
#endif
    for (Word v : smooth) {
        Word key = v;
        for (Word x = rotate(v); x != v; x = rotate(x)) key = std::min(key,x);
        if (!seen.insert(key).second || square(key)) continue;
#ifdef BATCH_HISTORY
        // Doubling is a permutation of order 31 on these nonzero coordinates.
        // Rotating the square twice tracks (2x)^2 with no new multiplication.
        std::array<uint32_t,32> inputs{}, powers;
        Word xx = key*key % p;
        for (unsigned j = 0; j < 31; ++j) {
            inputs[j] = xx+1 == p ? 0 : xx+1;
            xx = rotate(rotate(xx));
        }
        squarePowers(inputs.data(), powers.data(), inputs.size());
        Word x = key;
        for (unsigned j = 0; j < 31; ++j) {
            if (inputs[j] != powers[j]) histories.append(x, counts);
            x = rotate(x);
        }
#else
        Word x = key;
        do {
            if (!square((x*x + 1) % p)) {
                unsigned index = 0;
                Word offset = (x+p-10) % p;
                for (unsigned j = 0; j <= 10; ++j) {
                    index = 2*index + square(rhs(offset));
                    if (++offset == p) offset = 0;
                }
                ++counts[index];
            }
            x = rotate(x);
        } while (x != key);
#endif
    }
#ifdef BATCH_HISTORY
    histories.flush(counts);
#endif
    std::puts("history,successor,count");
    for (unsigned i = 0; i < counts.size(); ++i)
        std::printf("%u,%u,%u\n",i/2,i%2,counts[i]);
}
