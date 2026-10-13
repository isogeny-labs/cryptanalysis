// One linked Frobenius pair and eight free pairs on the frozen N41 public point.
#define main archived_ninepair_main
#include "../n41_w8_ninepair_join_control_20261012/join9.cpp"
#undef main

static uint64_t rng_state = 0x4d595df4d0f33173ULL;
static uint64_t random_word() {
    rng_state ^= rng_state >> 12;
    rng_state ^= rng_state << 25;
    rng_state ^= rng_state >> 27;
    return rng_state * 2685821657736338717ULL;
}

static constexpr std::array<unsigned, 5> LEFT_SLOTS{{0, 1, 2, 3, 4}};
static constexpr std::array<unsigned, 5> RIGHT_SLOTS{{5, 0, 1, 2, 3}};
static constexpr uint64_t LEFT_KEEP = 5000000;
static constexpr uint64_t RIGHT_KEEP = 5000000;
static constexpr uint64_t INFINITY_KEY = UINT64_MAX;

struct CanonicalLeft {
    uint64_t code;
    uint64_t y;
};

static uint64_t x_key(Point point) {
    return point.infinity ? INFINITY_KEY : point.x;
}

static uint64_t pack5(const std::array<uint8_t, 5>& ids) {
    uint64_t result = 0;
    for (unsigned i = 0; i < 5; ++i) result |= uint64_t(ids[i]) << (8 * i);
    return result;
}

static std::array<uint8_t, 5> unpack5(uint64_t code) {
    std::array<uint8_t, 5> ids{};
    for (unsigned i = 0; i < 5; ++i) ids[i] = (code >> (8 * i)) & 255;
    return ids;
}

static bool sample_half(const std::array<std::array<State, 140>, 6>& lists,
                        const std::array<unsigned, 5>& slots,
                        std::array<uint8_t, 5>& ids, Point& sum,
                        uint64_t& edges, bool linked) {
    edges = 0;
    sum = {};
    for (unsigned i = 0; i < 5; ++i) {
        ids[i] = linked && i == 1 ? ids[0] : random_word() % 140;
        const State& state = lists[slots[i]][ids[i]];
        uint64_t bit = 1ULL << state.edge;
        if ((edges & bit) && !(linked && i == 1)) return false;
        edges |= bit;
        sum = add(sum, state.point);
    }
    return true;
}

