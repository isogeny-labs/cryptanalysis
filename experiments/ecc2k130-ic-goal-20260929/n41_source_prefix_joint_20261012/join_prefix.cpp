// Exhaustive N41 raw-target join within one frozen source-mask prefix family.
#include <bitset>
#define main archived_join_main
#include "../n41_w8_ninepair_join_control_20261012/join9.cpp"
#undef main

struct SourceState { Point point; std::bitset<128> columns; uint16_t a, b; };
static constexpr unsigned COUNT = 30952;

int main(int argc, char** argv) {
  try {
    if (argc != 11) throw std::runtime_error("usage: join_prefix pairs.tsv depth p0 ... p7");
    const unsigned depth = unsigned(std::stoul(argv[2]));
    if (depth < 1 || depth > 8) throw std::runtime_error("depth");
    std::array<unsigned, 8> prefixes{};
    for (unsigned i = 0; i < 8; ++i) {
      prefixes[i] = unsigned(std::stoul(argv[3 + i]));
      if (prefixes[i] >= (1u << depth)) throw std::runtime_error("prefix range");
    }
    const auto start = std::chrono::steady_clock::now();
    std::ifstream in(argv[1]);
    if (!in) throw std::runtime_error("source input missing");
    std::string tag;
    int slots, targets;
    in >> tag >> slots >> targets;
    if (tag != "ECC2K41_ALLSEED4" || slots != 4 || targets != 4)
      throw std::runtime_error("source header");
    std::array<std::vector<SourceState>, 4> lists;
    std::array<Point, 4> raw{};
    unsigned source_rows = 0, target_rows = 0;
    while (in >> tag) {
      if (tag == "T") {
        int id; uint64_t x, y;
        in >> id >> x >> y;
        if (id < 0 || id >= 4) throw std::runtime_error("target id");
        raw[id] = {x, y, false}; ++target_rows;
      } else if (tag == "S") {
        int slot, id, a, b, ca, cb, sa, sb; uint64_t x, y;
        in >> slot >> id >> a >> b >> ca >> cb >> sa >> sb >> x >> y;
        if (slot < 0 || slot >= 4 || a >= b || ca == cb ||
            ca < 0 || cb < 0 || ca >= 128 || cb >= 128 ||
            sa < 0 || sa > 1 || sb < 0 || sb > 1)
          throw std::runtime_error("source row");
        ++source_rows;
        unsigned pa = unsigned(a) >> (8 - depth);
        unsigned pb = unsigned(b) >> (8 - depth);
        bool direct = pa == prefixes[2 * slot] && pb == prefixes[2 * slot + 1];
        bool swapped = pb == prefixes[2 * slot] && pa == prefixes[2 * slot + 1];
        if (!direct && !swapped) continue;
        SourceState state{{x, y, false}, {}, uint16_t(a), uint16_t(b)};
        state.columns.set(unsigned(ca)); state.columns.set(unsigned(cb));
        lists[slot].push_back(state);
      } else throw std::runtime_error("source tag");
    }
    if (source_rows != 4 * COUNT || target_rows != 4)
      throw std::runtime_error("source incomplete");
    for (const auto& list : lists) if (list.empty()) throw std::runtime_error("empty source family");
    std::cout << "SOURCE_PASS " << source_rows;
    for (const auto& list : lists) std::cout << " " << list.size();
    std::cout << " " << elapsed(start) << "\n" << std::flush;

    std::unordered_multimap<Point, uint32_t, Hash> left;
    uint64_t left_seen = 0, left_kept = 0;
    for (unsigned a = 0; a < lists[0].size(); ++a)
      for (unsigned b = 0; b < lists[1].size(); ++b) {
        ++left_seen;
        const auto& A = lists[0][a]; const auto& B = lists[1][b];
        if ((A.columns & B.columns).any()) continue;
        if (a >= 65536 || b >= 65536) throw std::runtime_error("index overflow");
        left.emplace(add(A.point, B.point), uint32_t(a) | (uint32_t(b) << 16));
        ++left_kept;
      }
    std::cout << "LEFT_DONE " << left_seen << " " << left_kept << " "
              << elapsed(start) << "\n" << std::flush;
    uint64_t right_seen = 0, right_kept = 0, point_hits = 0, column_rejects = 0;
    for (unsigned c = 0; c < lists[2].size(); ++c)
      for (unsigned d = 0; d < lists[3].size(); ++d) {
        ++right_seen;
        const auto& C = lists[2][c]; const auto& D = lists[3][d];
        if ((C.columns & D.columns).any()) continue;
        ++right_kept;
        Point need = add(raw[1], negate(add(C.point, D.point)));
        auto range = left.equal_range(need);
        for (auto it = range.first; it != range.second; ++it) {
          ++point_hits;
          unsigned a = it->second & 65535u, b = it->second >> 16;
          auto cols = lists[0][a].columns | lists[1][b].columns;
          if ((cols & (C.columns | D.columns)).any()) {
            ++column_rejects; continue;
          }
          Point sum = add(add(add(lists[0][a].point, lists[1][b].point),
                              C.point), D.point);
          if (!(sum == raw[1])) throw std::runtime_error("group replay mismatch");
          std::cout << "HIT 1 " << a << " " << b << " " << c << " " << d
                    << " " << left_seen << " " << left_kept << " "
                    << right_seen << " " << right_kept << " " << point_hits
                    << " " << column_rejects << " " << elapsed(start) << "\n"
                    << std::flush;
          return 0;
        }
      }
    std::cout << "EXHAUSTED " << left_seen << " " << left_kept << " "
              << right_seen << " " << right_kept << " " << point_hits
              << " " << column_rejects << " " << elapsed(start) << "\n"
              << std::flush;
    return 0;
  } catch (const std::exception& e) {
    std::cerr << "ERROR " << e.what() << "\n";
    return 2;
  }
}
