// One-target N41 IC and rho using the same audited binary-curve group kernel.
#define main archived_single_main
#include "../n41_w8_sixpair_mitm_20261011/join.cpp"
#undef main

#include <limits>

constexpr uint64_t ORDER = 549756390943ULL;

uint64_t mod_add(uint64_t a, uint64_t b) { return (a + b) % ORDER; }
uint64_t mod_sub(uint64_t a, uint64_t b) { return (a + ORDER - b) % ORDER; }
uint64_t mod_mul(uint64_t a, uint64_t b) { return uint64_t(U128(a) * b % ORDER); }

uint64_t mod_pow(uint64_t a, uint64_t exponent) {
    uint64_t result = 1;
    while (exponent) {
        if (exponent & 1) result = mod_mul(result, a);
        a = mod_mul(a, a);
        exponent >>= 1;
    }
    return result;
}

Point scale(Point point, uint64_t scalar) {
    Point result{};
    while (scalar) {
        if (scalar & 1) result = add(result, point);
        point = add(point, point);
        scalar >>= 1;
    }
    return result;
}

Point read_target(const char* filename) {
    std::ifstream input(filename);
    std::string tag;
    uint64_t x, y;
    input >> tag >> x >> y;
    if (tag != "Q" || !input) throw std::runtime_error("public target input");
    return {x, y, false};
}

using Lists = std::array<std::array<State, 140>, 6>;

Lists read_states(const char* filename) {
    std::ifstream input(filename);
    std::string tag;
    int slots, states, targets;
    input >> tag >> slots >> states >> targets;
    if (tag != "ECC2K41" || slots != 6 || states != 140 || targets != 4)
        throw std::runtime_error("source table header");
    Lists lists{};
    std::array<std::array<bool, 140>, 6> seen{};
    int checks = 0;
    while (input >> tag) {
        if (tag == "T") {
            int index; uint64_t x, y;
            input >> index >> x >> y;
        } else if (tag == "S") {
            int slot, sid, edge, a, b, sa, sb; uint64_t x, y;
            input >> slot >> sid >> edge >> a >> b >> sa >> sb >> x >> y;
            if (slot < 0 || slot >= 6 || sid < 0 || sid >= 140 ||
                edge != sid / 4 || seen[slot][sid] || (a ^ b) != 184)
                throw std::runtime_error("source table row");
            lists[slot][sid] = {{x, y, false}, static_cast<uint8_t>(edge)};
            seen[slot][sid] = true;
        } else if (tag == "C") {
            int64_t x1, y1, x2, y2, x3, y3;
            input >> x1 >> y1 >> x2 >> y2 >> x3 >> y3;
            Point result = add({uint64_t(x1), uint64_t(y1), false},
                               {uint64_t(x2), uint64_t(y2), false});
            if ((x3 < 0) != result.infinity ||
                (x3 >= 0 && (result.x != uint64_t(x3) || result.y != uint64_t(y3))))
                throw std::runtime_error("source arithmetic check");
            ++checks;
        } else throw std::runtime_error("source table tag");
    }
    if (checks != 128) throw std::runtime_error("source check count");
    for (const auto& slot : seen)
        for (bool present : slot) if (!present) throw std::runtime_error("missing source state");
    return lists;
}

using StateLogs = std::array<std::array<uint64_t, 140>, 6>;

StateLogs read_logs(const char* filename) {
    std::ifstream input(filename);
    std::string tag;
    int slots, states;
    input >> tag >> slots >> states;
    if (tag != "STATE_LOGS" || slots != 6 || states != 140)
        throw std::runtime_error("state log header");
    StateLogs logs{};
    std::array<std::array<bool, 140>, 6> seen{};
    int count = 0;
    while (input >> tag) {
        int slot, sid; uint64_t value;
        input >> slot >> sid >> value;
        if (tag != "L" || slot < 0 || slot >= 6 || sid < 0 || sid >= 140 ||
            seen[slot][sid] || value >= ORDER)
            throw std::runtime_error("state log row");
        logs[slot][sid] = value;
        seen[slot][sid] = true;
        ++count;
    }
    if (count != 840) throw std::runtime_error("state log count");
    return logs;
}

