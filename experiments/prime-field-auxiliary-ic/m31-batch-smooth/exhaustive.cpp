// Differential check for the full canonical field domain. Link with b16.cpp.
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <vector>

extern "C" std::size_t m31_smooth211(std::uint32_t*, std::size_t);

constexpr std::uint32_t modulus = 2147483647;
constexpr std::uint32_t half = modulus / 2;

static std::vector<unsigned> primes_through(unsigned bound) {
    std::vector<unsigned> primes;
    for (unsigned n = 2; n <= bound; ++n) {
        if (std::none_of(primes.begin(), primes.end(),
                         [n](unsigned q) { return n % q == 0; }))
            primes.push_back(n);
    }
    return primes;
}

// Enumerate positive smooth integers by their unique sorted prime factors.
static void mark_products(std::vector<bool>& smooth, const std::vector<unsigned>& primes,
                          unsigned value, std::size_t first) {
    smooth[value] = true;
    for (std::size_t i = first; i < primes.size(); ++i) {
        if (value > half / primes[i]) break;
        mark_products(smooth, primes, value * primes[i], i);
    }
}

int main() {
    std::vector<bool> smooth(half + 1);
    mark_products(smooth, primes_through(211), 1, 0);
    // Vary the length to exercise every possible final lane count.
    std::vector<std::uint32_t> xs(65536), expected;
    expected.reserve(xs.size());
    std::uint64_t accepted = 0;
    unsigned block = 0;
    for (unsigned start = 0; start < modulus; ++block) {
        const unsigned count = std::min(65536u - block % 16, modulus - start);
        expected.clear();
        for (unsigned i = 0; i < count; ++i) {
            const unsigned x = start + i;
            xs[i] = x;
            if (smooth[std::min(x, modulus - x)]) expected.push_back(x);
        }
        const auto kept = m31_smooth211(xs.data(), count);
        if (kept != expected.size() || !std::equal(expected.begin(), expected.end(), xs.begin())) {
            std::fprintf(stderr, "Mismatch in block starting at %u\n", start);
            return 1;
        }
        accepted += kept;
        start += count;
    }
    std::printf("coordinates=%u blocks=%u accepted=%llu\n", modulus, block,
                static_cast<unsigned long long>(accepted));
}
