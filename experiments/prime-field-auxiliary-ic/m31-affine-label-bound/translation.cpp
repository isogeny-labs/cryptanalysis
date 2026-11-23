// Complete public lift census for x -> x+1 (including wraparound).
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>

int main() {
    constexpr uint32_t p = 2147483647;
    std::array<uint64_t,4> cells{};
    bool first = false, previous = false;
    for (uint32_t base = 0; base < p;) {
        constexpr unsigned width = 64;
        const unsigned count = std::min(width, p-base);
        std::array<uint32_t,width> x{}, y{};
        for (unsigned j=0; j<count; ++j) {
            const uint64_t t = base+j;
            x[j] = (t*t%p*t + 2*t + 14) % p;
            if (!x[j]) return 1;
        }
        y=x;
        for (unsigned k=0; k<30; ++k) {
            for (unsigned j=0; j<count; ++j) {
                const uint64_t v = uint64_t(y[j])*y[j];
                const uint32_t r = (v & p) + (v >> 31);
                y[j] = r >= p ? r-p : r;
            }
        }
        for (unsigned j=0; j<count; ++j) {
            const bool label = y[j] == x[j];
            if (base+j) ++cells[2*previous+label];
            else first=label;
            previous=label;
        }
        base += count;
    }
    ++cells[2*previous+first];
    if (cells[1]!=cells[2] || cells[2]+cells[3]!=(uint64_t(p)+21645)/2) return 1;
    std::puts("source,destination,coordinates");
    for (unsigned i=0; i<4; ++i)
        std::printf("%u,%u,%llu\n",i/2,i%2,(unsigned long long)cells[i]);
}
