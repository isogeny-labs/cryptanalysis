// Complete public lift census for x -> x+1 (including wraparound).
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>

template<unsigned history>
int census() {
    constexpr uint32_t p = 2147483647;
    std::array<uint64_t, 2u << history> cells{};
    std::array<bool, history> prefix{};
    unsigned code = 0;
    auto advance = [&](bool value) { code = (2*code+value) & (cells.size()-1); };
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
            advance(label);
            if (base+j < history) prefix[base+j] = label;
            else ++cells[code];
        }
        base += count;
    }
    for (bool label : prefix) {
        advance(label);
        ++cells[code];
    }
    uint64_t total = 0, lifts = 0;
    for (size_t i = 0; i < cells.size(); ++i) {
        total += cells[i];
        if (i & 1) lifts += cells[i];
    }
    if (total != p || lifts != (uint64_t(p)+21645)/2) return 1;
    std::puts(history == 1 ? "source,destination,coordinates" : "history,destination,coordinates");
    for (unsigned i=0; i<cells.size(); ++i)
        std::printf("%u,%u,%llu\n",i/2,i%2,(unsigned long long)cells[i]);
    return 0;
}

int main(int argc, char** argv) {
    if (argc == 1) return census<1>();
    if (argc == 2 && std::strcmp(argv[1], "history12") == 0) return census<12>();
    return 1;
}
