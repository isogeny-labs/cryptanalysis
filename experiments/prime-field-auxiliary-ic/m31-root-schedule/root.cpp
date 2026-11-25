#include "root.h"
#include <algorithm>

#if defined(__aarch64__) && !defined(M31_ROOT_PORTABLE)
#include "kernel.hpp"
#endif

extern "C" void m31_checked_roots(const uint32_t* input, uint32_t* output, size_t count) {
#if defined(__aarch64__) && !defined(M31_ROOT_PORTABLE)
    const size_t bulk = count - count % 32;
    m31root::scheduled<true, 8>(input, output, bulk);
    if (count != bulk) {
        uint32_t tail[32]{};
        std::copy_n(input + bulk, count - bulk, tail);
        m31root::scheduled<true, 8>(tail, tail, 32);
        std::copy_n(tail, count - bulk, output + bulk);
    }
#else
    constexpr uint32_t p = 2147483647;
    for (size_t i = 0; i < count; ++i) {
        uint64_t x = input[i], y = x;
        for (unsigned j = 0; j < 29; ++j) y = y * y % p;
        output[i] = y * y % p == x ? std::min<uint64_t>(y, p - y) : p;
    }
#endif
}
