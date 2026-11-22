// Exact N41 seven-pair join on an ordinary public point, all slots free.
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using U128 = unsigned __int128;
constexpr uint64_t MOD = (1ULL << 41) | (1ULL << 3) | 1;

uint64_t mul(uint64_t a, uint64_t b) {
    uint64_t result = 0;
    while (b) {
        if (b & 1) result ^= a;
        b >>= 1;
        a <<= 1;
        if (a & (1ULL << 41)) a ^= MOD;
    }
    return result;
}

uint64_t sqr(uint64_t a) { return mul(a, a); }

int degree(uint64_t value) {
    if (!value) throw std::runtime_error("zero polynomial in inverse");
    return 63 - __builtin_clzll(value);
}

uint64_t inv(uint64_t a) {
    if (!a) throw std::runtime_error("zero field inverse");
    uint64_t u = a, v = MOD;
    U128 g1 = 1, g2 = 0;
    while (u != 1) {
        int j = degree(u) - degree(v);
        if (j < 0) {
            std::swap(u, v);
            std::swap(g1, g2);
            j = -j;
        }
        u ^= v << j;
        g1 ^= g2 << j;
    }
    for (int bit = 127; bit >= 41; --bit)
        if ((g1 >> bit) & 1) g1 ^= U128(MOD) << (bit - 41);
    uint64_t result = static_cast<uint64_t>(g1);
    if (mul(a, result) != 1) throw std::runtime_error("inverse verification");
    return result;
}

struct Point {
    uint64_t x = 0, y = 0;
    bool infinity = true;
    bool operator==(const Point& other) const {
        return infinity == other.infinity &&
               (infinity || (x == other.x && y == other.y));
    }
};

Point negate(Point point) {
    if (!point.infinity) point.y ^= point.x;
    return point;
}

Point add(Point left, Point right) {
    if (left.infinity) return right;
    if (right.infinity) return left;
    uint64_t slope, x3, y3;
    if (left.x == right.x) {
        if (left.y != right.y || left.x == 0) return {};
        slope = left.x ^ mul(left.y, inv(left.x));
        x3 = sqr(slope) ^ slope;
        y3 = sqr(left.x) ^ mul(slope ^ 1, x3);
    } else {
        slope = mul(left.y ^ right.y, inv(left.x ^ right.x));
        x3 = sqr(slope) ^ slope ^ left.x ^ right.x;
        y3 = mul(slope, left.x ^ x3) ^ x3 ^ left.y;
    }
    return {x3, y3, false};
}

struct Hash {
    size_t operator()(const Point& point) const {
        if (point.infinity) return 0x9e3779b97f4a7c15ULL;
        uint64_t z = point.x ^ (point.y << 17) ^ (point.y >> 24);
        z ^= z >> 30; z *= 0xbf58476d1ce4e5b9ULL;
        z ^= z >> 27; z *= 0x94d049bb133111ebULL;
        return static_cast<size_t>(z ^ (z >> 31));
    }
};

struct State {
    Point point;
    uint8_t edge = 0;
    uint8_t col0 = 0, col1 = 0;
};

bool add_columns(U128& used, const State& state) {
    const U128 bits = (U128(1) << state.col0) | (U128(1) << state.col1);
    if (state.col0 == state.col1 || (used & bits)) return false;
    used |= bits;
    return true;
}

uint32_t pack(unsigned a, unsigned b, unsigned c) {
    return a | (b << 8) | (c << 16);
}

std::array<unsigned, 3> unpack(uint32_t code) {
    return {code & 255, (code >> 8) & 255, (code >> 16) & 255};
}

double elapsed(std::chrono::steady_clock::time_point start) {
    return std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
}

