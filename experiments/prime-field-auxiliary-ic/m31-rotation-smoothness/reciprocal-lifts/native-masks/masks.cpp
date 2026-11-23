#include "../../../m31-native-product/product.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>

namespace {
using Word = std::uint32_t;
using Wide = std::uint64_t;
constexpr Word p = 2147483647;
#ifdef M31_BOUND_211
constexpr unsigned expected_pairs = 104580;
#else
constexpr unsigned expected_pairs = 3302;
#endif
using MaskSet = std::array<Word, 5>;

Word rotate(Word x, unsigned shift) {
    return ((x << shift) & p) | (x >> (31-shift));
}

Word multiply(Word x, Word y) { return Wide(x) * y % p; }

#ifdef M31_DIRECT_INVERSE_MASKS
Word inverse(Word x) {
    Word result = 1;
    for (Word e = p-2; e; e >>= 1) {
        if (e & 1) result = multiply(result, x);
        x = multiply(x, x);
    }
    return result;
}
#endif

MaskSet lift_masks(Word x) {
    Word cube = multiply(multiply(x, x), x);
#ifdef M31_DIRECT_INVERSE_MASKS
    Word inv = inverse(x);
    Word inv_cube = multiply(multiply(inv, inv), inv);
#else
    Word twist_term = multiply(14, multiply(cube, x));
#endif
    alignas(16) Word rhs[5 * 32]{};
    for (unsigned i = 0; i < 31; ++i) {
        const Wide center = cube + 2ULL*x;
        rhs[i] = (Wide(cube) + x) % p;
        rhs[32+i] = (center + 14) % p;
        rhs[64+i] = (center + p - 14) % p;
#ifdef M31_DIRECT_INVERSE_MASKS
        const Wide other_center = inv_cube + 2ULL*inv;
        rhs[96+i] = (other_center + 14) % p;
        rhs[128+i] = (other_center + p - 14) % p;
        inv = rotate(inv, 30);
        inv_cube = rotate(inv_cube, 28);
#else
        const Wide other_center = x + 2ULL*cube;
        rhs[96+i] = (other_center + twist_term) % p;
        rhs[128+i] = (other_center + p - twist_term) % p;
        twist_term = rotate(twist_term, 4);
#endif
        x = rotate(x, 1);
        cube = rotate(cube, 3);
    }
    alignas(16) Word powers[5 * 32];
    std::copy_n(rhs, 160, powers);
    for (unsigned i = 0; i < 30; ++i) m31_products(powers, powers, powers, 160);
    MaskSet masks{};
    for (unsigned j = 0; j < masks.size(); ++j)
        for (unsigned i = 0; i < 31; ++i)
            masks[j] |= Word(powers[32*j+i] == rhs[32*j+i]) << i;
    return masks;
}
}

int main(int argc, char** argv) {
    const bool audit = argc == 2 && std::strcmp(argv[1], "--masks") == 0;
    if (argc != 1 && !audit) return 2;
    Word sums[31][5]{};
    unsigned pairs = 0;
    Word x;
    int status;
    while ((status = std::scanf("%u", &x)) == 1) {
        if (!x || x >= p || pairs == expected_pairs) return 2;
        ++pairs;
        const auto m = lift_masks(x);
        if (audit) {
            std::printf("%u %u %u %u %u %u\n", x, m[0], m[1], m[2], m[3], m[4]);
            continue;
        }
        const MaskSet left{m[0], m[1], m[2], m[0]&m[1], m[0]&m[2]};
        const MaskSet right{m[0], m[3], m[4], m[0]&m[3], m[0]&m[4]};
        for (unsigned phase = 0; phase < 31; ++phase)
            for (unsigned j = 0; j < left.size(); ++j)
                sums[phase][j] += __builtin_popcount(left[j] & rotate(right[j], phase));
    }
    if (status != EOF || std::ferror(stdin) || pairs != expected_pairs) return 2;
    if (!audit) {
        std::puts("phase,coordinates,aux_joint,curve_joint,twist_joint,aux_curve_joint,aux_twist_joint");
        for (unsigned i = 0; i < 31; ++i)
            std::printf("%u,%u,%u,%u,%u,%u,%u\n", i, pairs*31, sums[i][0], sums[i][1],
                        sums[i][2], sums[i][3], sums[i][4]);
    }
    return std::fflush(stdout) != 0;
}
