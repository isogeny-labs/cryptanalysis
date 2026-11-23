// Independent translation check via explicit quadratic-residue membership.
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>

template<unsigned history>
int census() {
    constexpr uint64_t p = 2147483647;
    std::vector<uint64_t> squares((p+63)/64);
    for (uint64_t y=0; y<=p/2; ++y) {
        uint64_t u = y*y%p;
        squares[u/64] |= uint64_t(1) << (u%64);
    }
    auto lift = [&](uint64_t x) {
        uint64_t u = ((x*x%p)*x+2*x+14)%p;
        return (squares[u/64] >> (u%64)) & 1;
    };
    std::array<uint64_t, 2u << history> cells{};
    unsigned code = 0;
    auto prepend = [&](uint64_t x) { code = (code >> 1) | (unsigned(lift(x)) << history); };
    for (unsigned x = history; x > 0; --x) prepend(x-1);
    for (uint64_t x = p; x > 0; --x) {
        prepend(x-1);
        ++cells[code];
    }
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