int main(int argc, char** argv) {
    try {
        if (argc != 2) throw std::runtime_error("usage: join10 input.tsv");
        auto start = std::chrono::steady_clock::now();
        std::ifstream input(argv[1]);
        if (!input) throw std::runtime_error("cannot open input");
        std::string tag;
        int slots, states, targets;
        input >> tag >> slots >> states >> targets;
        if (tag != "ECC2K41" || slots != 6 || states != 140 || targets != 4)
            throw std::runtime_error("input header mismatch");
        std::array<std::array<State, 140>, 6> lists{};
        std::array<Point, 4> raw_targets{};
        std::array<std::array<bool, 140>, 6> seen{};
        int rows = 0, checks = 0;
        while (input >> tag) {
            if (tag == "T") {
                int i; uint64_t x, y;
                input >> i >> x >> y;
                if (i < 0 || i >= 4) throw std::runtime_error("target index");
                raw_targets[i] = {x, y, false};
            } else if (tag == "S") {
                int slot, sid, edge, a, b, sa, sb;
                uint64_t x, y;
                input >> slot >> sid >> edge >> a >> b >> sa >> sb >> x >> y;
                if (slot < 0 || slot >= 6 || sid < 0 || sid >= 140 ||
                    edge < 0 || edge >= 35 || sid / 4 != edge ||
                    seen[slot][sid] || a >= b || (a ^ b) != 184 ||
                    sa < 0 || sa > 1 || sb < 0 || sb > 1)
                    throw std::runtime_error("source row mismatch");
                lists[slot][sid] = {{x, y, false}, static_cast<uint8_t>(edge)};
                seen[slot][sid] = true;
                ++rows;
            } else if (tag == "C") {
                int64_t x1, y1, x2, y2, x3, y3;
                input >> x1 >> y1 >> x2 >> y2 >> x3 >> y3;
                Point got = add({uint64_t(x1), uint64_t(y1), false},
                                {uint64_t(x2), uint64_t(y2), false});
                if ((x3 < 0) != got.infinity ||
                    (x3 >= 0 && (got.x != uint64_t(x3) || got.y != uint64_t(y3))))
                    throw std::runtime_error("reference addition mismatch");
                ++checks;
            } else throw std::runtime_error("unknown input tag");
        }
        if (rows != 840 || checks != 128)
            throw std::runtime_error("incomplete source or reference checks");
        for (const auto& slot : seen)
            for (bool value : slot) if (!value) throw std::runtime_error("missing source state");
        for (const auto& slot : lists)
            for (unsigned i = 0; i < 140; ++i)
                if (!(negate(slot[i].point) == slot[i ^ 3].point) ||
                    slot[i].edge != slot[i ^ 3].edge)
                    throw std::runtime_error("global sign pairing mismatch");
        for (unsigned sid = 0; sid < 140; ++sid) {
            Point transported = lists[0][sid].point;
            for (unsigned step = 0; step < 7; ++step) {
                transported.x = sqr(transported.x);
                transported.y = sqr(transported.y);
            }
            if (!(transported == lists[1][sid].point) ||
                lists[0][sid].edge != lists[1][sid].edge)
                throw std::runtime_error("linked Frobenius state mismatch");
        }
        std::cout << "SOURCE_PASS " << rows << " " << checks << "\n" << std::flush;

        std::unordered_multimap<uint64_t, CanonicalLeft> left;
        left.max_load_factor(0.8f);
        left.reserve(LEFT_KEEP);
        uint64_t left_attempts = 0;
        while (left.size() < LEFT_KEEP) {
            ++left_attempts;
            std::array<uint8_t, 5> ids{};
            Point sum;
            uint64_t edges;
            if (!sample_half(lists, LEFT_SLOTS, ids, sum, edges, true)) continue;
            if (!sum.infinity && sum.y > (sum.y ^ sum.x)) {
                sum = negate(sum);
                for (auto& id : ids) id ^= 3;
            }
            left.emplace(x_key(sum), CanonicalLeft{pack5(ids), sum.y});
        }
        const double setup_seconds = elapsed(start);
        std::cout << "LEFT_DONE " << left.size() << " " << left_attempts << " "
                  << setup_seconds << "\n" << std::flush;

        uint64_t right_attempts = 0, right_kept = 0, point_matches = 0;
        uint64_t positive_hits = 0, negative_hits = 0;
        while (right_kept < RIGHT_KEEP) {
            ++right_attempts;
            std::array<uint8_t, 5> right_ids{};
            Point right_sum;
            uint64_t right_edges;
            if (!sample_half(lists, RIGHT_SLOTS, right_ids, right_sum, right_edges, false)) continue;
            ++right_kept;
            for (unsigned target_index = 0; target_index < 4; ++target_index) {
                Point need = add(raw_targets[target_index], negate(right_sum));
                auto range = left.equal_range(x_key(need));
                for (auto it = range.first; it != range.second; ++it) {
                    ++point_matches;
                    bool flip = false;
                    if (need.infinity) {
                        if (it->second.y != 0) throw std::runtime_error("identity row mismatch");
                    } else if (it->second.y != need.y) {
                        if ((it->second.y ^ need.x) != need.y)
                            throw std::runtime_error("x bucket contained non-negation point");
                        flip = true;
                    }
                    if (flip) ++negative_hits; else ++positive_hits;
                    auto left_ids = unpack5(it->second.code);
                    if (flip) for (auto& id : left_ids) id ^= 3;
                    uint64_t left_edges = 0;
                    Point left_sum;
                    for (unsigned i = 0; i < 5; ++i)
                    {
                        left_edges |= 1ULL << lists[LEFT_SLOTS[i]][left_ids[i]].edge;
                        left_sum = add(left_sum, lists[LEFT_SLOTS[i]][left_ids[i]].point);
                    }
                    if (left_ids[0] != left_ids[1] || __builtin_popcountll(left_edges) != 4 ||
                        __builtin_popcountll(right_edges) != 5)
                        throw std::runtime_error("linked source replay failed");
                    if (!(left_sum == need)) throw std::runtime_error("canonical row replay failed");
                    if (left_edges & right_edges) continue;
                    if (!(add(left_sum, right_sum) == raw_targets[target_index]))
                        throw std::runtime_error("point-match replay failed");
                    std::cout << "HIT " << target_index;
                    for (auto id : left_ids) std::cout << " " << unsigned(id);
                    for (auto id : right_ids) std::cout << " " << unsigned(id);
                    std::cout << " " << left.size() << " " << left_attempts
                              << " " << right_kept << " " << right_attempts
                              << " " << point_matches << " " << setup_seconds
                              << " " << elapsed(start) << " " << unsigned(flip)
                              << " " << positive_hits << " " << negative_hits
                              << "\n" << std::flush;
                    return 0;
                }
            }
        }
        std::cout << "EXHAUSTED " << left.size() << " " << left_attempts
                  << " " << right_kept << " " << right_attempts << " "
                  << point_matches << " " << setup_seconds << " "
                  << elapsed(start) << "\n" << std::flush;
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "ERROR " << error.what() << "\n";
        return 2;
    }
}
