// Five free signed W8 pair states on the target transformed by 1+Frobenius^7.
#define main archived_ninepair_main
#include "../n41_w8_ninepair_join_control_20261012/join9.cpp"
#undef main

#include <bitset>
#include <sstream>

struct PairState {
    Point point;
    uint8_t col_a, col_b;
};

struct LeftEntry {
    uint32_t code;
    uint64_t y;
};

static uint64_t random_state = 0x6a09e667f3bcc909ULL;
static uint64_t random_word() {
    random_state ^= random_state >> 12;
    random_state ^= random_state << 25;
    random_state ^= random_state >> 27;
    return random_state * 2685821657736338717ULL;
}

static bool on_curve(Point p) {
    return p.infinity ||
           (sqr(p.y) ^ mul(p.x, p.y)) == (mul(sqr(p.x), p.x) ^ 1);
}

static bool add_columns(std::bitset<128>& used, const PairState& s) {
    if (s.col_a >= 128 || s.col_b >= 128 || s.col_a == s.col_b ||
        used.test(s.col_a) || used.test(s.col_b)) return false;
    used.set(s.col_a); used.set(s.col_b);
    return true;
}

static bool sample(const std::vector<PairState>& source, unsigned count,
                   std::array<uint16_t, 3>& ids, Point& sum,
                   std::bitset<128>& used) {
    sum = {};
    used.reset();
    for (unsigned i = 0; i < count; ++i) {
        ids[i] = uint16_t(random_word() % source.size());
        const PairState& state = source[ids[i]];
        if (!add_columns(used, state)) return false;
        sum = add(sum, state.point);
    }
    return true;
}

static uint64_t key(Point p) { return p.infinity ? UINT64_MAX : p.x; }
static uint32_t pack2(const std::array<uint16_t, 3>& ids) {
    return uint32_t(ids[0]) | (uint32_t(ids[1]) << 15);
}
static std::array<uint16_t, 3> unpack2(uint32_t x) {
    return {uint16_t(x & 32767), uint16_t((x >> 15) & 32767), 0};
}

