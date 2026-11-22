#define main archived_join_main
#include "../n41_w8_ninepair_join_control_20261012/join9.cpp"
#undef main
#include <unordered_set>

int main(int argc, char** argv) {
    if (argc != 4) return 1;
    const size_t requested = std::stoull(argv[3]);
    const char* paths[2] = {argv[1], argv[2]};
    const uint64_t seeds[2] = {0x17cc3f818415c90bULL, 0x860d42c7ea9815b3ULL};
    for (unsigned mode = 0; mode < 2; ++mode) {
        std::ofstream out(paths[mode]);
        if (!out) return 1;
        uint64_t rng = seeds[mode];
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
            if (!u || (u & 1) || seen.count(u)) continue;
            if (mode == 1 && (inv(u) & 1)) continue;
            seen.insert(u);
            out << u << '\n';
        }
        std::cerr << "mode=" << mode << " accepted=" << seen.size()
                  << " attempted=" << attempted << '\n';
    }
}
