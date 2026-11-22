// Exact N41 W9 public-target five-pair join. All leaves are unpinned.
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using U128 = unsigned __int128;
using Clock = std::chrono::steady_clock;
constexpr uint64_t MOD = (1ULL << 41) | (1ULL << 3) | 1;
constexpr int SLOTS = 5;
constexpr int STATES = 284;

uint64_t mul(uint64_t a, uint64_t b) {
    uint64_t r = 0;
    while (b) {
        if (b & 1) r ^= a;
        b >>= 1; a <<= 1;
        if (a & (1ULL << 41)) a ^= MOD;
    }
    return r;
}
uint64_t sqr(uint64_t a) { return mul(a, a); }
int degree(uint64_t x) {
    if (!x) throw std::runtime_error("zero inverse");
    return 63 - __builtin_clzll(x);
}
uint64_t inv(uint64_t a) {
    if (!a) throw std::runtime_error("zero inverse");
    uint64_t u = a, v = MOD; U128 x = 1, y = 0;
    while (u != 1) {
        int j = degree(u) - degree(v);
        if (j < 0) { std::swap(u, v); std::swap(x, y); j = -j; }
        u ^= v << j; x ^= y << j;
    }
    for (int bit = 127; bit >= 41; --bit)
        if ((x >> bit) & 1) x ^= U128(MOD) << (bit - 41);
    uint64_t r = static_cast<uint64_t>(x);
    if (mul(a, r) != 1) throw std::runtime_error("inverse check");
    return r;
}
struct Point {
    uint64_t x = 0, y = 0; bool inf = true;
    bool operator==(const Point &q) const {
        return inf == q.inf && (inf || (x == q.x && y == q.y));
    }
};
struct Hash {
    size_t operator()(const Point &p) const {
        if (p.inf) return 0x9e3779b97f4a7c15ULL;
        uint64_t z = p.x ^ (p.y << 17) ^ (p.y >> 24);
        z ^= z >> 30; z *= 0xbf58476d1ce4e5b9ULL;
        z ^= z >> 27; z *= 0x94d049bb133111ebULL;
        return static_cast<size_t>(z ^ (z >> 31));
    }
};
Point neg(Point p) { if (!p.inf) p.y ^= p.x; return p; }
Point add(Point p, Point q) {
    if (p.inf) return q;
    if (q.inf) return p;
    uint64_t s, x, y;
    if (p.x == q.x) {
        if (p.y != q.y || !p.x) return {};
        s = p.x ^ mul(p.y, inv(p.x));
        x = sqr(s) ^ s;
        y = sqr(p.x) ^ mul(s ^ 1, x);
    } else {
        s = mul(p.y ^ q.y, inv(p.x ^ q.x));
        x = sqr(s) ^ s ^ p.x ^ q.x;
        y = mul(s, p.x ^ x) ^ x ^ p.y;
    }
    return {x, y, false};
}
bool on_curve(Point p) {
    return p.inf || (sqr(p.y) ^ mul(p.x, p.y)) == (mul(sqr(p.x), p.x) ^ 1);
}
struct Columns {
    std::array<uint64_t, 4> bits{};
    void insert(int col) { bits[col / 64] |= uint64_t(1) << (col % 64); }
    bool disjoint(const Columns &other) const {
        for (int i = 0; i < 4; ++i) if (bits[i] & other.bits[i]) return false;
        return true;
    }
    void join(const Columns &other) {
        for (int i = 0; i < 4; ++i) bits[i] |= other.bits[i];
    }
};
struct State { Point p; Columns cols; int a = 0, b = 0, sa = 0, sb = 0; };
uint32_t pack(int a, int b, int c) { return a | (b << 9) | (c << 18); }
std::array<int, 3> unpack(uint32_t x) {
    return {int(x & 511), int((x >> 9) & 511), int((x >> 18) & 511)};
}
double elapsed(Clock::time_point start) {
    return std::chrono::duration<double>(Clock::now() - start).count();
}

int main(int argc, char **argv) {
    try {
        if (argc != 2) throw std::runtime_error("usage: join_five input.tsv");
        auto start = Clock::now();
        std::ifstream input(argv[1]);
        if (!input) throw std::runtime_error("input missing");
        std::string tag; int slots, states; uint64_t tx, ty;
        input >> tag >> slots >> states >> tx >> ty;
        if (tag != "ECC2K41" || slots != SLOTS || states != STATES)
            throw std::runtime_error("header");
        Point target{tx, ty, false};
        if (!on_curve(target)) throw std::runtime_error("target curve");
        std::array<std::array<State, STATES>, SLOTS> list{};
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
            list[slot][id] = {p, cols, a, b, sa, sb};
            seen[slot][id] = true; ++count;
        }
        if (count != SLOTS * STATES) throw std::runtime_error("row count");
        for (auto &slot : seen) for (bool value : slot)
            if (!value) throw std::runtime_error("missing row");
        std::cout << "CHECK_PASS " << count << " " << elapsed(start) << "\n" << std::flush;
        std::unordered_multimap<Point, uint32_t, Hash> left;
        left.max_load_factor(0.8f);
        left.reserve(23000000);
        for (int a = 0; a < STATES; ++a) for (int b = 0; b < STATES; ++b) {
            const State &A = list[0][a], &B = list[1][b];
            if (!A.cols.disjoint(B.cols)) continue;
            Point ab = add(A.p, B.p);
            Columns used = A.cols; used.join(B.cols);
            for (int c = 0; c < STATES; ++c) {
                const State &C = list[2][c];
                if (!used.disjoint(C.cols)) continue;
                left.emplace(add(ab, C.p), pack(a, b, c));
            }
        }
        std::cout << "LEFT_DONE " << left.size() << " " << elapsed(start)
                  << "\n" << std::flush;
        uint64_t probes = 0, matches = 0;
        for (int a = 0; a < STATES; ++a) for (int b = 0; b < STATES; ++b) {
            const State &A = list[3][a], &B = list[4][b];
            if (!A.cols.disjoint(B.cols)) continue;
            Point right = add(A.p, B.p);
            Columns used = A.cols; used.join(B.cols);
            Point need = add(target, neg(right));
            auto range = left.equal_range(need); ++probes;
            for (auto it = range.first; it != range.second; ++it) {
                ++matches;
                auto ids = unpack(it->second);
                if (ids[0] >= STATES || ids[1] >= STATES || ids[2] >= STATES)
                    throw std::runtime_error("packed id");
                Columns all = used;
                bool valid = true;
                for (int slot = 0; slot < 3; ++slot) {
                    const State &C = list[slot][ids[slot]];
                    if (!all.disjoint(C.cols)) { valid = false; break; }
                    all.join(C.cols);
                }
                if (!valid) continue;
                if (!(add(it->first, right) == target))
                    throw std::runtime_error("hit replay");
                std::cout << "HIT " << ids[0] << " " << ids[1] << " " << ids[2]
                          << " " << a << " " << b << " " << probes << " "
                          << matches << " " << elapsed(start) << "\n" << std::flush;
                return 0;
            }
        }
        std::cout << "MISS_COMPLETE " << probes << " " << matches << " "
                  << elapsed(start) << "\n" << std::flush;
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "ERROR " << error.what() << "\n";
        return 2;
    }
}
