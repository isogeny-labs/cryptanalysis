// Aggregate coverage of the three-fold signed sumset in the additive group Z/nZ.
#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <iostream>
#include <random>
#include <set>
#include <vector>

using Word = std::uint32_t;
constexpr Word order = 2147505293U;
using Basis = std::array<Word, 500>;

Basis make_basis(unsigned seed) {
    std::mt19937 gen(seed);
    std::set<Word> used;
    Basis basis{};
    for (Word& x : basis) {
        do {
            x = gen();
        } while (x == 0 || x >= order || !used.insert(std::min(x, order - x)).second);
    }
    return basis;
}

class Bitmap {
    std::vector<std::uint64_t> bits;
public:
    explicit Bitmap(std::size_t size) : bits((size + 63) / 64) {}
    void insert(Word x) { bits[x / 64] |= UINT64_C(1) << (x % 64); }
    std::uint64_t count() const {
        std::uint64_t total = 0;
        for (auto word : bits) total += std::popcount(word);
        return total;
    }
    bool has_zero() const { return (bits.front() & 1) != 0; }
};

std::uint64_t direct(const Basis& basis) {
    std::vector<Word> terms;
    for (Word x : basis) {
        terms.push_back(x);
        terms.push_back(order - x);
    }
    Bitmap seen(order);
    for (std::size_t i = 0; i < terms.size(); ++i)
        for (std::size_t j = i; j < terms.size(); ++j) {
            std::uint64_t pair = std::uint64_t(terms[i]) + terms[j];
            for (std::size_t k = j; k < terms.size(); ++k)
                seen.insert((pair + terms[k]) % order);
        }
    return seen.count();
}

std::uint64_t folded(const Basis& basis) {
    Bitmap seen(order / 2 + 1);
    const auto record = [&](std::uint64_t sum) {
        Word x = sum % order;
        seen.insert(std::min(x, order - x));
    };
    for (std::size_t i = 0; i < basis.size(); ++i) {
        record(basis[i]);
        for (std::size_t j = i; j < basis.size(); ++j) {
            auto pair = std::uint64_t(basis[i]) + basis[j];
            for (std::size_t k = j; k < basis.size(); ++k) record(pair + basis[k]);
            for (std::size_t k = 0; k < basis.size(); ++k)
                if (k != i && k != j) record(pair + order - basis[k]);
        }
    }
    return 2 * seen.count() - seen.has_zero();
}

int main() {
    std::cout << "seed,direct,folded\n";
    for (unsigned seed : {0U, 1U, 2U}) {
        Basis basis = make_basis(seed);
        auto first = direct(basis);
        auto second = folded(basis);
        if (first != second || first > 166668000) return 1;
        std::cout << seed << ',' << first << ',' << second << std::endl;
    }
}
