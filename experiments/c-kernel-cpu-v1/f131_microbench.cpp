// Frozen direct-operation workload for the #880 ECC2K-130 historical claims.
// Build this same file on each pinned revision. Define F131_BENCH_BASE on the
// old side (packed polynomial arithmetic); the candidate side calls f131.h.
// --fingerprint runs the frozen recurrence without collecting a timing value.
#include "cpuknobs.h"
#include "packed131.h"
#ifndef F131_BENCH_BASE
#include "f131.h"
#endif

#include <array>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>

namespace {
using P = eccPacked131::P131;

uint64_t splitmix64(uint64_t *state)
{
    uint64_t z = (*state += UINT64_C(0x9E3779B97F4A7C15));
    z = (z ^ (z >> 30)) * UINT64_C(0xBF58476D1CE4E5B9);
    z = (z ^ (z >> 27)) * UINT64_C(0x94D049BB133111EB);
    return z ^ (z >> 31);
}

P multiply(P a, P b)
{
#ifdef F131_BENCH_BASE
    return eccPacked131::mulPolynomial131(a, b);
#else
    return f131::toPacked(f131::mul(f131::fromPacked(a), f131::fromPacked(b)));
#endif
}

P square(P a)
{
#ifdef F131_BENCH_BASE
    return eccPacked131::squarePolynomial131(a);
#else
    return f131::toPacked(f131::sqr(f131::fromPacked(a)));
#endif
}

P reference_mul_power(P a, P b, unsigned long long exponent)
{
    P result{{1, 0, 0, 0, 0}};
    while (exponent) {
        if (exponent & 1) result = eccPacked131::mulPolynomial131(result, b);
        exponent >>= 1;
        if (exponent) b = eccPacked131::mulPolynomial131(b, b);
    }
    return eccPacked131::mulPolynomial131(a, result);
}

uint64_t digest(const std::array<P, 8> &values)
{
    uint64_t h = UINT64_C(0x6A09E667F3BCC909);
    for (const auto &v : values)
        for (uint32_t limb : v.v) {
            h ^= uint64_t(limb) + UINT64_C(0x9E3779B97F4A7C15) + (h << 6) + (h >> 2);
            h = (h ^ (h >> 30)) * UINT64_C(0xBF58476D1CE4E5B9);
        }
    return h ^ (h >> 31);
}
}

int main(int argc, char **argv)
{
    const bool fingerprint_only = argc == 5 && !std::strcmp(argv[4], "--fingerprint");
    if ((argc != 4 && !fingerprint_only) ||
        (std::strcmp(argv[1], "mul") && std::strcmp(argv[1], "sqr"))) {
        std::fprintf(stderr, "usage: f131_microbench <mul|sqr> <iterations> <seed> [--fingerprint]\n");
        return 2;
    }
    char *end = nullptr;
    const unsigned long long iterations = std::strtoull(argv[2], &end, 10);
    if (!iterations || iterations > 10000000 || argv[2][0] == '-' || !end || *end) return 2;
    const unsigned long long seed = std::strtoull(argv[3], &end, 0);
    if (!end || *end) return 2;

    std::array<P, 8> x{}, y{};
    uint64_t rng = seed;
    for (size_t i = 0; i < x.size(); ++i) {
        for (uint32_t &word : x[i].v) word = uint32_t(splitmix64(&rng));
        x[i].v[4] &= 7u;
        for (uint32_t &word : y[i].v) word = uint32_t(splitmix64(&rng));
        y[i].v[4] &= 7u;
    }
    const bool do_square = !std::strcmp(argv[1], "sqr");
    auto step = [&]() {
        for (size_t i = 0; i < x.size(); ++i) x[i] = do_square ? square(x[i]) : multiply(x[i], y[i]);
    };
    for (uint64_t i = 0; i < 10000; ++i) step();
    long long ns = 0;
    if (fingerprint_only) {
        for (unsigned long long i = 0; i < iterations; ++i) step();
    } else {
        const auto begin = std::chrono::steady_clock::now();
        for (unsigned long long i = 0; i < iterations; ++i) step();
        const auto finish = std::chrono::steady_clock::now();
        ns = std::chrono::duration_cast<std::chrono::nanoseconds>(finish - begin).count();
    }

    bool verified = true;
    uint64_t check_rng = seed;
    for (size_t i = 0; i < x.size(); ++i) {
        P initial_x{}, initial_y{};
        for (uint32_t &word : initial_x.v) word = uint32_t(splitmix64(&check_rng));
        initial_x.v[4] &= 7u;
        for (uint32_t &word : initial_y.v) word = uint32_t(splitmix64(&check_rng));
        initial_y.v[4] &= 7u;
        P expected = initial_x;
        const auto total_iterations = iterations + 10000;
        if (do_square) {
            for (unsigned long long j = 0; j < total_iterations % 131; ++j)
                expected = eccPacked131::squarePolynomial131(expected);
        } else {
            expected = reference_mul_power(initial_x, initial_y, total_iterations);
        }
        verified = verified && std::memcmp(expected.v, x[i].v, sizeof(expected.v)) == 0;
    }
    if (!verified) {
        std::fprintf(stderr, "f131 microbenchmark result disagrees with packed polynomial reference\n");
        return 1;
    }
    if (fingerprint_only)
        std::printf("{\"status\":\"ok\",\"op\":\"%s\",\"lanes\":8,\"iterations\":%llu,"
                    "\"verified\":1,\"result\":\"%016llx\"}\n",
                    do_square ? "sqr" : "mul", iterations, (unsigned long long)digest(x));
    else
        std::printf("{\"status\":\"ok\",\"op\":\"%s\",\"lanes\":8,\"iterations\":%llu,"
                    "\"online_ms\":%.6f,\"verified\":1,\"result\":\"%016llx\"}\n",
                    do_square ? "sqr" : "mul", iterations, (double)ns / 1e6,
                    (unsigned long long)digest(x));
    return 0;
}
