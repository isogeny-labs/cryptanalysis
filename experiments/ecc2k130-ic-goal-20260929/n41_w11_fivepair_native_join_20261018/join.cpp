// Exact N41 five-pair group join with reusable two-pair tables.
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using U128 = unsigned __int128;
constexpr uint64_t MOD = (1ULL << 41) | (1ULL << 3) | 1;
constexpr int STATES = 1124;

uint64_t mul(uint64_t a, uint64_t b) {
    uint64_t result = 0;
    while (b) {
        if (b & 1) result ^= a;
        b >>= 1;
        a <<= 1;
        if (a >> 41) a ^= MOD;
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

bool on_curve(Point p) {
    if (p.infinity) return true;
    return (sqr(p.y) ^ mul(p.x, p.y)) == (mul(sqr(p.x), p.x) ^ 1);
}

Point negate(Point p) {
    if (!p.infinity) p.y ^= p.x;
    return p;
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
    size_t operator()(Point p) const {
        if (p.infinity) return 0x9e3779b97f4a7c15ULL;
        uint64_t z = p.x ^ (p.y << 17) ^ (p.y >> 24);
        z ^= z >> 30; z *= 0xbf58476d1ce4e5b9ULL;
        z ^= z >> 27; z *= 0x94d049bb133111ebULL;
        return static_cast<size_t>(z ^ (z >> 31));
    }
};

struct State {
    Point p;
    uint16_t code = 0;
    uint64_t col_a = 0, col_b = 0;
};

struct Pair {
    Point p;
    uint16_t a = 0, b = 0;
};

bool compatible(State a, State b) {
    if (a.code == b.code || a.col_a == a.col_b || b.col_a == b.col_b)
        return false;
    return a.col_a != b.col_a && a.col_a != b.col_b &&
           a.col_b != b.col_a && a.col_b != b.col_b;
}

bool five_distinct(const std::array<State, 5>& rows) {
    for (int i = 0; i < 5; ++i) {
        if (rows[i].col_a == rows[i].col_b) return false;
        for (int j = 0; j < i; ++j) {
            if (rows[i].code == rows[j].code) return false;
            for (uint64_t a : {rows[i].col_a, rows[i].col_b})
                for (uint64_t b : {rows[j].col_a, rows[j].col_b})
                    if (a == b) return false;
        }
    }
    return true;
}

double elapsed(std::chrono::steady_clock::time_point started) {
    return std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();
}

int main(int argc, char** argv) {
    try {
        if (argc != 4) throw std::runtime_error("usage: join input.tsv seed max_probes");
        auto start = std::chrono::steady_clock::now();
        std::ifstream input(argv[1]);
        if (!input) throw std::runtime_error("cannot open input");
        uint64_t seed = std::stoull(argv[2]);
        uint64_t max_probes = std::stoull(argv[3]);
        std::string tag;
        int slots, states, targets;
        input >> tag >> slots >> states >> targets;
        if (tag != "W11FIVE" || slots != 5 || states != STATES || targets != 1)
            throw std::runtime_error("input header mismatch");
        std::array<std::array<State, STATES>, 5> lists{};
        std::array<std::array<bool, STATES>, 5> seen{};
        Point Q;
        int state_rows = 0, check_rows = 0, target_rows = 0;
        while (input >> tag) {
            if (tag == "T") {
                int index; uint64_t x, y;
                input >> index >> x >> y;
                if (index != 0 || ++target_rows != 1) throw std::runtime_error("target row");
                Q = {x, y, false};
                if (!on_curve(Q)) throw std::runtime_error("target off curve");
            } else if (tag == "S") {
                int slot, sid, code, branch;
                uint64_t mask_a, mask_b, col_a, col_b, x, y;
                input >> slot >> sid >> code >> branch >> mask_a >> mask_b
                      >> col_a >> col_b >> x >> y;
                if (slot < 0 || slot >= 5 || sid < 0 || sid >= STATES ||
                    code < 0 || code >= 1024 || branch != sid % 4 ||
                    mask_b != (mask_a ^ 112) || seen[slot][sid] ||
                    x >= (1ULL << 41) || y >= (1ULL << 41))
                    throw std::runtime_error("bad state row");
                Point p{x, y, false};
                if (!on_curve(p)) throw std::runtime_error("state off curve");
                lists[slot][sid] = {p, static_cast<uint16_t>(code), col_a, col_b};
                seen[slot][sid] = true;
                ++state_rows;
            } else if (tag == "C") {
                int64_t x1,y1,x2,y2,x3,y3;
                input >> x1 >> y1 >> x2 >> y2 >> x3 >> y3;
                Point sum = add({uint64_t(x1),uint64_t(y1),false},
                                {uint64_t(x2),uint64_t(y2),false});
                if ((x3 < 0) != sum.infinity ||
                    (x3 >= 0 && (sum.x != uint64_t(x3) || sum.y != uint64_t(y3))))
                    throw std::runtime_error("Sage addition check failed");
                ++check_rows;
            } else {
                throw std::runtime_error("unknown input tag");
            }
        }
        if (target_rows != 1 || state_rows != 5*STATES || check_rows != 128)
            throw std::runtime_error("incomplete input");
        for (const auto& row : seen)
            for (bool value : row) if (!value) throw std::runtime_error("missing state");
        std::cout << "CHECK_PASS " << check_rows << " " << elapsed(start) << "\n" << std::flush;

        std::unordered_multimap<Point, uint32_t, Hash> right;
        right.max_load_factor(0.8f);
        right.reserve(1300000);
        uint64_t right_rejected = 0;
        for (int i = 0; i < STATES; ++i)
            for (int j = 0; j < STATES; ++j) {
                State a = lists[3][i], b = lists[4][j];
                if (!compatible(a,b)) { ++right_rejected; continue; }
                right.emplace(add(a.p,b.p), i*STATES+j);
            }
        std::cout << "RIGHT_TABLE " << right.size() << " " << right_rejected
                  << " " << elapsed(start) << "\n" << std::flush;
        std::vector<Pair> left;
        left.reserve(STATES*STATES);
        uint64_t left_rejected = 0;
        for (int i = 0; i < STATES; ++i)
            for (int j = 0; j < STATES; ++j) {
                State a = lists[0][i], b = lists[1][j];
                if (!compatible(a,b)) { ++left_rejected; continue; }
                left.push_back({add(a.p,b.p),static_cast<uint16_t>(i),
                                static_cast<uint16_t>(j)});
            }
        std::cout << "LEFT_TABLE " << left.size() << " " << left_rejected
                  << " " << elapsed(start) << "\n" << std::flush;

        auto online_start = std::chrono::steady_clock::now();
        std::mt19937_64 rng(seed);
        uint64_t hits = 0, rejected = 0;
        for (uint64_t probe = 1; probe <= max_probes; ++probe) {
            const Pair& L = left[rng() % left.size()];
            int k = rng() % STATES;
            State middle = lists[2][k];
            if (middle.code == lists[0][L.a].code ||
                middle.code == lists[1][L.b].code) { ++rejected; continue; }
            Point residual = add(add(Q, negate(L.p)), negate(middle.p));
            auto range = right.equal_range(residual);
            for (auto it = range.first; it != range.second; ++it) {
                ++hits;
                int i = it->second / STATES, j = it->second % STATES;
                std::array<State, 5> row = {
                    lists[0][L.a], lists[1][L.b], middle,
                    lists[3][i], lists[4][j]};
                if (!five_distinct(row)) { ++rejected; continue; }
                Point sum;
                for (State s : row) sum = add(sum,s.p);
                if (!(sum == Q)) throw std::runtime_error("hit sum mismatch");
                std::cout << "HIT " << L.a << " " << L.b << " " << k << " "
                          << i << " " << j << " " << probe << " " << hits
                          << " " << rejected << " " << elapsed(online_start)
                          << " " << elapsed(start) << "\n" << std::flush;
                return 0;
            }
        }
        std::cout << "NO_HIT " << max_probes << " " << hits << " " << rejected
                  << " " << elapsed(online_start) << " " << elapsed(start)
                  << "\n" << std::flush;
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "PRODUCER_FAILURE " << e.what() << "\n";
        return 2;
    }
}
