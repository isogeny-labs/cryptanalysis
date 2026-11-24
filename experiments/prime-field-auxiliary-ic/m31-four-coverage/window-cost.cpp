#ifdef M31_NEON_PANEL
#include <arm_neon.h>
#endif
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <random>
#include <vector>

using Word = std::uint32_t;
using Keys = std::array<Word,17>;
constexpr Word prime = 2147483647;
constexpr std::array<int,10> offsets{0,1,3,4,9,12,15,17,19,21};

bool scan(const Keys& keys, Word x) {
    Word found = 0;
    for (Word k : keys) found |= (k == x);
    return found != 0;
}

#ifdef M31_NEON_PANEL
// Compare four queries per register, narrowing the Boolean masks only at output.
void scan_batch(const Keys& keys, const Word* queries, unsigned char* out, int count) {
    int i = 0;
    for (; i + 8 <= count; i += 8) {
        auto left = vld1q_u32(queries + i);
        auto right = vld1q_u32(queries + i + 4);
        auto hits_left = vdupq_n_u32(0);
        auto hits_right = vdupq_n_u32(0);
        for (Word key : keys) {
            auto target = vdupq_n_u32(key);
            hits_left = vorrq_u32(hits_left, vceqq_u32(left, target));
            hits_right = vorrq_u32(hits_right, vceqq_u32(right, target));
        }
        auto hits = vcombine_u16(vmovn_u32(hits_left), vmovn_u32(hits_right));
        vst1_u8(out + i, vshr_n_u8(vmovn_u16(hits), 7));
    }
    for (; i < count; ++i) out[i] = scan(keys, queries[i]);
}
#ifdef M31_REUSE_PANEL
constexpr int arm_count = 5;
#else
constexpr int arm_count = 4;
#endif
#else
constexpr int arm_count = 3;
#endif

int choose(const Keys& keys) {
    for (int shift : offsets) {
        std::array<std::uint64_t,2> seen{};
        bool collision = false;
        for (Word x : keys) {
            Word slot = (x >> shift) & 127;
            auto mask = UINT64_C(1) << (slot & 63);
            auto& word = seen[slot >> 6];
            if (word & mask) { collision = true; break; }
            word |= mask;
        }
        if (!collision) return shift;
    }
    return -1;
}

int main(int argc, char** argv) {
    if (argc != 2) return 1;
    std::mt19937 rng(std::stoul(argv[1]));
    std::vector<Keys> bases(4096);
    for (auto& keys : bases)
        for (auto& x : keys)
            if (!(std::cin >> x) || x >= prime) return 2;
    std::shuffle(bases.begin(), bases.end(), rng);
    std::cout << "queries,round,method,ns_per_base\n";
    for (int count : {1,4,16,64,256,1024}) {
        std::vector<Word> queries(bases.size()*count);
        std::vector<unsigned char> expected(queries.size()), out(queries.size());
        for (size_t i=0; i<queries.size(); ++i) {
            const auto& keys = bases[i/count];
            Word x = (rng() & 1) ? keys[rng()%keys.size()] : rng()%prime;
            queries[i] = x;
            expected[i] = std::find(keys.begin(),keys.end(),x) != keys.end();
        }
        for (int round=0; round<3*arm_count; ++round) for (int j=0; j<arm_count; ++j) {
            int arm = (round + (round/arm_count%2 ? arm_count-1-j : j))%arm_count;
            auto start = std::chrono::steady_clock::now();
#ifdef M31_REUSE_PANEL
            std::array<unsigned char,128> candidate{};
#endif
            for (size_t b=0; b<bases.size(); ++b) {
                const auto& keys = bases[b];
                auto apply = [&](auto lookup) {
                    for (int i=0; i<count; ++i) out[b*count+i] = lookup(queries[b*count+i]);
                };
#ifdef M31_NEON_PANEL
                if (arm==3) scan_batch(keys, queries.data()+b*count, out.data()+b*count, count);
#endif
#ifdef M31_REUSE_PANEL
                if (arm==4) {
                    int shift = choose(keys);
                    if (shift<0) { apply([&](Word x){return scan(keys,x);}); continue; }
                    for (unsigned char i=0; i<keys.size(); ++i)
                        candidate[(keys[i]>>shift)&127] = i;
                    apply([&](Word x){return keys[candidate[(x>>shift)&127]] == x;});
                }
#endif
                if (arm==0) apply([&](Word x){return scan(keys,x);});
                if (arm==1) {
                    auto sorted = keys;
                    std::sort(sorted.begin(),sorted.end());
                    apply([&](Word x){return std::binary_search(sorted.begin(),sorted.end(),x);});
                }
                if (arm==2) {
                    int shift = choose(keys);
                    if (shift<0) { apply([&](Word x){return scan(keys,x);}); continue; }
                    std::array<Word,128> table;
                    table.fill(prime);
                    for (Word x : keys) table[(x>>shift)&127] = x;
                    apply([&](Word x){return table[(x>>shift)&127] == x;});
                }
            }
            auto elapsed = std::chrono::steady_clock::now()-start;
            if (expected!=out) return 3;
            if (round>=arm_count) std::cout << count << ',' << round-arm_count << ',' <<
                std::array{"scan","sort","window","batch","reuse"}[arm] << ',' <<
                std::chrono::duration<double,std::nano>(elapsed).count()/bases.size() << '\n';
        }
    }
}
