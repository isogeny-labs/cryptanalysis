// All admissible N41 first-code pairs: quadratic evaluation rank of third-code unions.
#define main reference_join_main
#include "../n41_w8_fixedseed_ordinary_join_20261013/join7.cpp"
#undef main

#include <algorithm>
#include <iomanip>
#include <set>

constexpr unsigned MONOMIALS = 1 + 41 + 41*40/2;
constexpr unsigned WORDS = (MONOMIALS + 63)/64;
using Feature = std::array<uint64_t, WORDS>;

void set_bit(Feature& out, unsigned bit) { out[bit/64] |= 1ULL << (bit%64); }

Feature quadratic_features(uint64_t x) {
    Feature out{};
    set_bit(out, 0);
    for (unsigned i=0; i<41; ++i) {
        if (!((x >> i) & 1)) continue;
        set_bit(out, 1+i);
        for (unsigned j=i+1; j<41; ++j) {
            if (!((x >> j) & 1)) continue;
            unsigned pair_index = 42 + i*40 - i*(i-1)/2 + (j-i-1);
            set_bit(out, pair_index);
        }
    }
    return out;
}

struct Basis {
    std::array<Feature, MONOMIALS> rows{};
    unsigned rank = 0;
    void insert(Feature value) {
        for (int word=int(WORDS)-1; word>=0; --word) {
            while (value[word]) {
                unsigned bit = word*64 + 63 - __builtin_clzll(value[word]);
                if (bit >= MONOMIALS) throw std::runtime_error("feature overflow");
                if (!rows[bit][word]) {
                    rows[bit] = value;
                    ++rank;
                    return;
                }
                for (int w=0; w<=word; ++w) value[w] ^= rows[bit][w];
            }
        }
    }
};

int main(int argc, char** argv) {
    try {
        if (argc != 2) throw std::runtime_error("usage: full_census input.tsv");
        auto start = std::chrono::steady_clock::now();
        std::ifstream input(argv[1]);
        if (!input) throw std::runtime_error("cannot open input");
        std::string tag;
        int slots, states, targets;
        input >> tag >> slots >> states >> targets;
        if (tag != "ECC2K41" || slots != 7 || states != 160 || targets != 1)
            throw std::runtime_error("input header mismatch");
        std::array<std::array<State,160>,3> lists{};
        std::array<std::array<bool,160>,3> seen{};
        unsigned source_rows=0, addition_checks=0;
        while (input >> tag) {
            if (tag == "T") {
                int idx; uint64_t x,y; input >> idx >> x >> y;
                if (idx != 0) throw std::runtime_error("target row mismatch");
            } else if (tag == "S") {
                int slot,sid,edge,c0,c1; uint64_t x,y;
                input >> slot >> sid >> edge >> c0 >> c1 >> x >> y;
                if (slot < 0 || slot >= 7 || sid < 0 || sid >= 160 ||
                    edge != sid/4 || c0 < 0 || c0 >= 128 ||
                    c1 < 0 || c1 >= 128) throw std::runtime_error("state row mismatch");
                if (slot >= 3) continue;
                if (seen[slot][sid]) throw std::runtime_error("duplicate state");
                seen[slot][sid] = true;
                lists[slot][sid] = {{x,y,false},uint8_t(edge),uint8_t(c0),uint8_t(c1)};
                ++source_rows;
            } else if (tag == "C") {
                int64_t x1,y1,x2,y2,x3,y3;
                input >> x1 >> y1 >> x2 >> y2 >> x3 >> y3;
                Point got = add({uint64_t(x1),uint64_t(y1),false},
                                {uint64_t(x2),uint64_t(y2),false});
                if ((x3<0) != got.infinity ||
                    (x3>=0 && (got.x != uint64_t(x3) || got.y != uint64_t(y3))))
                    throw std::runtime_error("Sage addition check failed");
                ++addition_checks;
            } else throw std::runtime_error("unknown input tag");
        }
        if (source_rows != 480 || addition_checks != 128)
            throw std::runtime_error("incomplete source or addition checks");
        for (auto& slot:seen) for (bool flag:slot)
            if (!flag) throw std::runtime_error("missing state");
        unsigned full=0, partial=0, empty=0;
        uint64_t code_families=0, feature_rows=0;
        std::array<unsigned, MONOMIALS+1> histogram{};
        for (unsigned a=0; a<40; ++a) {
            for (unsigned b=0; b<40; ++b) {
                Basis basis;
                unsigned valid=0, first_full_c=40;
                U128 used_ab=0;
                if (!add_columns(used_ab, lists[0][4*a]) ||
                    !add_columns(used_ab, lists[1][4*b])) {
                    ++empty;
                    std::cout << "PAIR " << a << " " << b << " EMPTY\n";
                    continue;
                }
                for (unsigned c=0; c<40; ++c) {
                    U128 used=used_ab;
                    if (!add_columns(used, lists[2][4*c])) continue;
                    ++valid;
                    if (basis.rank == MONOMIALS) continue;
                    for (unsigned i=0; i<2; ++i) {
                        for (unsigned j=0; j<4; ++j) {
                            Point ab=add(lists[0][4*a+i].point,
                                         lists[1][4*b+j].point);
                            for (unsigned k=0; k<4; ++k) {
                                Point p=add(ab, lists[2][4*c+k].point);
                                if (p.infinity) throw std::runtime_error("infinity output");
                                basis.insert(quadratic_features(p.x));
                                ++feature_rows;
                            }
                        }
                    }
                    if (basis.rank == MONOMIALS && first_full_c == 40)
                        first_full_c=c;
                }
                if (!valid) { ++empty; std::cout << "PAIR " << a << " " << b << " EMPTY\n"; continue; }
                code_families += valid;
                ++histogram[basis.rank];
                if (basis.rank == MONOMIALS) ++full; else ++partial;
                std::cout << "PAIR " << a << " " << b << " " << valid
                          << " " << basis.rank << " " << first_full_c << "\n";
            }
        }
        std::cout << "SUMMARY " << full << " " << partial << " " << empty
                  << " " << code_families << " " << feature_rows << " "
                  << std::setprecision(12) << elapsed(start) << "\n";
        for (unsigned rank=0; rank<=MONOMIALS; ++rank)
            if (histogram[rank]) std::cout << "RANK " << rank << " " << histogram[rank] << "\n";
        return 0;
    } catch (const std::exception& err) {
        std::cerr << err.what() << "\n";
        return 1;
    }
}
