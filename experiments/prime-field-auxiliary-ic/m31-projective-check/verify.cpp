// Check terminal values of public rational maps on canonical M31 coordinates.
#include <cstddef>
#include <cstdint>
using Word = std::uint32_t;
constexpr Word p = 2147483647;
struct Step { Word r, a, b; };

static Word plus(Word x, Word y) {
    Word s = x + y;
    return s >= p ? s - p : s;
}
static Word minus(Word x, Word y) {
    return x >= y ? x-y : x+p-y;
}
static Word mul(Word x, Word y) {
    return (std::uint64_t(x)*y) % p;
}
static Word inverse(Word x) {
    Word result = 1;
    for (Word e = p-2; e; e >>= 1) {
        if (e & 1) result = mul(result, x);
        x = mul(x, x);
    }
    return result;
}

// Inputs and step coefficients are canonical residues. Write one answer per
// input. The affine path is the same-language control for the projective path.
extern "C" void check_chain(const Word* xs, std::size_t n, const Step* steps,
                            std::size_t depth, Word target, bool projective,
                            std::uint8_t* output) {
    for (std::size_t i=0; i<n; ++i) {
        Word x = xs[i], d = 1;
        for (std::size_t j=0; j<depth; ++j) {
            const auto [r,a,b] = steps[j];
            if (projective) {
                Word u = minus(x, mul(r,d)), next_d = mul(u,d);
                x = plus(plus(mul(u,u), mul(a,next_d)), mul(b,mul(d,d)));
                d = next_d;
            } else {
                Word u = minus(x,r);
                if (!u) { d = 0; break; }
                x = plus(plus(u,a), mul(b,inverse(u)));
            }
        }
        output[i] = d != 0 && x == mul(target,d);
    }
}
