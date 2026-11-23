// Independent reference. Visit odd smooth integers by nondecreasing factors,
// compute orbit keys directly, and find partners in a sorted vector.
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <vector>

using Word = std::uint32_t;
constexpr Word p = 2147483647;

Word power(Word x, Word n) {
    std::uint64_t b = x, r = 1;
    for (; n; n >>= 1) {
        if (n & 1) r = r*b % p;
        b = b*b % p;
    }
    return Word(r);
}

void visit(Word x, const std::vector<Word>& primes, std::size_t first, std::vector<Word>& keys) {
    if (power(x,(p-1)/2) == p-1) keys.push_back(power(x,31));
    for (auto i = first; i < primes.size(); ++i) {
        const auto product = std::uint64_t(x)*primes[i];
        if (product >= p) break;
        visit(Word(product), primes, i, keys);
    }
}

int main() {
    std::vector<Word> primes, keys;
    for (Word n = 3; n <= 211; n += 2) {
        if (std::none_of(primes.begin(), primes.end(), [n](Word q){ return n % q == 0; }))
            primes.push_back(n);
    }
    visit(1, primes, 0, keys);
    std::sort(keys.begin(), keys.end());
    keys.erase(std::unique(keys.begin(), keys.end()), keys.end());
    for (Word k : keys) {
        const Word partner = power(k,p-2);
        if (k < partner && std::binary_search(keys.begin(), keys.end(), partner))
            std::printf("%u\n", k);
    }
    return std::fflush(stdout) != 0;
}
