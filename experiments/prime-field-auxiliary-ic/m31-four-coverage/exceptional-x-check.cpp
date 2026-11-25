#include "exceptional-x.hpp"
#include <algorithm>
#include <cstdio>
#include <limits>

int main() {
    using namespace m31_exceptional;
    if (!std::is_sorted(coordinates.begin(), coordinates.end())) return 1;
    auto next = coordinates.begin();
    for (uint32_t x = 0; x <= modulus; ++x) {
        bool expected = next != coordinates.end() && *next == x;
        if (contains(x) != expected) {
            std::fprintf(stderr, "lookup mismatch at %u\n", x);
            return 1;
        }
        if (expected) ++next;
    }
    return next != coordinates.end() || contains(std::numeric_limits<uint32_t>::max());
}
