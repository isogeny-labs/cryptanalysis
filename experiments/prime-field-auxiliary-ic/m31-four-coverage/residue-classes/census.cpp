#include <array>
#include <cinttypes>
#include <cstdio>
#include <vector>
#include <string_view>

using W = std::uint64_t;
constexpr W p = 2147483647, generator = 7;
constexpr W class_size = (p-1)/462;

W power(W x, W n) {
    W result=1;
    for (; n; n/=2) {
        if (n%2) result=result*x%p;
        x=x*x%p;
    }
    return result;
}

int main(int argc, char **argv) {
    const bool full = argc == 2 && std::string_view(argv[1]) == "--full";
    if (argc != 1 && !full) return 4;
    // Distinct prime factors of p-1 certify the order of the generator.
    for (W q : {2,3,7,11,31,151,331})
        if (power(generator,(p-1)/q)==1) return 1;
    std::vector<W> squares((p+63)/64);
    for (W y=1;y<=p/2;++y) {
        W z=y*y%p;
        squares[z/64] |= W{1} << (z%64);
    }
    auto sq=[&](W z){return (squares[z/64]>>(z%64))&1;};
    const W step=power(generator,462), cube_step=power(step,3);
    std::array<W,4> total{};
    std::array<std::array<W,4>,462> rows{};
    for (unsigned k=0;k<(full ? 462u : 231u);++k) {
        const W start=power(generator,k);
        W x=start, cube=power(x,3);
        std::array<W,4> counts{};
        for (W i=0;i<class_size;++i) {
            W a=(cube+2*x+14)%p, b=(cube+2*x+p-14)%p;
            if (!a || !b) return 2;
            ++counts[2*sq(a)+sq(b)];
            x=x*step%p;
            cube=cube*cube_step%p;
        }
        if (x!=start || cube!=power(start,3)) return 3;
        rows[k] = counts;
        // Negation shifts the class by 231 and sends (a,b) to (-b,-a).
        // Since -1 is nonsquare and neither value vanishes, both bits flip.
        if (!full) rows[k+231] = {counts[3], counts[1], counts[2], counts[0]};
    }
    for (unsigned k=0;k<rows.size();++k) {
        const auto &counts = rows[k];
        for (unsigned j=0;j<4;++j) total[j]+=counts[j];
        std::printf("%u,%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 "\n",k,counts[0],counts[1],counts[2],counts[3]);
    }
    ++total[2*sq(14)+sq(p-14)];
    return total!=std::array<W,4>{536844426,536886575,536908220,536844426};
}
