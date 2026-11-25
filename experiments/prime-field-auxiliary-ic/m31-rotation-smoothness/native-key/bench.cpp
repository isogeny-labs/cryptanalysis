#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>

using Word = std::uint32_t;
using Wide = std::uint64_t;
constexpr Word p = 2147483647;
constexpr Word primes[] = {3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67};

Word mul(Word a, Word b) {
    Wide z = Wide(a) * b;
    Word folded = Word(z >> 31) + Word(z & p);
    return folded >= p ? folded - p : folded;
}
Word power(Word a, Word e) {
    Word out = 1;
    for (; e; e >>= 1) {
        if (e & 1) out = mul(out, a);
        a = mul(a, a);
    }
    return out;
}
// Each reciprocal pair occupies two adjacent possible codes. Parity
// records the orientation, so the encoding preserves the entire key set.
Word encode(Word k, Word inv) {
    return 2 * std::min(k, inv) + (k > inv);
}
enum class Mode { direct, batch, carry };
struct Factor { Word prime, key, inverse; bool negative; };
struct Result { std::vector<Word> codes; size_t pairs; };

template<Mode mode>
void visit(const std::vector<Factor>& factors, size_t first, Word x, bool neg,
           Word k, Word inv, std::vector<Word>& out) {
    if (neg) {
        if constexpr (mode == Mode::direct) out.push_back(power(x, 31));
        if constexpr (mode == Mode::batch) out.push_back(k);
        if constexpr (mode == Mode::carry) out.push_back(encode(k, inv));
    }
    for (size_t i = first; i < factors.size(); ++i) {
        const auto& f = factors[i];
        Wide next = Wide(x) * f.prime;
        if (next >= p) break;
        Word nk = 0, ni = 0;
        if constexpr (mode != Mode::direct) nk = mul(k, f.key);
        if constexpr (mode == Mode::carry) ni = mul(inv, f.inverse);
        visit<mode>(factors, i, Word(next), neg != f.negative, nk, ni, out);
    }
}

template<Mode mode>
Result census(Word bound) {
    std::vector<Factor> factors;
    for (Word q : primes) {
        if (q > bound) break;
        Word k = 0, inv = 0;
        if constexpr (mode != Mode::direct) k = power(q,31);
        if constexpr (mode == Mode::carry) inv = power(k,p-2);
        factors.push_back({q,k,inv,power(q,(p-1)/2) == p-1});
    }
    std::vector<Word> codes;
    visit<mode>(factors,0,1,false,1,1,codes);
    if constexpr (mode != Mode::carry) {
        std::vector<Word> prefix(codes.size());
        Word product = 1;
        for (size_t i = 0; i < codes.size(); ++i) {
            prefix[i] = product;
            product = mul(product,codes[i]);
        }
        Word inverse = power(product,p-2);
        for (size_t i = codes.size(); i-- > 0;) {
            Word k = codes[i];
            codes[i] = encode(k,mul(inverse,prefix[i]));
            inverse = mul(inverse,k);
        }
    }
    std::sort(codes.begin(),codes.end());
    codes.erase(std::unique(codes.begin(),codes.end()),codes.end());
    size_t pairs = 0;
    for (size_t i = 1; i < codes.size(); ++i)
        pairs += ((codes[i-1] ^ codes[i]) == 1);
    return {std::move(codes),pairs};
}

int main() {
    using Clock = std::chrono::steady_clock;
    using Runner = Result (*)(Word);
    const Runner run[] = {census<Mode::direct>,census<Mode::batch>,census<Mode::carry>};
    const char* names[] = {"direct","batch","carry"};
    const int orders[][3] = {{0,1,2},{1,2,0},{2,0,1},{2,1,0},{1,0,2},{0,2,1}};
    std::puts("bound,round,position,mode,ms,orbits,pairs");
    for (Word b : {47,67}) {
        const Result ref = census<Mode::direct>(b);
        for (int round = 0; round < 12; ++round) {
            for (int pos = 0; pos < 3; ++pos) {
                int m = orders[round % 6][pos];
                auto start = Clock::now();
                Result result = run[m](b);
                double ms = std::chrono::duration<double,std::milli>(Clock::now()-start).count();
                if (result.codes != ref.codes || result.pairs != ref.pairs) return EXIT_FAILURE;
                std::printf("%u,%d,%d,%s,%.6f,%zu,%zu\n",b,round,pos,names[m],
                            ms,result.codes.size(),result.pairs);
            }
        }
    }
}
