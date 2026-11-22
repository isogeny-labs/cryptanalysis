// Target-conditioned linear-span gate across two free W8 two-pair sums.
#define main inherited_join_main
#include "../n41_w8_ninepair_join_control_20261012/join9.cpp"
#undef main
#include <bitset>
#include <map>
#include <random>
#include <set>
#include <unordered_set>

using u64 = uint64_t;
constexpr int N = 41, COUNT = 30952;
struct PairState { Point point; std::bitset<128> columns; };
struct Partial { Point point; u64 reciprocal; std::bitset<128> columns; };

int trace(u64 a) {
    u64 total = 0;
    for (int i=0;i<N;i++) { total ^= a; a=sqr(a); }
    if (total > 1) throw std::runtime_error("trace is not binary");
    return int(total);
}

bool insert(u64 value, std::array<u64,N>& pivots) {
    for (int bit=N-1;bit>=0;bit--) if (value & (1ULL<<bit)) {
        if (pivots[bit]) value ^= pivots[bit];
        else { pivots[bit]=value; return true; }
    }
    return false;
}
bool contains(u64 value,const std::array<u64,N>& pivots) {
    for (int bit=N-1;bit>=0;bit--) if (value & (1ULL<<bit)) {
        if (!pivots[bit]) return false;
        value ^= pivots[bit];
    }
    return true;
}
std::vector<u64> basis(const std::vector<Partial>& partials) {
    std::array<u64,N> pivots{}; std::vector<u64> result;
    for (const auto& p:partials) if (insert(p.reciprocal,pivots)) result.push_back(p.reciprocal);
    return result;
}

struct Gate { int left_rank,right_rank,cross_rank,total_rank; bool span_consistent; int exact_hits; };
Gate gate(const std::vector<Partial>& left,const std::vector<Partial>& right,
          u64 target_reciprocal,Point target) {
    // An empty source region is impossible, even if the other region's
    // coordinate span alone contains the public target constant.
    if (left.empty() || right.empty())
        return {0,0,0,0,false,0};
    auto C=basis(left), D=basis(right);
    std::array<u64,N> cross{},all{};
    for (u64 c:C) insert(sqr(c),all);
    for (u64 d:D) insert(sqr(d),all);
    for (u64 c:C) for (u64 d:D) {
        u64 z=mul(mul(target_reciprocal,c),d);
        u64 value=sqr(z)^z;
        insert(value,cross); insert(value,all);
    }
    int rc=0,ra=0; for (u64 v:cross) rc+=v!=0; for (u64 v:all) ra+=v!=0;
    std::unordered_multimap<Point,const Partial*,Hash> index;
    index.reserve(right.size());
    for (const auto& p:right) index.emplace(p.point,&p);
    int hits=0;
    for (const auto& p:left) {
        Point need=add(target,negate(p.point));
        auto range=index.equal_range(need);
        for (auto it=range.first;it!=range.second;++it)
            if ((p.columns & it->second->columns).none()) ++hits;
    }
    return {int(C.size()),int(D.size()),rc,ra,contains(sqr(target_reciprocal),all),hits};
}

std::vector<Partial> region_pair(const std::array<std::vector<PairState>,4>& lists,
                                 int first_slot,int start_a,int start_b,int width) {
    std::vector<Partial> result;
    result.reserve(width*width);
    for (int a=start_a;a<start_a+width;a++) for (int b=start_b;b<start_b+width;b++) {
        const auto& A=lists[first_slot][a]; const auto& B=lists[first_slot+1][b];
        if ((A.columns&B.columns).any()) continue;
        Point sum=add(A.point,B.point);
        if (sum.infinity || !sum.x) continue;
        u64 reciprocal=inv(sum.x);
        if (trace(reciprocal)) throw std::runtime_error("partial reciprocal trace");
        result.push_back({sum,reciprocal,A.columns|B.columns});
    }
    return result;
}

