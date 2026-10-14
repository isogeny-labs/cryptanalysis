// Exact quadratic one-hot eligibility for W8 two-pair partial families.
#include "joint_core.hpp"
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

struct Row {
    int f; bool positive; std::array<int,4> starts;
    int left_points,right_points,left_unique,right_unique,left_rank,right_rank;
    bool onehot,linear_pass; int s3_hits,root_proposals,exact_hits;
};

std::pair<int,int> s3_join(const std::unordered_set<u64>& left,
                           const std::unordered_set<u64>& right,u64 t) {
    int hits=0,proposals=0;
    for (u64 c:left) {
        u64 ct=mul(c,t);
        for (u64 d:roots(1^sqr(ct),ct,sqr(c)^sqr(t))) {
            ++proposals;
            if (!right.count(d)) continue;
            u64 z=mul(ct,d);
            if ((sqr(z)^z^sqr(c^d^t))!=0) throw std::runtime_error("S3 root replay");
            ++hits;
        }
    }
    return {hits,proposals};
}

Row evaluate_region(const std::array<std::vector<PairState>,4>& lists,
                    Point target,u64 t,int f,bool positive,
                    std::array<int,4> starts) {
    int width=1<<f;
    auto left=region_pair(lists,0,starts[0],starts[1],width);
    auto right=region_pair(lists,2,starts[2],starts[3],width);
    std::unordered_set<u64> C,D;
    for (const auto& p:left) C.insert(p.reciprocal);
    for (const auto& p:right) D.insert(p.reciprocal);
    std::array<u64,N> lp{},rp{};
    for (u64 c:C) insert(c,lp);
    for (u64 d:D) insert(d,rp);
    int lr=0,rr=0;
    for (u64 v:lp) lr+=v!=0;
    for (u64 v:rp) rr+=v!=0;
    auto [s3,proposals]=s3_join(C,D,t);
    auto screened=gate(left,right,t,target);
    if (positive && (s3<1||screened.exact_hits<1||!screened.span_consistent))
        throw std::runtime_error("positive witness missing");
    return {f,positive,starts,int(left.size()),int(right.size()),int(C.size()),int(D.size()),
            lr,rr,!C.empty()&&!D.empty()&&int(C.size())==lr&&int(D.size())==rr,
            screened.span_consistent,s3,proposals,screened.exact_hits};
}

int main(int argc,char** argv) {
    try {
        if (argc!=3) throw std::runtime_error("usage: census pairs.tsv result.json");
        std::ifstream input(argv[1]); if (!input) throw std::runtime_error("pairs input");
        std::string tag;int slots,targets;input>>tag>>slots>>targets;
        if (tag!="ECC2K41_ALLSEED4"||slots!=4||targets!=4) throw std::runtime_error("header");
        std::array<std::vector<PairState>,4> lists;
        for (auto& v:lists) v.resize(COUNT);
        std::array<std::vector<bool>,4> seen;
        for (auto& v:seen) v.resize(COUNT,false);
        std::array<Point,4> raw{};int states=0,target_rows=0;
        while (input>>tag) {
            if (tag=="T") {int id;u64 x,y;input>>id>>x>>y;
                if (id<0||id>=4) throw std::runtime_error("target id");
                raw[id]={x,y,false};++target_rows;
            } else if (tag=="S") {
                int slot,id,a,b,ca,cb,sa,sb;u64 x,y;
                input>>slot>>id>>a>>b>>ca>>cb>>sa>>sb>>x>>y;
                if (slot<0||slot>=4||id<0||id>=COUNT||seen[slot][id]||a>=b||
                    ca<0||cb<0||ca>=128||cb>=128||ca==cb)
                    throw std::runtime_error("state row");
                auto& value=lists[slot][id];
                value.point={x,y,false};value.columns.set(ca);value.columns.set(cb);
                seen[slot][id]=true;++states;
            } else throw std::runtime_error("table tag");
        }
        if (states!=4*COUNT||target_rows!=4) throw std::runtime_error("table size");
        for (const auto& v:seen) for (bool b:v) if (!b) throw std::runtime_error("missing state");
        Point target=raw[1];u64 t=inv(target.x);
        if (t!=344545435656ULL) throw std::runtime_error("target reciprocal");
        const std::array<int,4> witness={17678,155,6169,16990};
        std::vector<Row> rows;
        for (int f=2;f<=5;f++) {
            int width=1<<f;std::array<int,4> starts{};
            for (int i=0;i<4;i++) starts[i]=(witness[i]/width)*width;
            rows.push_back(evaluate_region(lists,target,t,f,true,starts));
        }
        for (int f=2;f<=4;f++) {
            int width=1<<f,groups=COUNT/width;
            std::mt19937_64 rng(202610140300ULL+f);
            for (int k=0;k<64;k++) {
                std::array<int,4> starts{};
                for (int i=0;i<4;i++) starts[i]=int(rng()%groups)*width;
                rows.push_back(evaluate_region(lists,target,t,f,false,starts));
            }
        }
        std::ofstream out(argv[2]);if (!out) throw std::runtime_error("result path");
        out<<"{\"status\":\"COMPLETE_W8_QUADRATIC_PARTIAL_IDEAL_CENSUS\",\"target_reciprocal\":"
           <<t<<",\"cases\":[";
        for (size_t k=0;k<rows.size();k++) {
            const auto& v=rows[k];
            out<<(k?",":"")<<"{\"free_state_bits_per_slot\":"<<v.f
               <<",\"kind\":\""<<(v.positive?"witness":"sample")<<"\""
               <<",\"starts\":["<<v.starts[0]<<","<<v.starts[1]<<","<<v.starts[2]<<","<<v.starts[3]<<"]"
               <<",\"left_partial_points\":"<<v.left_points
               <<",\"right_partial_points\":"<<v.right_points
               <<",\"left_unique_reciprocals\":"<<v.left_unique
               <<",\"right_unique_reciprocals\":"<<v.right_unique
               <<",\"left_span_rank\":"<<v.left_rank
               <<",\"right_span_rank\":"<<v.right_rank
               <<",\"exact_quadratic_one_hot_ideal\":"<<(v.onehot?"true":"false")
               <<",\"linear_span_pass\":"<<(v.linear_pass?"true":"false")
               <<",\"s3_coordinate_pairs\":"<<v.s3_hits
               <<",\"root_proposals\":"<<v.root_proposals
               <<",\"exact_group_hits\":"<<v.exact_hits<<"}";
        }
        out<<"]}\n";
        std::cout<<"COMPLETE_W8_QUADRATIC_PARTIAL_IDEAL_CENSUS cases="<<rows.size()<<"\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr<<"ERROR "<<error.what()<<"\n";return 2;
    }
}
