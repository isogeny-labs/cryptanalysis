// Reuse the independently audited field/group kernel without changing it.
#define main archived_single_main
#include "../n41_w8_sixpair_mitm_20261011/join.cpp"
#undef main

struct PanelTarget {
    uint64_t scalar = 0;
    std::array<Point, 4> raw{};
};

int main(int argc, char** argv) {
    try {
        if (argc != 3) throw std::runtime_error("usage: batch_join states.tsv panel.tsv");
        auto start = std::chrono::steady_clock::now();
        std::array<std::array<State, 140>, 6> lists{};
        std::array<std::array<bool, 140>, 6> seen{};
        std::ifstream input(argv[1]);
        std::string tag;
        int slots, states, old_targets;
        input >> tag >> slots >> states >> old_targets;
        if (tag != "ECC2K41" || slots != 6 || states != 140 || old_targets != 4)
            throw std::runtime_error("state header");
        int check_rows = 0, state_rows = 0;
        while (input >> tag) {
            if (tag == "T") {
                int index; uint64_t x, y;
                input >> index >> x >> y;
            } else if (tag == "S") {
                int slot, sid, edge, a, b, sa, sb; uint64_t x, y;
                input >> slot >> sid >> edge >> a >> b >> sa >> sb >> x >> y;
                if (slot < 0 || slot >= 6 || sid < 0 || sid >= 140 ||
                    edge != sid / 4 || seen[slot][sid] || (a ^ b) != 184)
                    throw std::runtime_error("state row");
                lists[slot][sid] = {{x, y, false}, static_cast<uint8_t>(edge)};
                seen[slot][sid] = true;
                ++state_rows;
            } else if (tag == "C") {
                int64_t x1, y1, x2, y2, x3, y3;
                input >> x1 >> y1 >> x2 >> y2 >> x3 >> y3;
                Point result = add({uint64_t(x1), uint64_t(y1), false},
                                   {uint64_t(x2), uint64_t(y2), false});
                if ((x3 < 0) != result.infinity ||
                    (x3 >= 0 && (result.x != uint64_t(x3) || result.y != uint64_t(y3))))
                    throw std::runtime_error("Sage group check");
                ++check_rows;
            } else throw std::runtime_error("state tag");
        }
        if (state_rows != 840 || check_rows != 128)
            throw std::runtime_error("state or check count");
        for (const auto& slot : seen)
            for (bool value : slot) if (!value) throw std::runtime_error("missing state");
        std::ifstream panel(argv[2]);
        int target_count, raw_count;
        panel >> tag >> target_count >> raw_count;
        if (tag != "TARGETS" || target_count != 128 || raw_count != 4)
            throw std::runtime_error("panel header");
        std::array<PanelTarget, 128> targets{};
        std::array<std::array<bool, 4>, 128> target_seen{};
        int target_rows = 0;
        while (panel >> tag) {
            int i, j; uint64_t k, x, y;
            panel >> i >> j >> k >> x >> y;
            if (tag != "T" || i < 0 || i >= 128 || j < 0 || j >= 4 ||
                target_seen[i][j] || (targets[i].scalar && targets[i].scalar != k))
                throw std::runtime_error("panel row");
            targets[i].scalar = k;
            targets[i].raw[j] = {x, y, false};
            target_seen[i][j] = true;
            ++target_rows;
        }
        if (target_rows != 512) throw std::runtime_error("panel count");
        std::cout << "CHECK_PASS 128 512 " << elapsed(start) << "\n" << std::flush;

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
        std::cout << "LEFT_DONE " << left.size() << " " << elapsed(start) << "\n" << std::flush;
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
        std::cout << "RIGHT_DONE " << right.size() << " " << elapsed(start) << "\n" << std::flush;
        int solved = 0;
        for (int target = 0; target < 128; ++target) {
            double target_start = elapsed(start);
            bool found = false;
            uint64_t probes = 0;
            for (int raw = 0; raw < 4 && !found; ++raw) {
                for (const auto& item : right) {
                    Point need = add(targets[target].raw[raw], negate(item.point));
                    auto range = left.equal_range(need);
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
                        if (!(add(it->first, item.point) == targets[target].raw[raw]))
                            throw std::runtime_error("group replay after hash hit");
                        std::cout << "ROW " << target << " " << raw << " "
                                  << targets[target].scalar;
                        for (unsigned id : ids) std::cout << " " << id;
                        std::cout << " " << probes << " " << (elapsed(start) - target_start)
                                  << " " << elapsed(start) << "\n" << std::flush;
                        ++solved;
                        found = true;
                        break;
                    }
                    ++probes;
                    if (found) break;
                }
            }
            if (!found)
                std::cout << "MISS " << target << " " << targets[target].scalar
                          << " " << probes << " " << (elapsed(start) - target_start)
                          << " " << elapsed(start) << "\n" << std::flush;
        }
        std::cout << "COMPLETE " << solved << " 128 " << elapsed(start) << "\n" << std::flush;
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "ERROR " << error.what() << "\n";
        return 2;
    }
}
