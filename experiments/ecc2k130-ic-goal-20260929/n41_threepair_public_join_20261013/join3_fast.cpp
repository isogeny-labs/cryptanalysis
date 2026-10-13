#include <arm_neon.h>
// Exact N41 nine-pair join: two frozen prefix pairs plus seven free pairs.
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

uint64_t slow_mul(uint64_t a, uint64_t b) {
    uint64_t result = 0;
    while (b) {
        if (b & 1) result ^= a;
        b >>= 1;
        a <<= 1;
        if (a & (1ULL << 41)) a ^= MOD;
    }
    return result;
}


// Carryless 41-by-41 product, reduced by x^41 + x^3 + 1 in two folds.
uint64_t mul(uint64_t a, uint64_t b) {
#if defined(__ARM_FEATURE_CRYPTO)
    poly128_t product = vmull_p64((poly64_t)a, (poly64_t)b);
    uint64x2_t lanes = vreinterpretq_u64_p128(product);
    uint64_t lo = vgetq_lane_u64(lanes, 0);
    uint64_t hi = vgetq_lane_u64(lanes, 1);
    constexpr uint64_t mask = (1ULL << 41) - 1;
    uint64_t high = (lo >> 41) ^ (hi << 23);
    uint64_t folded = (lo & mask) ^ high ^ (high << 3);
    uint64_t high2 = folded >> 41;
    return (folded & mask) ^ high2 ^ (high2 << 3);
#else
    return slow_mul(a, b);
#endif
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
};

uint32_t pack(unsigned a, unsigned b, unsigned c) {
    return a | (b << 8) | (c << 16);
}

std::array<unsigned, 3> unpack(uint32_t code) {
    return {code & 255, (code >> 8) & 255, (code >> 16) & 255};
}

double elapsed(std::chrono::steady_clock::time_point start) {
    return std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
}


#include <bitset>
#include <sstream>
#include <unordered_map>

struct TripleState {
    Point point;
    uint16_t mask_a, mask_b;
    uint8_t col_a, col_b;
};

static bool on_curve3(Point p) {
    return p.infinity ||
           (sqr(p.y) ^ mul(p.x, p.y)) == (mul(sqr(p.x), p.x) ^ 1);
}

static bool add_columns3(std::bitset<128>& used, const TripleState& s) {
    if (s.col_a == s.col_b || used.test(s.col_a) || used.test(s.col_b)) return false;
    used.set(s.col_a); used.set(s.col_b);
    return true;
}

static std::vector<unsigned> parse_buckets(const std::string& order) {
    std::vector<unsigned> out;
    std::array<bool, 64> seen{};
    std::istringstream stream(order);
    std::string token;
    while (std::getline(stream, token, ',')) {
        unsigned bucket = std::stoul(token);
        if (bucket >= 64 || seen[bucket]) throw std::runtime_error("bad bucket order");
        seen[bucket] = true;
        out.push_back(bucket);
    }
    if (out.empty()) throw std::runtime_error("empty bucket order");
    return out;
}

