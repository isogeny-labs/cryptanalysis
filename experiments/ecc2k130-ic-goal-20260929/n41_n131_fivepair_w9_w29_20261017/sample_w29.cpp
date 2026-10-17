// Deterministic W29 canonical-mask edge sample, using the frozen N131 field kernel.
#define main archived_w23_geometry_main
#include "../../koblitz-s5-invariant-20260924/lowpoly_w23_geometry.cpp"
#undef main

#include <chrono>
#include <iostream>
#include <unordered_set>

constexpr uint32_t WIDTH = 29;
constexpr uint32_t SEED_MASK = 898618;
constexpr uint32_t CANONICAL_BIT = 1u << 19;
constexpr uint32_t SAMPLES = 1u << 16;

uint64_t splitmix64(uint64_t& state) {
    uint64_t z = (state += 0x9e3779b97f4a7c15ULL);
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

int main() {
    try {
        auto started = std::chrono::steady_clock::now();
        const Fe tr = trace_mask();
        std::unordered_set<uint32_t> chosen;
        chosen.reserve(SAMPLES * 2);
        uint64_t state = 20261017;
        uint64_t eligible_a = 0, eligible_b = 0, eligible_both = 0;
        uint64_t same_column = 0, inverse_checks = 0;
        while (chosen.size() < SAMPLES) {
            uint32_t a = uint32_t(splitmix64(state) & ((1u << WIDTH) - 1)) & ~CANONICAL_BIT;
            if (!a || !chosen.insert(a).second) continue;
            uint32_t b = a ^ SEED_MASK;
            if (b >= (1u << WIDTH) || a >= b) throw std::runtime_error("canonical rule");
            Fe wa{uint64_t(a) << 1, 0, 0};
            Fe wb{uint64_t(b) << 1, 0, 0};
            if (trace_bit(wa, tr) || trace_bit(wb, tr))
                throw std::runtime_error("source trace");
            Fe ia = inverse(wa);
            Fe ib = inverse(wb);
            if (!(mul(wa, ia) == Fe{1, 0, 0}) ||
                !(mul(wb, ib) == Fe{1, 0, 0})) throw std::runtime_error("inverse replay");
            inverse_checks += 2;
            bool va = !trace_bit(ia, tr);
            bool vb = !trace_bit(ib, tr);
            eligible_a += va;
            eligible_b += vb;
            if (!(va && vb)) continue;
            ++eligible_both;
            Fe orbit = wa;
            for (int i = 0; i < 131; ++i) {
                if (orbit == wb) { ++same_column; break; }
                orbit = square(orbit);
            }
            if (!(orbit == wa) && !(orbit == wb))
                throw std::runtime_error("Frobenius period");
        }
        rusage usage{};
        getrusage(RUSAGE_SELF, &usage);
        double seconds = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - started).count();
        std::cout << "{\"status\":\"COMPLETE_W29_SAMPLE\","
                  << "\"width\":" << WIDTH << ",\"seed_mask\":" << SEED_MASK
                  << ",\"samples\":" << SAMPLES << ",\"prng_seed\":20261017,"
                  << "\"eligible_a\":" << eligible_a
                  << ",\"eligible_b\":" << eligible_b
                  << ",\"eligible_both\":" << eligible_both
                  << ",\"same_column\":" << same_column
                  << ",\"usable_sample_edges\":" << eligible_both - same_column
                  << ",\"inverse_checks\":" << inverse_checks
                  << ",\"elapsed_wall_seconds\":" << seconds
                  << ",\"peak_self_rss_bytes\":" << usage.ru_maxrss << "}\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "ERROR " << error.what() << "\n";
        return 2;
    }
}
