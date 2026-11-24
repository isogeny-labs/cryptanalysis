#define BUILD_LIBRARY
#include "native_v2.cpp"
#include <bit>
#include <cstdio>

// CHAIN_COUNT=1 uses the frozen batchPlus implementation, unchanged.
using Batch = std::array<Point, 64>;

#ifdef FUSED_CHORD
inline U foldChord(U value) {
    U sum = (value & p) + (value >> 31);
    return sum >= p ? sum - p : sum;
}
#endif

template<std::size_t Chains>
void stripedAdd(Batch& points, const Batch& steps) {
    std::array<U, 64> denominator, prefix;
    std::array<U, Chains> product, head, back;
    product.fill(1);
    for (size_t j = 0; j < points.size(); ++j) {
        size_t g = j % Chains;
        auto a = points[j], b = steps[j];
        prefix[j] = product[g];
        denominator[j] = a.inf || b.inf || a.x == b.x ? 0 : sub(b.x, a.x);
        if (denominator[j]) product[g] = mul(product[g], denominator[j]);
    }

    U total = 1;
    for (size_t g = 0; g < Chains; ++g) {
        head[g] = total;
        total = mul(total, product[g]);
    }
    U inverse = invf(total);
    for (size_t g = Chains; g-- > 0;) {
        back[g] = mul(inverse, head[g]);
        inverse = mul(inverse, product[g]);
    }
    for (size_t j = points.size(); j-- > 0;) {
        auto a = points[j], b = steps[j];
        if (!denominator[j]) {
            points[j] = plus(a, b);
            continue;
        }
        size_t g = j % Chains;
        U reciprocal = mul(back[g], prefix[j]);
        back[g] = mul(back[g], denominator[j]);
        U slope = mul(sub(b.y, a.y), reciprocal);
#ifdef FUSED_CHORD
        U x = foldChord(slope * slope + (2*p - a.x - b.x));
        points[j] = {x, foldChord(slope * sub(a.x, x) + (p - a.y)), false};
#else
        U x = sub(sub(mul(slope, slope), a.x), b.x);
        points[j] = {x, sub(mul(slope, sub(a.x, x)), a.y), false};
#endif
    }
}

int main(int argc, char** argv) {
    static_assert(std::endian::native == std::endian::little);
    static_assert(CHAIN_COUNT == 1 || CHAIN_COUNT == 2 || CHAIN_COUNT == 4);
    if (argc != 3) return 1;
    std::mt19937_64 rng(20261115 + std::stoul(argv[1]));
    size_t limit = std::stoul(argv[2]);
    curveA = 2;
    curveB = 14;
    n = 2147505293;
    Point P{1, 814455902, false}, Q{988441464, 1643383878, false};
    auto fresh = [&] {
        U a = rng() % n;
        U b = rng() % n;
        return plus(times(a, P), times(b, Q));
    };
    std::array<Point, 32> jumps;
    Batch lanes, steps;
    for (auto& jump : jumps) jump = fresh();
    for (auto& lane : lanes) lane = fresh();
    for (size_t offset = 0; offset < limit; offset += lanes.size()) {
        for (auto& step : steps) step = jumps[rng() & 31];
        if constexpr (CHAIN_COUNT == 1) batchPlus(lanes, steps);
        else stripedAdd<CHAIN_COUNT>(lanes, steps);
        std::array<uint32_t, 64> xs;
        for (size_t j = 0; j < lanes.size(); ++j)
            xs[j] = lanes[j].inf ? UINT32_MAX : lanes[j].x;
        size_t length = std::min(xs.size(), limit - offset);
        if (std::fwrite(xs.data(), sizeof(xs[0]), length, stdout) != length) return 2;
    }
    return std::fflush(stdout) != 0;
}