int main(int argc, char** argv) {
    try {

        uint64_t test_state = 0x175ba1fa9dULL;
        for (unsigned trial = 0; trial < 100000; ++trial) {
            test_state ^= test_state << 7;
            test_state ^= test_state >> 9;
            uint64_t a = test_state & ((1ULL << 41) - 1);
            test_state ^= test_state << 7;
            test_state ^= test_state >> 9;
            uint64_t b = test_state & ((1ULL << 41) - 1);
            if (mul(a, b) != slow_mul(a, b))
                throw std::runtime_error("PMULL differential mismatch");
        }
        std::cout << "FIELD_SELFTEST_PASS 100000\n" << std::flush;
        if (argc != 6) throw std::runtime_error(
            "usage: join3 pairs.tsv public target_x target_y bucket_csv OR pairs.tsv control id0 id1 id2");
        const auto started = std::chrono::steady_clock::now();
        std::ifstream input(argv[1]);
        if (!input) throw std::runtime_error("cannot open source table");
        std::string line;
        if (!std::getline(input, line) || line != "ECC2K41_ALLSEED4 4 4")
            throw std::runtime_error("source header mismatch");
        std::vector<TripleState> source;
        source.reserve(30952);
        unsigned target_rows = 0;
        while (std::getline(input, line)) {
            std::istringstream row(line);
            std::string tag;
            row >> tag;
            if (tag == "T") { ++target_rows; continue; }
            if (tag != "S") throw std::runtime_error("source tag mismatch");
            unsigned slot, sid, mask_a, mask_b, col_a, col_b, sign_a, sign_b;
            uint64_t x, y;
            row >> slot >> sid >> mask_a >> mask_b >> col_a >> col_b
                >> sign_a >> sign_b >> x >> y;
            if (slot != 0) continue;
            if (sid != source.size() || mask_a >= mask_b ||
                mask_a > 255 || mask_b > 255 || col_a >= 128 || col_b >= 128 ||
                col_a == col_b || sign_a != ((sid >> 1) & 1) ||
                sign_b != (sid & 1))
                throw std::runtime_error("source row mismatch");
            Point point{x, y, false};
            if (!on_curve3(point)) throw std::runtime_error("source point off curve");
            source.push_back({point, uint16_t(mask_a), uint16_t(mask_b),
                              uint8_t(col_a), uint8_t(col_b)});
        }
        if (source.size() != 30952 || target_rows != 4)
            throw std::runtime_error("incomplete source table");
        for (unsigned i = 0; i < source.size(); ++i) {
            const auto& a = source[i], &b = source[i ^ 3];
            if (!(negate(a.point) == b.point) || a.mask_a != b.mask_a ||
                a.mask_b != b.mask_b || a.col_a != b.col_a || a.col_b != b.col_b)
                throw std::runtime_error("sign partner mismatch");
        }
        Point target;
        std::vector<unsigned> buckets;
        const std::string mode(argv[2]);
        if (mode == "public") {
            target = {std::stoull(argv[3]), std::stoull(argv[4]), false};
            buckets = parse_buckets(argv[5]);
        } else if (mode == "control") {
            unsigned ids[3] = {unsigned(std::stoul(argv[3])),
                               unsigned(std::stoul(argv[4])),
                               unsigned(std::stoul(argv[5]))};
            for (unsigned id : ids)
                if (id >= source.size()) throw std::runtime_error("control id out of range");
            target = add(add(source[ids[0]].point, source[ids[1]].point),
                         source[ids[2]].point);
            buckets = {ids[0] % 64};
            std::cout << "CONTROL_TARGET " << target.x << " " << target.y
                      << " " << ids[0] << " " << ids[1] << " " << ids[2] << "\n";
        } else {
            throw std::runtime_error("bad mode");
        }
        if (target.infinity || !on_curve3(target))
            throw std::runtime_error("target off curve or identity");
        std::unordered_multimap<uint64_t, uint16_t> index;
        index.max_load_factor(0.8f);
        index.reserve(source.size());
        for (unsigned k = 0; k < source.size(); ++k)
            index.emplace(source[k].point.x, uint16_t(k));
        std::cout << "SOURCE_PASS " << source.size() << " " << target_rows
                  << " " << elapsed(started) << "\n" << std::flush;
        std::vector<uint64_t> prefix(source.size()+1), denom(source.size()), invdenom(source.size());
        uint64_t probes = 0, x_matches = 0, exact_matches = 0;
        for (unsigned bucket : buckets) {
            unsigned first_states = 0;
            for (unsigned i = bucket; i < source.size(); i += 64) {
                ++first_states;
                Point base = add(target, negate(source[i].point));
                if (base.infinity) {
                    for (unsigned j = 0; j < source.size(); ++j) {
                        std::bitset<128> used;
                        if (!add_columns3(used, source[i]) ||
                            !add_columns3(used, source[j])) continue;
                        ++probes;
                        Point need = negate(source[j].point);
                        auto range = index.equal_range(need.x);
                        for (auto it = range.first; it != range.second; ++it) {
                            ++x_matches;
                            unsigned k = it->second;
                            if (!(source[k].point == need)) continue;
                            ++exact_matches;
                            auto all = used;
                            if (!add_columns3(all, source[k])) continue;
                            if (!(add(add(source[i].point, source[j].point), source[k].point) == target))
                                throw std::runtime_error("hit replay mismatch");
                            std::cout << "HIT " << i << " " << j << " " << k << " "
                                      << bucket << " " << probes << " " << x_matches << " "
                                      << exact_matches << " " << elapsed(started) << "\n" << std::flush;
                            return 0;
                        }
                    }
                    continue;
                }
                prefix[0] = 1;
                for (unsigned j = 0; j < source.size(); ++j) {
                    denom[j] = base.x ^ source[j].point.x;
                    prefix[j+1] = denom[j] ? mul(prefix[j], denom[j]) : prefix[j];
                }
                uint64_t inverse_product = inv(prefix[source.size()]);
                for (unsigned j = source.size(); j-- > 0;) {
                    if (!denom[j]) continue;
                    invdenom[j] = mul(inverse_product, prefix[j]);
                    inverse_product = mul(inverse_product, denom[j]);
                }
                if (inverse_product != 1)
                    throw std::runtime_error("batch inverse closure mismatch");
                for (unsigned j = 0; j < source.size(); ++j) {
                    std::bitset<128> used;
                    if (!add_columns3(used, source[i]) ||
                        !add_columns3(used, source[j])) continue;
                    ++probes;
                    Point need;
                    Point right = negate(source[j].point);
                    if (!denom[j]) {
                        need = add(base, right);
                    } else {
                        uint64_t slope = mul(base.y ^ right.y, invdenom[j]);
                        uint64_t x3 = sqr(slope) ^ slope ^ base.x ^ right.x;
                        uint64_t y3 = mul(slope, base.x ^ x3) ^ x3 ^ base.y;
                        need = {x3, y3, false};
                    }
                    if ((j & 4095) == 0 && !(need == add(base, right)))
                        throw std::runtime_error("batch addition differential mismatch");
                    if (need.infinity) continue;
                    auto range = index.equal_range(need.x);
                    for (auto it = range.first; it != range.second; ++it) {
                        ++x_matches;
                        unsigned k = it->second;
                        if (!(source[k].point == need)) continue;
                        ++exact_matches;
                        auto all = used;
                        if (!add_columns3(all, source[k])) continue;
                        if (!(add(add(source[i].point, source[j].point), source[k].point) == target))
                            throw std::runtime_error("hit replay mismatch");
                        std::cout << "HIT " << i << " " << j << " " << k << " "
                                  << bucket << " " << probes << " " << x_matches << " "
                                  << exact_matches << " " << elapsed(started) << "\n" << std::flush;
                        return 0;
                    }
                }
            }
            std::cout << "BUCKET_DONE " << bucket << " " << first_states << " "
                      << probes << " " << x_matches << " " << exact_matches
                      << " " << elapsed(started) << "\n" << std::flush;
        }
        std::cout << "EXHAUSTED " << probes << " " << x_matches << " "
                  << exact_matches << " " << elapsed(started) << "\n" << std::flush;
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "ERROR " << error.what() << "\n";
        return 2;
    }
}