int main(int argc, char** argv) {
    try {
        if (argc != 2) throw std::runtime_error("usage: join7 input.tsv");
        auto start = std::chrono::steady_clock::now();
        std::ifstream input(argv[1]);
        if (!input) throw std::runtime_error("cannot open input");
        std::string tag;
        int slots, states, targets;
        input >> tag >> slots >> states >> targets;
        if (tag != "ECC2K41" || slots != 7 || states != 160 || targets != 1)
            throw std::runtime_error("input header mismatch");
        std::array<std::array<State, 160>, 7> lists{};
        std::array<Point, 1> raw_targets{};
        std::array<std::array<bool, 160>, 7> seen{};
        int state_rows = 0, check_rows = 0;
        while (input >> tag) {
            if (tag == "T") {
                int i; uint64_t x, y;
                input >> i >> x >> y;
                if (i != 0) throw std::runtime_error("target index");
                raw_targets[i] = {x, y, false};
            } else if (tag == "S") {
                int slot, sid, edge, col0, col1;
                uint64_t x, y;
                input >> slot >> sid >> edge >> col0 >> col1 >> x >> y;
                if (slot < 0 || slot >= 7 || sid < 0 || sid >= 160 ||
                    edge < 0 || edge >= 40 || sid / 4 != edge ||
                    col0 < 0 || col0 >= 128 || col1 < 0 || col1 >= 128 ||
                    seen[slot][sid])
                    throw std::runtime_error("state row mismatch");
                lists[slot][sid] = {{x, y, false}, static_cast<uint8_t>(edge),
                                    static_cast<uint8_t>(col0), static_cast<uint8_t>(col1)};
                seen[slot][sid] = true;
                ++state_rows;
            } else if (tag == "C") {
                int64_t x1, y1, x2, y2, x3, y3;
                input >> x1 >> y1 >> x2 >> y2 >> x3 >> y3;
                Point computed = add({uint64_t(x1), uint64_t(y1), false},
                                     {uint64_t(x2), uint64_t(y2), false});
                if ((x3 < 0) != computed.infinity ||
                    (x3 >= 0 && (computed.x != uint64_t(x3) || computed.y != uint64_t(y3))))
                    throw std::runtime_error("Sage addition check failed");
                ++check_rows;
            } else {
                throw std::runtime_error("unknown input tag");
            }
        }
        if (state_rows != 1120 || check_rows != 128)
            throw std::runtime_error("incomplete states or checks");
        for (const auto& slot : seen)
            for (bool value : slot) if (!value) throw std::runtime_error("missing state");
        std::cout << "CHECK_PASS " << check_rows << " " << elapsed(start) << "\n" << std::flush;

        std::unordered_multimap<Point, uint32_t, Hash> left;
        left.max_load_factor(0.8f);
        left.reserve(4000000);
        for (unsigned a = 0; a < 160; ++a)
            for (unsigned b = 0; b < 160; ++b) {
                U128 used = 0;
                if (!add_columns(used, lists[0][a]) ||
                    !add_columns(used, lists[1][b])) continue;
                Point first = add(lists[0][a].point, lists[1][b].point);
                for (unsigned c = 0; c < 160; ++c) {
                    U128 used3 = used;
                    if (!add_columns(used3, lists[2][c])) continue;
                    left.emplace(add(first, lists[2][c].point), pack(a, b, c));
                }
            }
        std::cout << "LEFT_DONE " << left.size() << " " << elapsed(start) << "\n" << std::flush;

        constexpr unsigned TERMINAL_STATES = 160;
        constexpr unsigned TARGET_HITS = 1;
        size_t probes = 0, point_matches = 0, accepted = 0;
        const unsigned target = 0;
        for (unsigned a = 0; a < 160; ++a)
            for (unsigned b = 0; b < 160; ++b) {
                U128 used = 0;
                if (!add_columns(used, lists[3][a]) ||
                    !add_columns(used, lists[4][b])) continue;
                Point first = add(lists[3][a].point, lists[4][b].point);
                for (unsigned c = 0; c < 160; ++c) {
                    U128 used3 = used;
                    if (!add_columns(used3, lists[5][c])) continue;
                    Point triple = add(first, lists[5][c].point);
                    for (unsigned d = 0; d < TERMINAL_STATES; ++d) {
                        U128 used4 = used3;
                        if (!add_columns(used4, lists[6][d])) continue;
                        Point right = add(triple, lists[6][d].point);
                        Point need = add(raw_targets[target], negate(right));
                        auto range = left.equal_range(need);
                        for (auto it = range.first; it != range.second; ++it) {
                            ++point_matches;
                            auto l = unpack(it->second);
                            std::array<unsigned, 7> ids{l[0], l[1], l[2], a, b, c, d};
                            U128 all_used = 0;
                            bool distinct = true;
                            for (int slot = 0; slot < 7; ++slot) {
                                if (!add_columns(all_used, lists[slot][ids[slot]]))
                                    distinct = false;
                            }
                            if (!distinct) continue;
                            if (!(add(it->first, right) == raw_targets[target]))
                                throw std::runtime_error("hash hit failed group replay");
                            std::cout << "HIT " << target;
                            for (unsigned id : ids) std::cout << " " << id;
                            std::cout << " " << probes << " " << point_matches
                                      << " " << elapsed(start) << "\n" << std::flush;
                            if (++accepted == TARGET_HITS) {
                                std::cout << "COMPLETE_HITS " << accepted << " " << probes
                                          << " " << elapsed(start) << "\n" << std::flush;
                                return 0;
                            }
                        }
                        ++probes;
                    }
                }
            }
        std::cout << "MISS_COMPLETE " << probes << " " << accepted << " "
                  << elapsed(start) << "\n" << std::flush;
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "ERROR " << error.what() << "\n";
        return 2;
    }
}
