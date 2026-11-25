// Exact target-conditioned W9 left-pair oracle with one-slot source storage.
#define main reference_join_main
#include "../n41_target_conditioned_2p1_join_20261018/join_2p1.cpp"
#undef main

#include <algorithm>
#include <sstream>

using Lists = std::array<std::array<State, STATES>, SLOTS>;

Lists read_lists(const char *path, Point &target) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("input missing");
    std::string tag; int slots, states; uint64_t tx, ty;
    input >> tag >> slots >> states >> tx >> ty;
    if (tag != "ECC2K41" || slots != SLOTS || states != STATES)
        throw std::runtime_error("header");
    target = {tx, ty, false};
    if (!on_curve(target)) throw std::runtime_error("target curve");
    Lists lists{};
    std::array<std::array<bool, STATES>, SLOTS> seen{};
    int count = 0;
    while (input >> tag) {
        if (tag != "S") throw std::runtime_error("row tag");
        int slot, id, a, b, sa, sb, ca, cb; uint64_t x, y;
        input >> slot >> id >> a >> b >> sa >> sb >> ca >> cb >> x >> y;
        if (!input || slot < 0 || slot >= SLOTS || id < 0 || id >= STATES ||
            seen[slot][id] || a <= 0 || b <= 0 || a >= 512 || b >= 512 ||
            (a ^ b) != 56 || ca < 0 || cb < 0 || ca >= 256 || cb >= 256 ||
            ca == cb || sa < 0 || sa > 1 || sb < 0 || sb > 1)
            throw std::runtime_error("row field");
        Point p{x, y, false};
        if (!on_curve(p)) throw std::runtime_error("state curve");
        Columns cols; cols.insert(ca); cols.insert(cb);
        lists[slot][id] = {p, cols, a, b, sa, sb};
        seen[slot][id] = true; ++count;
    }
    if (count != SLOTS * STATES) throw std::runtime_error("row count");
    for (const auto &slot : seen) for (bool value : slot)
        if (!value) throw std::runtime_error("missing row");
    return lists;
}

Point oriented(Point p, int count) {
    for (int j = 0; j < count; ++j) { p.x = sqr(p.x); p.y = sqr(p.y); }
    return p;
}

uint64_t halftrace(uint64_t a) {
    uint64_t result = 0;
    for (int j = 0; j < 21; ++j) { result ^= a; a = sqr(sqr(a)); }
    return result;
}

void make_panel(const Lists &lists, Point target) {
    const Point positive = add(lists[0][0].p, lists[1][130].p);
    Point other = add(lists[2][233].p,
                      add(lists[3][283].p, lists[4][152].p));
    if (!(add(positive, other) == oriented(target, 3)))
        throw std::runtime_error("positive relation check");
    std::cout << "P 3 233 283 152 " << positive.x << " " << positive.y << "\n";
    for (int orientation = 0; orientation < 3; ++orientation) {
        Point rotated = oriented(target, orientation);
        for (int j = 0; j < 128; ++j) {
            int c = (37 * j + 11 * orientation) % STATES;
            int a = -1, b = -1;
            for (int delta = 0; delta < STATES; ++delta) {
                int trial_a = (17 * j + 5 * orientation + delta) % STATES;
                int trial_b = (73 * j + 7 * orientation + 2 * delta) % STATES;
                const Columns &C = lists[2][c].cols;
                const Columns &A = lists[3][trial_a].cols;
                const Columns &B = lists[4][trial_b].cols;
                if (C.disjoint(A) && C.disjoint(B) && A.disjoint(B)) {
                    a = trial_a; b = trial_b; break;
                }
            }
            if (a < 0) throw std::runtime_error("panel column filter");
            Point right = add(lists[3][a].p, lists[4][b].p);
            Point key = add(add(rotated, neg(lists[2][c].p)), neg(right));
            if (key.inf || !on_curve(key)) throw std::runtime_error("panel key");
            std::cout << "M " << orientation << " " << c << " " << a << " "
                      << b << " " << key.x << " " << key.y << "\n";
        }
    }
}

