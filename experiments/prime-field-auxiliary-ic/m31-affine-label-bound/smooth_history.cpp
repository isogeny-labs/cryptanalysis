// Exact conditional distribution on the existing bound-47 smooth-orbit population.
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

bool lift(Word x) {
    return square(((x*x % p)*x + 2*x + 14) % p);
}

int main() {
    std::vector<Word> smooth{1};
    for (Word q : {3,5,7,11,13,17,19,23,29,31,37,41,43,47}) {
        const auto before = smooth.size();
        for (size_t i = 0; i < before; ++i)
            for (Word v = q*smooth[i]; v < p; v *= q) smooth.push_back(v);
    }
    std::unordered_set<Word> seen;
    std::array<unsigned,2048> counts{};
    for (Word v : smooth) {
        Word key = v;
        for (Word x = rotate(v); x != v; x = rotate(x)) key = std::min(key,x);
        if (!seen.insert(key).second || square(key)) continue;
        Word x = key;
        do {
            if (!square((x*x + 1) % p)) {
                unsigned index = 0;
                Word offset = (x+p-10) % p;
                for (unsigned j = 0; j <= 10; ++j) {
                    index = 2*index + lift(offset);
                    if (++offset == p) offset = 0;
                }
                ++counts[index];
            }
            x = rotate(x);
        } while (x != key);
    }
    std::puts("history,successor,count");
    for (unsigned i = 0; i < counts.size(); ++i)
        std::printf("%u,%u,%u\n",i/2,i%2,counts[i]);
}
