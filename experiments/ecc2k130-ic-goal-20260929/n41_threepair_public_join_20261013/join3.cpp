// Target-first exact three-pair join on the frozen N41 W8 raw source.
#define main archived_ninepair_main
#include "../n41_w8_ninepair_join_control_20261012/join9.cpp"
#undef main

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