struct Case { char kind; int orientation, c, a, b; Point key; };
std::vector<Case> read_panel(const char *path) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("panel missing");
    std::vector<Case> rows;
    std::string line;
    while (std::getline(input, line)) {
        std::istringstream stream(line);
        Case row{}; uint64_t x, y;
        stream >> row.kind >> row.orientation >> row.c >> row.a >> row.b >> x >> y;
        if (!stream || (row.kind != 'P' && row.kind != 'M'))
            throw std::runtime_error("panel row");
        row.key = {x, y, false};
        if (!on_curve(row.key)) throw std::runtime_error("panel key curve");
        rows.push_back(row);
    }
    if (rows.size() != 385 || rows.front().kind != 'P')
        throw std::runtime_error("panel size");
    return rows;
}

void query(const Lists &lists, const std::vector<Case> &panel) {
    const uint64_t seed = 56ULL << 1;
    const uint64_t H = sqr(halftrace(seed));
    const uint64_t C = 1 ^ H;
    std::unordered_map<uint64_t, std::vector<int>> by_product;
    std::unordered_map<Point, std::vector<int>, Hash> by_point;
    for (int id = 0; id < STATES; ++id) {
        const State &state = lists[1][id];
        uint64_t first = uint64_t(state.a) << 1;
        uint64_t second = uint64_t(state.b) << 1;
        by_product[mul(first, second)].push_back(id);
        by_point[state.p].push_back(id);
    }
    if (by_product.size() != 71)
        throw std::runtime_error("product-code map size");
    uint64_t total_checks = 0, total_direct = 0, total_inverse = 0;
    for (size_t index = 0; index < panel.size(); ++index) {
        auto began = Clock::now();
        const Case &row = panel[index];
        uint64_t checks = 0, direct_hits = 0, inverse_hits = 0;
        int first_a = -1, first_b = -1;
        for (int a = 0; a < STATES; ++a) {
            Point need = add(row.key, neg(lists[0][a].p));
            ++checks;
            std::vector<int> direct, inverted;
            auto direct_it = by_point.find(need);
            if (direct_it != by_point.end()) direct = direct_it->second;
            if (!need.inf && need.x) {
                uint64_t raw_x = need.x;
                for (int j = 0; j < 41 - 6; ++j) raw_x = sqr(raw_x);
                uint64_t product = mul(C, inv(raw_x)) ^ mul(H, raw_x);
                auto product_it = by_product.find(product);
                if (product_it != by_product.end())
                    for (int b : product_it->second)
                        if (lists[1][b].p == need) inverted.push_back(b);
            }
            if (direct != inverted)
                throw std::runtime_error("inverse/direct membership disagreement");
            direct_hits += direct.size(); inverse_hits += inverted.size();
            for (int b : direct)
                if (lists[0][a].cols.disjoint(lists[1][b].cols) && first_a < 0) {
                    first_a = a; first_b = b;
                }
        }
        total_checks += checks; total_direct += direct_hits; total_inverse += inverse_hits;
        std::cout << "CASE " << index << " " << row.kind << " " << row.orientation
                  << " " << checks << " " << direct_hits << " " << inverse_hits
                  << " " << first_a << " " << first_b << " "
                  << elapsed(began) << "\n";
    }
    std::cout << "TOTAL " << panel.size() << " " << total_checks << " "
              << total_direct << " " << total_inverse << "\n";
}

int main(int argc, char **argv) {
    try {
        if (argc != 3 && argc != 4)
            throw std::runtime_error("usage: oracle panel input.tsv | oracle query input.tsv panel.tsv");
        Point target;
        Lists lists = read_lists(argv[2], target);
        if (std::string(argv[1]) == "panel" && argc == 3)
            make_panel(lists, target);
        else if (std::string(argv[1]) == "query" && argc == 4)
            query(lists, read_panel(argv[3]));
        else throw std::runtime_error("mode");
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "ERROR " << error.what() << "\n";
        return 2;
    }
}
