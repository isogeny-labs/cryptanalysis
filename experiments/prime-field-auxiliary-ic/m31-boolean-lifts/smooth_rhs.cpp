#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <chrono>
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

static uint32_t orbit_key(uint32_t x) {
    uint32_t least=x;
    for (unsigned i=1; i<31; ++i) {
        x=((x<<1)&prime) | (x>>30);
        least=std::min(least,x);
    }
    return least;
}

static uint32_t inverse(uint32_t x) {
    uint64_t y=1, z=x;
    for (uint32_t e=prime-2; e; e>>=1, z=z*z%prime)
        if (e&1) y=y*z%prime;
    return uint32_t(y);
}

static void compact(std::vector<uint32_t>& keys) {
    std::sort(keys.begin(),keys.end());
    keys.erase(std::unique(keys.begin(),keys.end()),keys.end());
    for (size_t i=1; i<keys.size(); ++i)
        if ((keys[i]>>1)==(keys[i-1]>>1)) std::abort();
}

// A hit carries the class bit of the smooth representative.
static int lookup(const std::vector<uint32_t>& keys,uint32_t key) {
    auto it=std::lower_bound(keys.begin(),keys.end(),key*2);
    return it!=keys.end() && (*it>>1)==key ? int(*it&1) : -1;
}

static int orbit_census(const std::vector<Row>& rows,uint32_t nonsquare) {
    std::vector<uint32_t> direct,reciprocal;
    for (auto [x,mask]:rows) {
        if (!(x&1)) continue; // Removing powers of two preserves this orbit and class.
        unsigned label=!__builtin_parity(mask&nonsquare);
        direct.push_back(2*orbit_key(x)+label);
        reciprocal.push_back(2*orbit_key(inverse(x))+label);
    }
    compact(direct);
    compact(reciprocal);
    std::array<uint32_t,16> patterns{},positive{};
    for (auto row:rows) {
        uint64_t x=row.x;
        uint32_t r=(x*x%prime*x+2*x+14)%prime;
        if (!r) return 1; // The fixture group has odd order.
        uint32_t key=orbit_key(r),neg=orbit_key(prime-r);
        int labels[]={lookup(direct,key),lookup(direct,neg),
                      lookup(reciprocal,key),lookup(reciprocal,neg)};
        unsigned pattern=0;
        bool actual=square(r);
        for (unsigned j=0; j<4; ++j) if (labels[j]>=0) {
            if ((labels[j]^int(j&1))!=int(actual)) return 1;
            pattern|=1u<<j;
        }
        ++patterns[pattern];
        positive[pattern]+=actual;
    }
    std::puts("match_mask,coordinates,lifts");
    for (unsigned j=0; j<16; ++j) std::printf("%u,%u,%u\n",j,patterns[j],positive[j]);
    return 0;
}

// Pick the least word among the rotations of r and its complement.
// The low bit of the returned code records whether the complement won.
static uint32_t signed_key(uint32_t r) {
    uint32_t low=r, high=r;
    for (unsigned i=1; i<31; ++i) {
        r=((r<<1)&prime) | (r>>30);
        low=std::min(low,r);
        high=std::max(high,r);
    }
    return low<=prime-high ? 2*low : 2*(prime-high)+1;
}

static int orbit_timing(const std::vector<Row>& rows,uint32_t nonsquare) {
    using Clock=std::chrono::steady_clock;
    auto ns=[](auto duration) {
        return std::chrono::duration_cast<std::chrono::nanoseconds>(duration).count();
    };
    auto start=Clock::now();
    // Each least representative is <= (p-1)/2. Two bits encode miss or label.
    std::vector<uint8_t> table(1u<<28);
    for (auto [x,mask]:rows) {
        if (!(x&1)) continue;
        unsigned positive=!__builtin_parity(mask&nonsquare);
        for (auto r:{x,inverse(x)}) {
            auto key=signed_key(r);
            unsigned shift=2*((key>>1)&3);
            uint8_t &byte=table[key>>3];
            unsigned label=1+(positive^(key&1));
            unsigned old=(byte>>shift)&3;
            if (old && old!=label) return 1;
            byte|=label<<shift;
        }
    }
    auto setup=ns(Clock::now()-start);
    std::vector<uint8_t> a(rows.size()),b(rows.size());
    for (unsigned round=0; round<6; ++round) {
        unsigned hits=0;
        long long elapsed[2];
        for (unsigned pos=0; pos<2; ++pos) {
            unsigned arm=(round+pos)%2;
            start=Clock::now();
            for (size_t i=0; i<rows.size(); ++i) {
                uint64_t x=rows[i].x;
                uint32_t r=(x*x%prime*x+2*x+14)%prime;
                if (!arm) { a[i]=square(r); continue; }
                auto key=signed_key(r);
                unsigned entry=(table[key>>3]>>(2*((key>>1)&3)))&3;
                if (entry) { b[i]=(entry-1)^(key&1); ++hits; }
                else b[i]=square(r);
            }
            elapsed[arm]=ns(Clock::now()-start);
        }
        if (a!=b || hits!=235328) return 1;
        std::printf("%u,%zu,%u,%lld,%lld,%lld\n",round,rows.size(),hits,
                    static_cast<long long>(setup),elapsed[0],elapsed[1]);
    }
    return 0;
}

int main(int argc,char **argv) {
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
    if (argc==2 && std::strcmp(argv[1],"orbits")==0) return orbit_census(rows,nonsquare);
    if (argc==2 && std::strcmp(argv[1],"timing")==0) return orbit_timing(rows,nonsquare);
    if (argc!=1) return 1;
    std::sort(rows.begin(),rows.end(),[](Row a,Row b){return a.x<b.x;});
    // first[b] is the first row with (x >> 12) >= b. The last entry is
    // rows.size(), including when the last bucket is empty.
    constexpr unsigned shift = 12;
    std::vector<uint32_t> first((prime >> shift) + 2);
    size_t next = 0;
    for (size_t b = 0; b < first.size(); ++b) {
        while (next < rows.size() && (rows[next].x >> shift) < b) ++next;
        first[b] = static_cast<uint32_t>(next);
    }
    std::vector<std::array<uint32_t,2>> buckets(1u<<primes.size());
    uint32_t lifts=0, overlap=0, overlap_lifts=0, errors=0, mixed=0, used=0, mixed_rows=0;
    for (size_t i=0; i<rows.size(); ++i) {
        auto [x,mask]=rows[i];
        if (i && x==rows[i-1].x) return 1;
        uint32_t rhs=(uint64_t(x)*x%prime*x+2ull*x+14)%prime;
        bool label=square(rhs);
        lifts+=label;
        ++buckets[mask][label];
        const auto bucket = rhs >> shift;
        auto end = rows.begin() + first[bucket+1];
        auto it = std::lower_bound(rows.begin() + first[bucket], end, rhs,
                                   [](const Row& a, uint32_t b) { return a.x < b; });
        if (it!=end && it->x==rhs) {
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
