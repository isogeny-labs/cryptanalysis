// Independent translation check via explicit quadratic-residue membership.
#include <array>
#include <cstdint>
#include <cstdio>
#include <vector>

int main() {
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
    std::array<uint64_t,4> cells{};
    uint64_t prev=lift(p-1);
    for (uint64_t x=0; x<p; ++x) {
        uint64_t curr=lift(x);
        ++cells[2*prev+curr];
        prev=curr;
    }
    std::puts("source,destination,coordinates");
    for (unsigned i=0; i<4; ++i)
        std::printf("%u,%u,%llu\n",i/2,i%2,(unsigned long long)cells[i]);
}
