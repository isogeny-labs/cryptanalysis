// Enumerate the 13-term target-conditioned resultant over all W11 free codes.
#define main inherited_join_main
#include "../n41_w11_fivepair_native_join_20261018/join.cpp"
#undef main
#include <set>
#include <sys/resource.h>

using Powers = std::array<uint64_t, 5>;
struct Product { uint64_t first, second; Powers a, b; };

static uint64_t frob(uint64_t v, unsigned rotation) {
    for (unsigned i = 0; i < rotation; ++i) v = sqr(v);
    return v;
}

int main(int argc, char** argv) {
    try {
        if (argc != 3) throw std::runtime_error("usage: census_all resultant_input.tsv output.json");
        const auto start = std::chrono::steady_clock::now();
        std::ifstream in(argv[1]);
        if (!in) throw std::runtime_error("missing frozen input");
        std::string tag;
        int targets, valid_count, term_count;
        in >> tag >> targets >> valid_count >> term_count;
        if (tag != "FREECODE" || targets != 25 || valid_count != 281 || term_count != 13)
            throw std::runtime_error("unexpected frozen input header");
        constexpr std::array<int, 10> bits{0, 1, 2, 3, 4, 6, 7, 8, 9, 10};
        std::array<Product, 1024> products{};
        for (int code = 0; code < 1024; ++code) {
            uint64_t a = 0;
            for (int j = 0; j < 10; ++j) if ((code >> j) & 1) a ^= 1ULL << (bits[j] + 1);
            const uint64_t p = mul(a, a ^ 112);
            auto& row = products[code];
            row.first = frob(p, 12);
            row.second = frob(p, 24);
            row.a[0] = row.b[0] = 1;
            for (int i = 1; i <= 4; ++i) {
                row.a[i] = mul(row.a[i - 1], row.first);
                row.b[i] = mul(row.b[i - 1], row.second);
            }
        }
        std::set<int> valid;
        for (int i = 0; i < valid_count; ++i) {
            int code;
            uint64_t p1, p2;
            in >> tag >> code >> p1 >> p2;
            if (tag != "P" || code < 0 || code >= 1024 || !valid.insert(code).second ||
                products[code].first != p1 || products[code].second != p2)
                throw std::runtime_error("archived product mismatch");
        }
        if (!valid.contains(253) || !valid.contains(63))
            throw std::runtime_error("archived witness absent");
        std::ofstream out(argv[2]);
        if (!out) throw std::runtime_error("cannot open output");
        out << "{\"status\":\"COMPLETE_N41_W11_ALLCODE_RESULTANT_CENSUS\","
               "\"candidate_id\":null,\"curve_id\":\"EC1N41Ckb1h7d5e80d3c4d0\","
               "\"all_codes\":1024,\"archived_valid_codes\":281,\"targets\":[";
        uint64_t total_zeros = 0, total_valid_zeros = 0, total_invalid_zeros = 0;
        for (int k = 0; k < targets; ++k) {
            int index;
            uint64_t x, y;
            in >> tag >> index >> x >> y;
            if (tag != "T" || index != k || x >= (1ULL << 41) || y >= (1ULL << 41) ||
                !on_curve(Point{x, y, false})) throw std::runtime_error("target mismatch");
            uint64_t coeff[5][5]{};
            std::set<std::pair<int, int>> seen;
            for (int t = 0; t < 13; ++t) {
                int row, i, j;
                uint64_t value;
                in >> tag >> row >> i >> j >> value;
                if (tag != "C" || row != k || i < 0 || i > 4 || j < 0 || j > 4 ||
                    !value || value >= (1ULL << 41) || !seen.insert({i, j}).second)
                    throw std::runtime_error("coefficient mismatch");
                coeff[i][j] = value;
            }
            const auto query_start = std::chrono::steady_clock::now();
            uint64_t zeros = 0, valid_zeros = 0, invalid_zeros = 0;
            bool positive = false;
            std::vector<std::pair<int, int>> zero_pairs;
            for (int a = 0; a < 1024; ++a) {
                uint64_t weighted[5]{};
                for (int j = 0; j < 5; ++j) for (int i = 0; i < 5; ++i)
                    if (coeff[i][j]) weighted[j] ^= mul(coeff[i][j], products[a].a[i]);
                for (int b = 0; b < 1024; ++b) {
                    uint64_t value = 0;
                    for (int j = 0; j < 5; ++j)
                        if (weighted[j]) value ^= mul(weighted[j], products[b].b[j]);
                    if (value) continue;
                    ++zeros;
                    const bool both_valid = valid.contains(a) && valid.contains(b);
                    valid_zeros += both_valid;
                    invalid_zeros += !both_valid;
                    zero_pairs.push_back({a, b});
                    if (k == 0 && a == 253 && b == 63) positive = true;
                }
            }
            if (k == 0 && !positive) throw std::runtime_error("positive root absent");
            total_zeros += zeros;
            total_valid_zeros += valid_zeros;
            total_invalid_zeros += invalid_zeros;
            out << (k ? "," : "") << "{\"index\":" << k << ",\"target_point\":["
                << x << "," << y << "],\"all_code_zero_pairs\":" << zeros
                << ",\"both_valid_zero_pairs\":" << valid_zeros
                << ",\"at_least_one_invalid_zero_pairs\":" << invalid_zeros
                << ",\"zero_pairs\":[";
            for (size_t n = 0; n < zero_pairs.size(); ++n)
                out << (n ? "," : "") << "[" << zero_pairs[n].first << ","
                    << zero_pairs[n].second << "]";
            out << "],\"query_seconds\":" << elapsed(query_start) << "}";
        }
        std::string trailing;
        if (in >> trailing) throw std::runtime_error("trailing frozen input");
        struct rusage usage{};
        getrusage(RUSAGE_SELF, &usage);
        out << "],\"total_zero_pairs\":" << total_zeros
            << ",\"total_both_valid_zero_pairs\":" << total_valid_zeros
            << ",\"total_invalid_zero_pairs\":" << total_invalid_zeros
            << ",\"wall_seconds\":" << elapsed(start)
            << ",\"self_maxrss_raw\":" << usage.ru_maxrss << "}\n";
        std::cout << "COMPLETE_N41_W11_ALLCODE_RESULTANT_CENSUS\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "ERROR " << error.what() << "\n";
        return 2;
    }
}