std::array<Point, 4> read_torsion(const char* filename) {
    std::ifstream input(filename);
    std::string tag;
    int count;
    input >> tag >> count;
    if (tag != "TORSION" || count != 4) throw std::runtime_error("torsion header");
    std::array<Point, 4> points{};
    for (int index = 0; index < 4; ++index) {
        int row; int64_t x, y;
        input >> tag >> row >> x >> y;
        if (tag != "T" || row != index || !input)
            throw std::runtime_error("torsion row");
        points[index] = x < 0 ? Point{} : Point{uint64_t(x), uint64_t(y), false};
    }
    return points;
}

uint64_t ns(std::chrono::steady_clock::time_point a,
            std::chrono::steady_clock::time_point b) {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(b - a).count();
}

int run_ic(int argc, char** argv) {
    if (argc != 8) throw std::runtime_error(
        "usage: online ic states.tsv logs.tsv torsion.tsv public.tsv Gx Gy");
    Point generator{std::stoull(argv[6]), std::stoull(argv[7]), false};
    auto setup_start = std::chrono::steady_clock::now();
    Lists lists = read_states(argv[2]);
    StateLogs logs = read_logs(argv[3]);
    auto torsion = read_torsion(argv[4]);
    if (!(scale(generator, ORDER).infinity))
        throw std::runtime_error("generator order check");
    std::unordered_multimap<Point, uint32_t, Hash> left;
    left.max_load_factor(0.8f);
    left.reserve(2500000);
    for (unsigned a = 0; a < 140; ++a)
        for (unsigned b = 0; b < 140; ++b) {
            if (lists[0][a].edge == lists[1][b].edge) continue;
            Point first = add(lists[0][a].point, lists[1][b].point);
            for (unsigned c = 0; c < 140; ++c) {
                if (lists[2][c].edge == lists[0][a].edge ||
                    lists[2][c].edge == lists[1][b].edge) continue;
                left.emplace(add(first, lists[2][c].point), pack(a, b, c));
            }
        }
    std::vector<Triple> right;
    right.reserve(2500000);
    for (unsigned a = 0; a < 140; ++a)
        for (unsigned b = 0; b < 140; ++b) {
            if (lists[3][a].edge == lists[4][b].edge) continue;
            Point first = add(lists[3][a].point, lists[4][b].point);
            for (unsigned c = 0; c < 140; ++c) {
                if (lists[5][c].edge == lists[3][a].edge ||
                    lists[5][c].edge == lists[4][b].edge) continue;
                right.push_back({add(first, lists[5][c].point), pack(a, b, c)});
            }
        }
    auto setup_end = std::chrono::steady_clock::now();
    Point target = read_target(argv[5]);
    std::cout << "IC_READY " << left.size() << " " << right.size() << " "
              << ns(setup_start, setup_end) << "\n" << std::flush;
    auto online_start = std::chrono::steady_clock::now();
    Point raw0 = scale(target, mod_pow(4, ORDER - 2));
    std::array<Point, 4> preimages{};
    for (int index = 0; index < 4; ++index) {
        preimages[index] = add(raw0, torsion[index]);
        if (!(scale(preimages[index], 4) == target))
            throw std::runtime_error("raw preimage check");
    }
    auto query_end = std::chrono::steady_clock::now();
    uint64_t check_ns = 0, probes = 0;
    for (int raw = 0; raw < 4; ++raw) {
        for (const auto& item : right) {
            Point need = add(preimages[raw], negate(item.point));
            auto range = left.equal_range(need);
            if (range.first != range.second) {
                auto check_start = std::chrono::steady_clock::now();
                for (auto it = range.first; it != range.second; ++it) {
                    auto l = unpack(it->second), r = unpack(item.code);
                    std::array<unsigned, 6> ids{l[0], l[1], l[2], r[0], r[1], r[2]};
                    uint64_t occupied = 0;
                    bool distinct = true;
                    for (int slot = 0; slot < 6; ++slot) {
                        uint64_t bit = 1ULL << lists[slot][ids[slot]].edge;
                        if (occupied & bit) distinct = false;
                        occupied |= bit;
                    }
                    if (!distinct) continue;
                    if (!(add(it->first, item.point) == preimages[raw]))
                        throw std::runtime_error("IC raw group replay");
                    auto check_end = std::chrono::steady_clock::now();
                    check_ns += ns(check_start, check_end);
                    auto descent_start = check_end;
                    uint64_t answer = 0;
                    for (int slot = 0; slot < 6; ++slot)
                        answer = mod_add(answer, logs[slot][ids[slot]]);
                    auto descent_end = std::chrono::steady_clock::now();
                    if (!(scale(generator, answer) == target))
                        throw std::runtime_error("IC scalar replay");
                    auto replay_end = std::chrono::steady_clock::now();
                    uint64_t target_query = ns(online_start, query_end);
                    uint64_t search = ns(query_end, check_end) - check_ns;
                    uint64_t descent = ns(descent_start, descent_end);
                    uint64_t replay = ns(descent_end, replay_end);
                    uint64_t online = target_query + search + check_ns + descent + replay;
                    std::cout << "IC_RESULT " << answer << " " << raw;
                    for (unsigned id : ids) std::cout << " " << id;
                    std::cout << " " << probes << " " << target_query << " " << search
                              << " " << check_ns << " " << descent << " " << replay
                              << " " << online << " " << ns(online_start, replay_end)
                              << "\n" << std::flush;
                    return 0;
                }
                check_ns += ns(check_start, std::chrono::steady_clock::now());
            }
            ++probes;
        }
    }
    std::cout << "IC_MISS " << probes << " "
              << ns(online_start, std::chrono::steady_clock::now()) << "\n" << std::flush;
    return 1;
}

