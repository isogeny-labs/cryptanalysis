// Streaming sparse GF(2) elimination for degree-six block certificates.
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <sys/resource.h>
#include <unordered_map>
#include <vector>

using Mask = std::uint64_t;
using Column = std::uint32_t;
using RowId = std::uint32_t;

struct Pivot {
    std::vector<Column> row;
    RowId source_row;
    std::vector<std::uint32_t> dependencies;
};

std::vector<Column> xor_sorted(const std::vector<Column>& left,
                               const std::vector<Column>& right) {
    std::vector<Column> out;
    out.reserve(left.size() + right.size());
    std::set_symmetric_difference(left.begin(), left.end(), right.begin(),
                                  right.end(), std::back_inserter(out));
    return out;
}

std::uint64_t rss_peak_raw() {
    rusage usage{};
    if (getrusage(RUSAGE_SELF, &usage) != 0) return 0;
    return static_cast<std::uint64_t>(usage.ru_maxrss);
}

double elapsed(std::chrono::steady_clock::time_point start) {
    return std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
}

int main(int argc, char** argv) {
  try {
    if (argc != 2) throw std::runtime_error("usage: sparse_block input.eqs");
    const auto start = std::chrono::steady_clock::now();
    std::ifstream input(argv[1]);
    if (!input) throw std::runtime_error("input open");
    std::string tag;
    int variables = 0, field_bits = 0, base_degree = 0, multiplier_degree = 0;
    input >> tag >> variables >> field_bits >> base_degree >> multiplier_degree;
    if (tag != "EQS" || (variables != 13 && variables != 35) ||
        (field_bits != 41 && field_bits != 131) || base_degree != 4 ||
        multiplier_degree != 2)
        throw std::runtime_error("header mismatch");
    std::vector<std::vector<Mask>> equations(field_bits);
    for (int bit = 0; bit < field_bits; ++bit) {
        int recorded = -1, count = -1;
        input >> recorded >> count;
        if (!input || recorded != bit || count < 0 || count > 100000)
            throw std::runtime_error("equation header");
        auto& row = equations[bit];
        row.reserve(static_cast<std::size_t>(count));
        for (int i = 0; i < count; ++i) {
            Mask mask;
            input >> mask;
            if (!input || (mask >> variables) || __builtin_popcountll(mask) > 4)
                throw std::runtime_error("equation monomial");
            row.push_back(mask);
        }
        if (!std::is_sorted(row.begin(), row.end()) ||
            std::adjacent_find(row.begin(), row.end()) != row.end())
            throw std::runtime_error("equation support order");
    }
    std::string extra;
    if (input >> extra) throw std::runtime_error("trailing input");

    std::unordered_map<Mask, Column> column;
    column.reserve(variables == 35 ? 2200000 : 6000);
    std::vector<Mask> factors;
    Column next = 0;
    for (int degree = 0; degree <= 6; ++degree) {
        if (degree == 0) {
            column.emplace(0, next++);
            factors.push_back(0);
            continue;
        }
        // Ascending bit positions reproduce itertools.combinations order.
        auto visit = [&](auto&& self, int first, int remaining, Mask mask) -> void {
            if (!remaining) {
                column.emplace(mask, next++);
                if (degree <= 2) factors.push_back(mask);
                return;
            }
            for (int bit = first; bit <= variables - remaining; ++bit)
                self(self, bit + 1, remaining - 1, mask | (Mask(1) << bit));
        };
        visit(visit, 0, degree, 0);
    }
    const Column columns = next;
    const std::uint32_t factor_count = static_cast<std::uint32_t>(factors.size());
    if ((variables == 13 && (columns != 4096 || factor_count != 92)) ||
        (variables == 35 && (columns != 2007328 || factor_count != 631)))
        throw std::runtime_error("monomial enumeration");
    std::vector<std::int32_t> pivot_index(columns, -1);
    std::vector<Pivot> pivots;
    pivots.reserve(field_bits * factor_count);
    std::uint64_t xors = 0, largest_row = 0, largest_trace = 0;
    const RowId requested = static_cast<RowId>(field_bits * factor_count);
    RowId processed = 0;
    std::cout << "SETUP " << variables << ' ' << field_bits << ' ' << columns << ' '
              << factor_count << ' ' << requested << ' ' << elapsed(start) << ' '
              << rss_peak_raw() << '\n' << std::flush;
    for (std::uint32_t fi = 0; fi < factor_count; ++fi) {
        for (int bit = 0; bit < field_bits; ++bit) {
            const RowId row_id = static_cast<RowId>(bit * factor_count + fi);
            ++processed;
            const Mask factor = factors[fi];
            std::vector<Column> row;
            row.reserve(equations[bit].size());
            for (Mask mask : equations[bit]) {
                auto found = column.find(mask | factor);
                if (found == column.end()) throw std::runtime_error("missing column");
                row.push_back(found->second);
            }
            std::sort(row.begin(), row.end());
            std::vector<Column> reduced;
            reduced.reserve(row.size());
            for (std::size_t i = 0; i < row.size();) {
                std::size_t j = i + 1;
                while (j < row.size() && row[j] == row[i]) ++j;
                if ((j - i) & 1) reduced.push_back(row[i]);
                i = j;
            }
            row.swap(reduced);
            std::vector<std::uint32_t> dependencies;
            while (!row.empty()) {
                largest_row = std::max<std::uint64_t>(largest_row, row.size());
                largest_trace = std::max<std::uint64_t>(largest_trace, dependencies.size());
                if (row.size() == 1 && row[0] == 0) {
                    // Expand the acyclic reduction trace only for a terminal identity.
                    std::vector<std::uint8_t> selected(pivots.size(), 0);
                    std::vector<std::uint8_t> source_parity(requested, 0);
                    source_parity[row_id] = 1;
                    for (std::uint32_t index : dependencies) selected[index] ^= 1;
                    for (std::size_t i = pivots.size(); i-- > 0;) {
                        if (!selected[i]) continue;
                        const auto& witness = pivots[i];
                        source_parity[witness.source_row] ^= 1;
                        for (std::uint32_t index : witness.dependencies)
                            selected[index] ^= 1;
                    }
                    const auto count = std::count(source_parity.begin(),
                                                  source_parity.end(), 1);
                    std::cout << "REJECT_CERTIFICATE " << processed << ' '
                              << pivots.size() << ' ' << xors << ' '
                              << count << ' ' << elapsed(start) << ' '
                              << rss_peak_raw() << '\n';
                    std::cout << "CERT_ROWS";
                    for (RowId id = 0; id < requested; ++id) {
                        if (source_parity[id])
                            std::cout << ' ' << (id / factor_count) << ':'
                                      << factors[id % factor_count];
                    }
                    std::cout << '\n' << std::flush;
                    return 0;
                }
                const Column pivot = row.back();
                const auto prior = pivot_index[pivot];
                if (prior < 0) {
                    pivot_index[pivot] = static_cast<std::int32_t>(pivots.size());
                    pivots.push_back({std::move(row), row_id, std::move(dependencies)});
                    break;
                }
                row = xor_sorted(row, pivots[prior].row);
                dependencies.push_back(static_cast<std::uint32_t>(prior));
                ++xors;
            }
            if (processed % 1000 == 0 || processed == requested)
                std::cout << "PROGRESS " << processed << ' ' << pivots.size()
                          << ' ' << xors << ' ' << largest_row << ' '
                          << largest_trace << ' ' << elapsed(start) << ' '
                          << rss_peak_raw() << '\n' << std::flush;
        }
    }
    std::cout << "UNRESOLVED_AT_DEGREE6 " << requested << ' ' << pivots.size()
              << ' ' << xors << ' ' << elapsed(start) << ' ' << rss_peak_raw()
              << '\n' << std::flush;
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "PRODUCER_FAILURE " << error.what() << '\n';
    return 2;
  }
}
