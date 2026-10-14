#include "../n41_w8_quadratic_partial_ideal_v3_20261013/joint_core.hpp"
#include <unordered_set>
u64 halftrace(u64 a) {
    u64 total=0;
    for (int i=0;i<21;i++) { total^=a; a=sqr(sqr(a)); }
    return total;
}

std::vector<u64> roots(u64 a,u64 b,u64 c) {
    if (!a) return b ? std::vector<u64>{mul(c,inv(b))} : std::vector<u64>{};
    if (!b) {
        u64 value=mul(c,inv(a));
        for (int i=0;i<40;i++) value=sqr(value);
        return {value};
    }
    u64 scale=mul(b,inv(a));
    u64 rhs=mul(mul(a,c),inv(sqr(b)));
    if (trace(rhs)) return {};
    u64 first=mul(scale,halftrace(rhs));
    return {first,first^scale};
}


#include <bitset>

constexpr int FEATURES = 1 + N + (N * (N - 1)) / 2;
using Lift = std::bitset<FEATURES>;
Lift lift(u64 value) {
    Lift row; row.set(0); int next=1;
    for (int i=0;i<N;i++) row[next++]=bool(value&(1ULL<<i));
    for (int i=0;i<N;i++) for (int j=i+1;j<N;j++)
        row[next++]=bool(value&(1ULL<<i))&&bool(value&(1ULL<<j));
    return row;
}
struct LiftBasis {
    std::array<Lift,FEATURES> pivots{};
    int rank=0;
    bool insert(Lift row) {
        for (int i=FEATURES-1;i>=0;i--) if (row[i]) {
            if (pivots[i].any()) row^=pivots[i];
            else {pivots[i]=row;rank++;return true;}
        }
        return false;
    }
};
int main(int argc,char** argv) {
    try {
        if (argc!=3) throw std::runtime_error("usage lift pairs.tsv output.json");
        std::ifstream input(argv[1]); if(!input) throw std::runtime_error("input");
        std::string tag;int slots,targets;input>>tag>>slots>>targets;
        if(tag!="ECC2K41_ALLSEED4"||slots!=4||targets!=4) throw std::runtime_error("header");
        std::array<std::vector<PairState>,4> lists;
        for(auto& v:lists)v.resize(COUNT);
        std::array<Point,4> raw{};int states=0;
        while(input>>tag) {
            if(tag=="T") {int id;u64 x,y;input>>id>>x>>y;raw[id]={x,y,false};}
            else if(tag=="S") {int slot,id,a,b,ca,cb,sa,sb;u64 x,y;
                input>>slot>>id>>a>>b>>ca>>cb>>sa>>sb>>x>>y;
                lists[slot][id].point={x,y,false};
                lists[slot][id].columns.set(ca);lists[slot][id].columns.set(cb);states++;}
            else throw std::runtime_error("tag");
        }
        if(states!=4*COUNT) throw std::runtime_error("states");
        const std::array<int,4> witness={17678,155,6169,16990};
        int width=16;std::array<int,4> starts{};
        for(int i=0;i<4;i++)starts[i]=(witness[i]/width)*width;
        auto left=region_pair(lists,0,starts[0],starts[1],width);
        auto right=region_pair(lists,2,starts[2],starts[3],width);
        std::unordered_set<u64> C,D;
        for(auto& p:left)C.insert(p.reciprocal);
        for(auto& p:right)D.insert(p.reciprocal);
        LiftBasis base;
        for(u64 d:D)base.insert(lift(d));
        int proposals=0,passed=0,true_members=0,false_members=0;
        u64 t=inv(raw[1].x);
        for(u64 c:C) {
            u64 ct=mul(c,t);
            for(u64 d:roots(1^sqr(ct),ct,sqr(c)^sqr(t))) {
                proposals++;
                LiftBasis query=base;
                bool in_span=!query.insert(lift(d));
                bool in_set=D.count(d);
                passed+=in_span;true_members+=in_set;
                false_members+=in_span&&!in_set;
                if(in_set&&!in_span)throw std::runtime_error("false reject");
            }
        }
        std::ofstream out(argv[2]);
        out<<"{\"status\":\"COMPLETE_QUADRATIC_LIFT_SCREEN\",\"width\":16,\"feature_dimension\":"
           <<FEATURES<<",\"left_unique\":"<<C.size()<<",\"right_unique\":"<<D.size()
           <<",\"right_lift_rank\":"<<base.rank<<",\"root_proposals\":"<<proposals
           <<",\"lift_passes\":"<<passed<<",\"set_hits\":"<<true_members
           <<",\"lift_false_positives\":"<<false_members<<"}\n";
        return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 2;}
}
