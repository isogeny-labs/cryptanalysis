// Exact W29 source-edge census for first-mask low eight bits equal to three.
#define main archived_w23_geometry_main
#include "../../koblitz-s5-invariant-20260924/lowpoly_w23_geometry.cpp"
#undef main

#include <chrono>
#include <iostream>
#include <stdexcept>
#include <sys/resource.h>

int main() {
    try {
        constexpr uint32_t seed = 898618;
        constexpr uint32_t prefix = 3;
        const Fe trace = trace_mask();
        uint64_t eligible = 0, left_inverse_trace_zero = 0;
        uint64_t right_inverse_trace_zero = 0, inverse_checks = 0;
        uint32_t first_eligible = 0, last_eligible = 0;
        auto start = std::chrono::steady_clock::now();
        for (uint32_t index = 0; index < (1u << 20); ++index) {
            uint32_t a = prefix | ((index & ((1u << 11) - 1)) << 8) |
                         ((index >> 11) << 20);
            uint32_t b = a ^ seed;
            if (a >= b || b >= (1u << 29) || (a & 255) != prefix ||
                (a & (1u << 19))) throw std::runtime_error("canonical mask");
            Fe wa{uint64_t(a) << 1, 0, 0};
            Fe wb{uint64_t(b) << 1, 0, 0};
            if (trace_bit(wa, trace) || trace_bit(wb, trace))
                throw std::runtime_error("source trace");
            Fe ia = inverse(wa), ib = inverse(wb);
            if (!(mul(wa, ia) == Fe{1, 0, 0}) ||
                !(mul(wb, ib) == Fe{1, 0, 0}))
                throw std::runtime_error("inverse replay");
            inverse_checks += 2;
            bool va = !trace_bit(ia, trace);
            bool vb = !trace_bit(ib, trace);
            left_inverse_trace_zero += va;
            right_inverse_trace_zero += vb;
            if (va && vb) {
                if (!first_eligible) first_eligible = a;
                last_eligible = a;
                ++eligible;
            }
        }
        rusage usage{};
        getrusage(RUSAGE_SELF, &usage);
        double seconds = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - start).count();
        std::cout << "{\"status\":\"COMPLETE_PREFIX_CENSUS\","
                  << "\"prefix\":" << prefix << ",\"canonical_masks\":1048576,"
                  << "\"eligible_edges\":" << eligible << ","
                  << "\"left_inverse_trace_zero\":" << left_inverse_trace_zero << ","
                  << "\"right_inverse_trace_zero\":" << right_inverse_trace_zero << ","
                  << "\"inverse_checks\":" << inverse_checks << ","
                  << "\"first_eligible\":" << first_eligible << ","
                  << "\"last_eligible\":" << last_eligible << ","
                  << "\"self_wall_seconds\":" << seconds << ","
                  << "\"ru_maxrss_raw\":" << usage.ru_maxrss << "}\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "ERROR " << error.what() << "\n";
        return 2;
    }
}
