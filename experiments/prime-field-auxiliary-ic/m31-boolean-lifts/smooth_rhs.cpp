#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>

constexpr uint32_t prime = 2147483647;
struct Row { uint32_t x, parity; };
constexpr std::array<uint32_t,24> primes = {2,3,5,7,11,13,17,19,23,29,31,37,
                                             41,43,47,53,59,61,67,71,73,79,83,89};

static bool square(uint32_t x) {
    uint64_t y=x;
    for (int i=0; i<30; ++i) y=y*y%prime;
    return y==x;
}

int main() {
    std::vector<Row> rows{{1,0}};
    uint32_t nonsquare = 0;
    for (size_t j=0; j<primes.size(); ++j) {
        auto q=primes[j];
        if (!square(q)) nonsquare |= 1u<<j;
        const size_t before=rows.size();
        for (size_t i=0; i<before; ++i) {
            auto parent=rows[i];
            auto mask=parent.parity;
            for (uint64_t x=uint64_t(parent.x)*q; x<prime; x*=q) {
                mask ^= 1u<<j;
                rows.push_back({uint32_t(x),mask});
            }
        }
    }
    std::sort(rows.begin(),rows.end(),[](Row a,Row b){return a.x<b.x;});
    std::vector<std::array<uint32_t,2>> buckets(1u<<primes.size());
    uint32_t lifts=0, overlap=0, overlap_lifts=0, errors=0, mixed=0, used=0, mixed_rows=0;
    for (size_t i=0; i<rows.size(); ++i) {
        auto [x,mask]=rows[i];
        if (i && x==rows[i-1].x) return 1;
        uint32_t rhs=(uint64_t(x)*x%prime*x+2ull*x+14)%prime;
        bool label=square(rhs);
        lifts+=label;
        ++buckets[mask][label];
        auto it=std::lower_bound(rows.begin(),rows.end(),rhs,[](Row a,uint32_t b){return a.x<b;});
        if (it!=rows.end() && it->x==rhs) {
            if (label != (__builtin_parity(it->parity & nonsquare)==0)) return 1;
            ++overlap;
            overlap_lifts+=label;
        }
    }
    uint32_t pure_negatives=0, pure_positives=0;
    for (auto b:buckets) {
        used+=bool(b[0]+b[1]);
        if (b[0] && b[1]) { ++mixed; mixed_rows+=b[0]+b[1]; }
        if (!b[1]) pure_negatives+=b[0];
        if (!b[0]) pure_positives+=b[1];
        errors+=std::min(b[0],b[1]);
    }
    if (rows.size()!=3846525 || lifts!=1924024) return 1;
    std::puts("coordinates,lifts,signatures,mixed_signatures,coordinates_in_mixed,pure_negative_rows,pure_positive_rows,minimum_errors,smooth_rhs,smooth_rhs_lifts");
    std::printf("%zu,%u,%u,%u,%u,%u,%u,%u,%u,%u\n",rows.size(),lifts,used,mixed,mixed_rows,pure_negatives,pure_positives,errors,overlap,overlap_lifts);
}
