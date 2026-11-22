// Exact six-slot 3+3 group join for the frozen N41 adjacent-union source.
#define main unused_three_pair_s7_main
#include "../n41_w6_s8_distinct_window_geometry/native_join/frozen_source/three_pair_s7_native.cpp"
#undef main

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

struct Seed { Point point; uint16_t column, mask; uint8_t sign, image; };
struct Triple { Point sum; std::array<uint8_t, 3> ids; };

static uint64_t elapsed_ns(std::chrono::steady_clock::time_point start) {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::steady_clock::now() - start).count();
}
static uint64_t peak_rss_bytes() {
    rusage usage{};
    getrusage(RUSAGE_SELF, &usage);
#if defined(__APPLE__)
    return uint64_t(usage.ru_maxrss);
#else
    return uint64_t(usage.ru_maxrss) * 1024;
#endif
}
static bool less_point(Point a, Point b) {
    if (a.infinity != b.infinity) return a.infinity;
    if (a.infinity) return false;
    if (a.x != b.x) return a.x < b.x;
    return a.y < b.y;
}

int main(int argc, char** argv) {
    try {
        if (argc != 3) throw std::runtime_error("usage: join input.txt receipt.json");
        std::ifstream in(argv[1]);
        if (!in) throw std::runtime_error("missing input");
        uint64_t qx, qy, r;
        int m;
        in >> qx >> qy >> r >> m;
        if (!in || m != 6 || r != 549756390943ULL) throw std::runtime_error("header");
        Point target = finite(qx, qy);
        if (!on_curve(target)) throw std::runtime_error("target curve");
        std::array<std::vector<Seed>, 6> base;
        const std::array<int, 6> rotations{0, 5, 10, 15, 20, 25};
        for (int slot = 0; slot < 6; ++slot) {
            int rotation, count;
            in >> rotation >> count;
            if (!in || rotation != rotations[slot] || count != 128)
                throw std::runtime_error("slot header");
            base[slot].reserve(128);
            for (int index = 0; index < count; ++index) {
                uint64_t x, y;
                int col, mask, sign, image;
                in >> x >> y >> col >> mask >> sign >> image;
                if (!in || col < 0 || col >= 26 || mask <= 0 || mask >= 64 ||
                    sign < 0 || sign > 1 || image < 0 || image > 1 ||
                    image != (index >= 64)) throw std::runtime_error("row");
                Point point = finite(x, y);
                if (!on_curve(point)) throw std::runtime_error("point curve");
                base[slot].push_back({point, uint16_t(col), uint16_t(mask),
                                      uint8_t(sign), uint8_t(image)});
            }
        }
        std::string extra;
        if (in >> extra) throw std::runtime_error("trailing input");
        const auto setup_start = std::chrono::steady_clock::now();
        std::vector<Triple> left;
        left.reserve(128ULL * 128 * 128);
        bool setup_cap = false, online_cap = false, memory_guard = false;
        for (uint8_t i = 0; i < 128 && !setup_cap && !memory_guard; ++i)
            for (uint8_t j = 0; j < 128 && !setup_cap && !memory_guard; ++j) {
                Point pair = add(base[0][i].point, base[1][j].point);
                for (uint8_t k = 0; k < 128; ++k) {
                    left.push_back({add(pair, base[2][k].point), {i, j, k}});
                    if ((left.size() & 65535) == 0) {
                        setup_cap = elapsed_ns(setup_start) >= 120000000000ULL;
                        memory_guard = peak_rss_bytes() >= 4ULL*1024*1024*1024;
                        if (setup_cap || memory_guard) break;
                    }
                }
            }
        if (!setup_cap && !memory_guard) {
            std::sort(left.begin(), left.end(), [](const Triple& a, const Triple& b) {
                return less_point(a.sum, b.sum);
            });
            setup_cap = elapsed_ns(setup_start) >= 120000000000ULL;
            memory_guard = peak_rss_bytes() >= 4ULL*1024*1024*1024;
        }
        uint64_t setup_ns = elapsed_ns(setup_start);
        uint64_t probes = 0, hits = 0;
        std::array<uint8_t, 6> chosen{};
        bool found = false;
        uint64_t online_ns = 0, check_ns = 0;
        if (!setup_cap && !memory_guard) {
            const auto online_start = std::chrono::steady_clock::now();
            for (uint8_t i = 0; i < 128 && !found && !online_cap && !memory_guard; ++i)
                for (uint8_t j = 0; j < 128 && !found && !online_cap && !memory_guard; ++j) {
                    Point pair = add(base[3][i].point, base[4][j].point);
                    for (uint8_t k = 0; k < 128; ++k) {
                        Point right = add(pair, base[5][k].point);
                        Point needed = add(target, neg(right));
                        ++probes;
                        auto hit = std::lower_bound(left.begin(), left.end(), needed,
                            [](const Triple& row, Point key) { return less_point(row.sum, key); });
                        for (; hit != left.end() && hit->sum == needed; ++hit) {
                            ++hits;
                            auto check_start = std::chrono::steady_clock::now();
                            Point sum = hit->sum;
                            sum = add(sum, right);
                            check_ns += elapsed_ns(check_start);
                            if (!(sum == target)) throw std::runtime_error("false join hit");
                            chosen = {hit->ids[0], hit->ids[1], hit->ids[2], i, j, k};
                            found = true;
                            break;
                        }
                        if (found) break;
                        if ((probes & 16383) == 0) {
                            online_cap = elapsed_ns(online_start) >= 120000000000ULL;
                            memory_guard = peak_rss_bytes() >= 4ULL*1024*1024*1024;
                            if (online_cap || memory_guard) break;
                        }
                    }
                }
            online_ns = elapsed_ns(online_start);
        }
        const char* status = found ? "VERIFIED_SIX_POINT_ROW" :
            memory_guard ? "MEMORY_GUARD" : setup_cap ? "SETUP_TIME_CAP" :
            online_cap ? "ONLINE_TIME_CAP" : "FULL_SEARCH_NO_ROW";
        std::ofstream out(argv[2]);
        if (!out) throw std::runtime_error("receipt");
        out << "{\"kind\":\"n41_w6_adjacent_union_3plus3_join\",\"status\":\""
            << status << "\",\"target\":[" << qx << "," << qy << "],"
            << "\"setup_ns\":" << setup_ns << ",\"online_ns\":";
        if (setup_cap || (memory_guard && !probes)) out << "null";
        else out << online_ns;
        out << ",\"relation_check_ns\":" << check_ns
            << ",\"left_rows\":" << left.size() << ",\"right_probes\":" << probes
            << ",\"exact_hits\":" << hits << ",\"peak_rss_bytes\":"
            << peak_rss_bytes() << ",\"chosen_ids\":";
        if (!found) out << "null";
        else {
            out << "[";
            for (int i = 0; i < 6; ++i) out << (i ? "," : "") << unsigned(chosen[i]);
            out << "]";
        }
        out << "}\n";
        std::cout << status << " setup_ns=" << setup_ns << " online_ns="
                  << online_ns << " probes=" << probes << " hits=" << hits << "\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "error: " << error.what() << "\n";
        return 2;
    }
}
