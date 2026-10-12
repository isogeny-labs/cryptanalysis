#define main archived_join_main
#include "../n41_w8_ninepair_join_control_20261012/join9.cpp"
#undef main
#include <unordered_set>

int main(int argc, char** argv) {
    if (argc != 3) return 1;
    size_t requested = std::stoull(argv[2]);
    std::ofstream out(argv[1]);
    if (!out) return 1;
    uint64_t rng = 0x32827f19ca770e51ULL;
    auto draw = [&]() {
        rng ^= rng >> 12; rng ^= rng << 25; rng ^= rng >> 27;
        return rng * 0x2545f4914f6cdd1dULL;
    };
    std::unordered_set<uint64_t> seen;
    seen.reserve(requested * 2);
    size_t attempted = 0;
    while (seen.size() < requested) {
        ++attempted;
        uint64_t u = draw() & ((1ULL << 41) - 1);
        if (!u || seen.count(u)) continue;
        uint64_t x = inv(u), z = x ^ u, trace = 0;
        for (unsigned i = 0; i < 41; ++i) {trace ^= z; z = sqr(z);}
        if (trace != 0) continue;
        seen.insert(u);
        out << u << '\n';
    }
    std::cerr << "curve_valid_reciprocals=" << seen.size()
              << " attempted=" << attempted << '\n';
}
