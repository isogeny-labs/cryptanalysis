#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>

using Word = uint64_t;
using Counts = std::array<std::array<Word, 3>, 3>;

static unsigned euler(Word v, Word p) {
    if (!v) return 0;
    Word r = 1;
    for (Word k = (p-1)/2; k; k >>= 1) {
        if (k & 1) r = r*v % p;
        v = v*v % p;
    }
    return r == 1 ? 1 : 2;
}

static Word add(Word a, Word b, Word p) {
    Word s = a+b;
    return s >= p ? s-p : s;
}

static Counts census(Word p) {
    std::vector<Word> squares((p+63)/64);
    Word sq = 0, odd = 1;
    for (Word y = 1; y <= (p-1)/2; ++y) {
        sq = add(sq, odd, p);
        odd = add(odd, 2, p);
        squares[sq/64] |= Word(1) << (sq%64);
    }
    auto character = [&](Word v) -> unsigned {
        if (!v) return 0;
        return squares[v/64] & (Word(1) << (v%64)) ? 1 : 2;
    };
    Counts counts{};
    // f=x^3+x, first difference 3x^2+3x+2, second difference 6x+6.
    Word f=0, delta=2, second=6;
    for (Word x=0; x<p; ++x) {
        Word g = add(add(f,x,p),14,p);
        auto a = character(f), b = character(g);
        if (p < 10000 || x % 524287 == 0) {
            Word cube = ((x*x)%p)*x%p;
            Word actual_f=(cube+x)%p, actual_g=(cube+2*x+14)%p;
            if (f!=actual_f || g!=actual_g || a!=euler(actual_f,p) || b!=euler(actual_g,p))
                std::abort();
        }
        ++counts[a][b];
        f=add(f,delta,p);
        delta=add(delta,second,p);
        second=add(second,6,p);
    }
    return counts;
}

int main() {
    std::puts("p,auxiliary_character,target_character,x_count");
    const int chars[] = {0,1,-1};
    for (Word p : {31U,127U,8191U,2147483647U}) {
        auto counts=census(p);
        for (unsigned a=0;a<3;++a)
            for (unsigned b=0;b<3;++b)
                std::printf("%llu,%d,%d,%llu\n",(unsigned long long)p,chars[a],chars[b],
                            (unsigned long long)counts[a][b]);
        std::fflush(stdout);
    }
}