int main(int argc, char** argv) {
    try {
        if (argc != 4) throw std::runtime_error("usage: join5 pairs.tsv target_x target_y");
        auto start = std::chrono::steady_clock::now();
        const Point target{std::stoull(argv[2]), std::stoull(argv[3]), false};
        if (!on_curve(target)) throw std::runtime_error("transformed target off curve");
        std::ifstream in(argv[1]);
        if (!in) throw std::runtime_error("cannot open source table");
        std::string line;
        if (!std::getline(in, line) || line != "ECC2K41_ALLSEED4 4 4")
            throw std::runtime_error("source header mismatch");
        std::vector<PairState> source;
        std::array<bool, 30952> seen{};
        unsigned raw_targets = 0;
        while (std::getline(in, line)) {
            std::istringstream row(line);
            std::string tag;
            row >> tag;
            if (tag == "T") {
                ++raw_targets;
                continue;
            }
            if (tag != "S") throw std::runtime_error("source tag mismatch");
            unsigned slot, sid, mask_a, mask_b, col_a, col_b, sign_a, sign_b;
            uint64_t x, y;
            row >> slot >> sid >> mask_a >> mask_b >> col_a >> col_b
                >> sign_a >> sign_b >> x >> y;
            if (slot != 0) continue;
            if (sid >= 30952 || sid != source.size() || seen[sid] ||
                mask_a >= mask_b || col_a >= 128 || col_b >= 128 ||
                col_a == col_b || sign_a > 1 || sign_b > 1 ||
                sign_a != ((sid >> 1) & 1) || sign_b != (sid & 1))
                throw std::runtime_error("slot-zero row mismatch");
            Point raw{x, y, false};
            if (!on_curve(raw)) throw std::runtime_error("source point off curve");
            Point twice = add(raw, raw);
            Point projected = add(twice, twice);
            if (projected.infinity || !on_curve(projected))
                throw std::runtime_error("zero or invalid projected state");
            source.push_back({projected, uint8_t(col_a), uint8_t(col_b)});
            seen[sid] = true;
        }
        if (source.size() != 30952 || raw_targets != 4)
            throw std::runtime_error("incomplete source table");
        for (unsigned i = 0; i < source.size(); ++i) {
            const auto& a = source[i], &b = source[i ^ 3];
            if (!(negate(a.point) == b.point) ||
                a.col_a != b.col_a || a.col_b != b.col_b)
                throw std::runtime_error("global-sign partner mismatch");
        }
        std::cout << "SOURCE_PASS " << source.size() << " " << raw_targets
                  << " " << elapsed(start) << "\n" << std::flush;
        constexpr uint64_t LEFT_KEEP = 2000000, RIGHT_KEEP = 5000000;
        std::unordered_multimap<uint64_t, LeftEntry> left;
        left.max_load_factor(0.8f);
        left.reserve(LEFT_KEEP);
        uint64_t left_attempts = 0;
        while (left.size() < LEFT_KEEP) {
            ++left_attempts;
            std::array<uint16_t, 3> ids{};
            Point sum;
            std::bitset<128> used;
            if (!sample(source, 2, ids, sum, used)) continue;
            if (!sum.infinity && sum.y > (sum.y ^ sum.x)) {
                sum = negate(sum);
                ids[0] ^= 3; ids[1] ^= 3;
            }
            left.emplace(key(sum), LeftEntry{pack2(ids), sum.y});
        }
        const double setup = elapsed(start);
        std::cout << "LEFT_DONE " << left.size() << " " << left_attempts
                  << " " << setup << "\n" << std::flush;
        uint64_t right_attempts = 0, right_kept = 0, x_matches = 0;
        while (right_kept < RIGHT_KEEP) {
            ++right_attempts;
            std::array<uint16_t, 3> right_ids{};
            Point right_sum;
            std::bitset<128> right_cols;
            if (!sample(source, 3, right_ids, right_sum, right_cols)) continue;
            ++right_kept;
            Point need = add(target, negate(right_sum));
            auto range = left.equal_range(key(need));
            for (auto it = range.first; it != range.second; ++it) {
                ++x_matches;
                bool flip = false;
                if (need.infinity) {
                    if (it->second.y != 0) throw std::runtime_error("identity key mismatch");
                } else if (it->second.y != need.y) {
                    if ((it->second.y ^ need.x) != need.y)
                        throw std::runtime_error("x bucket mismatch");
                    flip = true;
                }
                auto left_ids = unpack2(it->second.code);
                if (flip) { left_ids[0] ^= 3; left_ids[1] ^= 3; }
                std::bitset<128> all_cols = right_cols;
                if (!add_columns(all_cols, source[left_ids[0]]) ||
                    !add_columns(all_cols, source[left_ids[1]])) continue;
                Point left_sum = add(source[left_ids[0]].point, source[left_ids[1]].point);
                if (!(left_sum == need) || !(add(left_sum, right_sum) == target))
                    throw std::runtime_error("group hit replay mismatch");
                std::cout << "HIT " << unsigned(left_ids[0]) << " "
                          << unsigned(left_ids[1]);
                for (auto sid : right_ids) std::cout << " " << unsigned(sid);
                std::cout << " " << left.size() << " " << left_attempts
                          << " " << right_kept << " " << right_attempts
                          << " " << x_matches << " " << setup << " "
                          << elapsed(start) << " " << unsigned(flip)
                          << "\n" << std::flush;
                return 0;
            }
        }
        std::cout << "EXHAUSTED " << left.size() << " " << left_attempts
                  << " " << right_kept << " " << right_attempts << " "
                  << x_matches << " " << setup << " " << elapsed(start)
                  << "\n" << std::flush;
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "ERROR " << error.what() << "\n";
        return 2;
    }
}