uint64_t splitmix(uint64_t& state) {
    uint64_t z = (state += 0x9e3779b97f4a7c15ULL);
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

int run_rho(int argc, char** argv) {
    if (argc != 5) throw std::runtime_error("usage: online rho public.tsv Gx Gy");
    Point generator{std::stoull(argv[3]), std::stoull(argv[4]), false};
    Point target = read_target(argv[2]);
    auto online_start = std::chrono::steady_clock::now();
    uint64_t random = 20261011;
    std::array<Point, 16> increments{};
    std::array<uint64_t, 16> alpha{}, beta{};
    for (int index = 0; index < 16; ++index) {
        alpha[index] = splitmix(random) % ORDER;
        beta[index] = splitmix(random) % ORDER;
        increments[index] = add(scale(generator, alpha[index]),
                                scale(target, beta[index]));
    }
    auto setup_end = std::chrono::steady_clock::now();
    std::unordered_map<Point, std::pair<uint64_t, uint64_t>, Hash> distinguished;
    Point walker = generator;
    uint64_t a = 1, b = 0, steps = 0, stored = 0, collisions = 0;
    for (; steps < 20000000; ++steps) {
        unsigned partition = Hash{}(walker) & 15;
        walker = add(walker, increments[partition]);
        a = mod_add(a, alpha[partition]);
        b = mod_add(b, beta[partition]);
        if (walker.infinity || (walker.x & 255)) continue;
        auto [it, fresh] = distinguished.emplace(walker, std::make_pair(a, b));
        if (fresh) {
            ++stored;
            continue;
        }
        ++collisions;
        uint64_t denominator = mod_sub(b, it->second.second);
        if (!denominator) continue;
        uint64_t numerator = mod_sub(it->second.first, a);
        uint64_t answer = mod_mul(numerator, mod_pow(denominator, ORDER - 2));
        auto check_start = std::chrono::steady_clock::now();
        if (scale(generator, answer) == target) {
            auto end = std::chrono::steady_clock::now();
            uint64_t setup = ns(online_start, setup_end);
            uint64_t check = ns(check_start, end);
            uint64_t walk = ns(setup_end, check_start);
            std::cout << "RHO_RESULT " << answer << " " << (steps + 1) << " "
                      << stored << " " << collisions << " " << setup << " "
                      << walk << " " << check << " " << setup + walk + check << " "
                      << ns(online_start, end) << "\n" << std::flush;
            return 0;
        }
    }
    std::cout << "RHO_BOUNDED " << steps << " " << stored << " "
              << ns(online_start, std::chrono::steady_clock::now()) << "\n" << std::flush;
    return 1;
}

int main(int argc, char** argv) {
    try {
        if (argc < 3) throw std::runtime_error("mode required");
        std::string mode(argv[1]);
        if (mode == "ic") return run_ic(argc, argv);
        if (mode == "rho") return run_rho(argc, argv);
        throw std::runtime_error("unknown mode");
    } catch (const std::exception& error) {
        std::cerr << "ERROR " << error.what() << "\n";
        return 2;
    }
}
