#include <cstddef>
#include <cstdint>

// P is a compile-time divisor, allowing the compiler to lower both the
// divisibility test and exact quotient without a hardware division.
template<std::uint32_t P>
static bool strip(std::uint32_t& value) {
    while (value % P == 0) value /= P;
    return value <= 211;
}

template<std::uint32_t... Primes>
static bool smooth(std::uint32_t value) {
    return value != 0 && (strip<Primes>(value) || ...);
}

// Compact canonical field coordinates in input order.
extern "C" std::size_t m31_smooth211(std::uint32_t* xs, std::size_t n) {
    constexpr std::uint32_t p=2147483647;
    std::size_t kept=0;
    for (std::size_t i=0;i<n;++i) {
        const auto x=xs[i];
        const auto v=x<p-x ? x : p-x;
        if (smooth<2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,
                   67,71,73,79,83,89,97,101,103,107,109,113,127,131,137,
                   139,149,151,157,163,167,173,179,181,191,193,197,199,211>(v))
            xs[kept++]=x;
    }
    return kept;
}
