#define main archived_join_main
#include "../n41_w8_ninepair_join_control_20261012/join9.cpp"
#undef main
#include <sstream>
#include <unordered_set>

struct PairState {
    Point point;
    unsigned a, b;
};

int main(int argc, char** argv) {
    try {
        if (argc != 4) throw std::runtime_error("usage: sample pairs.tsv output.tsv count");
        const size_t requested = std::stoull(argv[3]);
        std::ifstream input(argv[1]);
        std::string tag;
        int slots, targets;
        input >> tag >> slots >> targets;
        if (tag != "ECC2K41_ALLSEED4" || slots != 4 || targets != 4)
            throw std::runtime_error("source header mismatch");
        std::array<std::vector<PairState>,2> states;
        while (input >> tag) {
            std::string tail;
            std::getline(input, tail);
            if (tag != "S") continue;
            std::istringstream row(tail);
            int slot, sid, source_a, source_b, a, b, sa, sb;
            uint64_t x, y;
            row >> slot >> sid >> source_a >> source_b >> a >> b >> sa >> sb >> x >> y;
            if (slot < 0 || slot >= 4 || !row || a == b || sa < 0 || sa > 1 || sb < 0 || sb > 1)
                throw std::runtime_error("bad state row");
            if (slot < 2) {
                if (sid != int(states[slot].size())) throw std::runtime_error("state order mismatch");
                states[slot].push_back({{x,y,false},unsigned(a),unsigned(b)});
            }
        }
        if (states[0].size() != 30952 || states[1].size() != 30952)
            throw std::runtime_error("unexpected state count");
        std::ofstream output(argv[2]);
        if (!output) throw std::runtime_error("cannot write output");
        output << "slot0_sid\tslot1_sid\tx\treciprocal_x\n";
        uint64_t rng = 0x5d5e26b88125a773ULL;
        auto draw = [&]() {
            rng ^= rng >> 12; rng ^= rng << 25; rng ^= rng >> 27;
            return rng * 0x2545f4914f6cdd1dULL;
        };
        std::unordered_set<uint64_t> seen;
        seen.reserve(requested * 2);
        size_t attempted = 0, overlap = 0, identity = 0, zero_x = 0, duplicate = 0;
        while (seen.size() < requested) {
            if (++attempted > requested * 4) throw std::runtime_error("sampling attempt cap");
            unsigned i = draw() % states[0].size(), j = draw() % states[1].size();
            const auto &left = states[0][i], &right = states[1][j];
            if (left.a == right.a || left.a == right.b || left.b == right.a || left.b == right.b) {
                ++overlap; continue;
            }
            Point sum = add(left.point, right.point);
            if (sum.infinity) {++identity; continue;}
            if (sum.x == 0) {++zero_x; continue;}
            if (!seen.insert(sum.x).second) {++duplicate; continue;}
            output << i << '\t' << j << '\t' << sum.x << '\t' << inv(sum.x) << '\n';
        }
        std::cerr << "requested=" << requested << " attempted=" << attempted
                  << " overlap=" << overlap << " identity=" << identity
                  << " zero_x=" << zero_x << " duplicate_x=" << duplicate << '\n';
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n'; return 1;
    }
}
