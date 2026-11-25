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

int main(int argc,char** argv) {
    try {
        if (argc!=3) throw std::runtime_error("usage: joint pairs.tsv result.json");
        std::ifstream input(argv[1]); if (!input) throw std::runtime_error("missing pairs table");
        std::string tag; int slots,targets; input>>tag>>slots>>targets;
        if (tag!="ECC2K41_ALLSEED4"||slots!=4||targets!=4) throw std::runtime_error("header");
        std::array<std::vector<PairState>,4> lists;
        for (auto& list:lists) list.resize(COUNT);
        std::array<std::vector<bool>,4> seen;
        for (auto& row:seen) row.resize(COUNT,false);
        std::array<Point,4> raw{};
        int state_count=0,target_count=0;
        while (input>>tag) {
            if (tag=="T") { int id;u64 x,y;input>>id>>x>>y;
                if (id<0||id>=4) throw std::runtime_error("target id");
                raw[id]={x,y,false};++target_count;
            } else if (tag=="S") {
                int slot,id,a,b,ca,cb,sa,sb;u64 x,y;
                input>>slot>>id>>a>>b>>ca>>cb>>sa>>sb>>x>>y;
                if (slot<0||slot>=4||id<0||id>=COUNT||seen[slot][id]||
                    ca<0||ca>=128||cb<0||cb>=128||ca==cb||a>=b)
                    throw std::runtime_error("state row");
                auto& state=lists[slot][id];
                state.point={x,y,false};state.columns.set(ca);state.columns.set(cb);
                seen[slot][id]=true;++state_count;
            } else throw std::runtime_error("unexpected table tag");
        }
        if (state_count!=4*COUNT||target_count!=4) throw std::runtime_error("table count");
        for (const auto& row:seen) for (bool flag:row) if (!flag) throw std::runtime_error("missing state");
        Point target=raw[1];u64 t=inv(target.x);
        if (trace(t)) throw std::runtime_error("target reciprocal trace");
        const std::array<int,4> witness={17678,155,6169,16990};
        Point check=add(add(lists[0][witness[0]].point,lists[1][witness[1]].point),
                        add(lists[2][witness[2]].point,lists[3][witness[3]].point));
        if (!(check==target)) throw std::runtime_error("public witness mismatch");
        std::ofstream output(argv[2]); if (!output) throw std::runtime_error("result path");
        output<<"{\"status\":\"COMPLETE_N41_W8_JOINT_PARTIAL_SPAN\",\"target_reciprocal\":"<<t
              <<",\"target_index\":1,\"levels\":[";
        for (int f=0;f<=5;f++) {
            int width=1<<f,groups=COUNT/width;
            std::array<int,4> positive_start{};
            for (int i=0;i<4;i++) positive_start[i]=(witness[i]/width)*width;
            auto positive_left=region_pair(lists,0,positive_start[0],positive_start[1],width);
            auto positive_right=region_pair(lists,2,positive_start[2],positive_start[3],width);
            auto positive=gate(positive_left,positive_right,t,target);
            if (!positive.span_consistent||positive.exact_hits<1)
                throw std::runtime_error("positive not retained");
            std::mt19937_64 rng(202610140100ULL+f);
            int sample=64,reject=0,cross40=0,exact_hits=0;
            std::map<int,int> rank_hist;
            for (int k=0;k<sample;k++) {
                std::array<int,4> starts{};
                for (int i=0;i<4;i++) starts[i]=int(rng()%groups)*width;
                auto left=region_pair(lists,0,starts[0],starts[1],width);
                auto right=region_pair(lists,2,starts[2],starts[3],width);
                auto value=gate(left,right,t,target);
                reject+=!value.span_consistent;cross40+=value.cross_rank==40;
                exact_hits+=value.exact_hits;rank_hist[value.left_rank+value.right_rank]++;
            }
            output<<(f?",":"")<<"{\"free_state_bits_per_slot\":"<<f
                  <<",\"states_per_slot\":"<<width<<",\"positive_starts\":["
                  <<positive_start[0]<<","<<positive_start[1]<<","<<positive_start[2]<<","<<positive_start[3]<<"]"
                  <<",\"positive_left_partials\":"<<positive_left.size()
                  <<",\"positive_right_partials\":"<<positive_right.size()
                  <<",\"positive_left_rank\":"<<positive.left_rank
                  <<",\"positive_right_rank\":"<<positive.right_rank
                  <<",\"positive_cross_rank\":"<<positive.cross_rank
                  <<",\"positive_span_consistent\":true"
                  <<",\"positive_exact_hits\":"<<positive.exact_hits
                  <<",\"sampled_regions\":"<<sample
                  <<",\"sampled_span_rejects\":"<<reject
                  <<",\"sampled_full_cross_rank\":"<<cross40
                  <<",\"sampled_exact_hits\":"<<exact_hits
                  <<",\"sampled_rank_sum_histogram\":{";
            bool first=true;
            for (auto [rank,count]:rank_hist) {
                output<<(first?"":",")<<"\""<<rank<<"\":"<<count;first=false;
            }
            output<<"}}";
        }
        output<<"]}\n";
        std::cout<<"COMPLETE_N41_W8_JOINT_PARTIAL_SPAN target_reciprocal="<<t<<"\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr<<"ERROR "<<error.what()<<"\n";return 2;
    }
}
