// Exact coordinate-subspace occupancy of the frozen 19-bit W20 pair-code set.
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

constexpr unsigned SOURCE_BITS = 19;
constexpr unsigned SOURCE_SIZE = 1u << SOURCE_BITS;
constexpr unsigned MASK_SIZE = 1u << 20;
constexpr unsigned SEED = 898618;

unsigned canonical_code(unsigned mask) {
    unsigned code = 0, out_bit = 0;
    unsigned pivot = 31 - __builtin_clz(SEED);
    for (unsigned bit=0; bit<20; ++bit) {
        if (bit == pivot) continue;
        code |= ((mask >> bit) & 1u) << out_bit;
        ++out_bit;
    }
    if (out_bit != SOURCE_BITS) throw std::runtime_error("canonical bit count");
    return code;
}

struct Row {
    unsigned free_bits=0, mask=0, nonempty=0, full=0;
    std::array<unsigned,17> histogram{};
};

int main(int argc, char** argv) {
    try {
        if (argc != 2) throw std::runtime_error("usage: census support_w20.tsv");
        auto started=std::chrono::steady_clock::now();
        std::vector<int> columns(MASK_SIZE,-1);
        std::ifstream input(argv[1]);
        if (!input) throw std::runtime_error("cannot open support table");
        unsigned mask, column, shift, support_rows=0;
        while (input >> mask >> column >> shift) {
            if (mask >= MASK_SIZE || columns[mask] != -1)
                throw std::runtime_error("bad or duplicate support row");
            columns[mask]=int(column);
            ++support_rows;
        }
        std::vector<uint8_t> valid(SOURCE_SIZE,0);
        unsigned count=0;
        for (unsigned a=0; a<MASK_SIZE; ++a) {
            unsigned b=a ^ SEED;
            if (a < b && columns[a] >= 0 && columns[b] >= 0 &&
                columns[a] != columns[b]) {
                unsigned code=canonical_code(a);
                if (valid[code]) throw std::runtime_error("duplicate valid code");
                valid[code]=1;
                ++count;
            }
        }
        if (count != 132045) throw std::runtime_error("source count mismatch");
        std::cout << "SOURCE " << support_rows << " " << count << "\n";
        for (unsigned free_bits=2; free_bits<=4; ++free_bits) {
            Row best{};
            best.nonempty=SOURCE_SIZE+1;
            unsigned configurations=0;
            for (unsigned free_mask=1; free_mask<SOURCE_SIZE; ++free_mask) {
                if (__builtin_popcount(free_mask) != int(free_bits)) continue;
                std::array<unsigned,16> submasks{};
                unsigned subcount=0, sub=free_mask;
                while (true) {
                    submasks[subcount++]=sub;
                    if (sub==0) break;
                    sub=(sub-1)&free_mask;
                }
                if (subcount != (1u<<free_bits)) throw std::runtime_error("submask count");
                Row row{};
                row.free_bits=free_bits;
                row.mask=free_mask;
                for (unsigned base=0; base<SOURCE_SIZE; ++base) {
                    if (base & free_mask) continue;
                    unsigned occupied=0;
                    for (unsigned j=0; j<subcount; ++j)
                        occupied += valid[base|submasks[j]];
                    ++row.histogram[occupied];
                }
                for (unsigned k=1; k<=subcount; ++k)
                    row.nonempty += row.histogram[k];
                row.full=row.histogram[subcount];
                unsigned source_sum=0;
                for (unsigned k=1; k<=subcount; ++k)
                    source_sum += k*row.histogram[k];
                if (source_sum != count ||
                    row.nonempty+row.histogram[0] != (SOURCE_SIZE>>free_bits))
                    throw std::runtime_error("partition conservation");
                std::cout << "ROW " << free_bits << " " << free_mask
                          << " " << row.nonempty << " " << row.full;
                for (unsigned k=0; k<=subcount; ++k)
                    std::cout << " " << row.histogram[k];
                std::cout << "\n";
                if (row.nonempty < best.nonempty ||
                    (row.nonempty == best.nonempty && row.full > best.full) ||
                    (row.nonempty == best.nonempty && row.full == best.full &&
                     row.mask < best.mask)) best=row;
                ++configurations;
            }
            std::cout << "BEST " << free_bits << " " << configurations
                      << " " << best.mask << " " << best.nonempty
                      << " " << best.full << "\n";
        }
        double seconds=std::chrono::duration<double>(
            std::chrono::steady_clock::now()-started).count();
        std::cout << "DONE " << std::setprecision(12) << seconds << "\n";
        return 0;
    } catch (const std::exception& err) {
        std::cerr << err.what() << "\n";
        return 1;
    }
}
