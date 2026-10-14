// Exact low-weight Boolean quadratic-annihilator census on N41 partial sums.
#include "../n41_w8_quadratic_partial_ideal_v3_20261013/joint_core.hpp"
#include <algorithm>
#include <unordered_map>

u64 halftrace(u64 a) {
    u64 total=0;
    for(int i=0;i<21;i++) {total^=a;a=sqr(sqr(a));}
    return total;
}
std::vector<u64> roots(u64 a,u64 b,u64 c) {
    if(!a) return b ? std::vector<u64>{mul(c,inv(b))}:std::vector<u64>{};
    if(!b) {u64 x=mul(c,inv(a));for(int i=0;i<40;i++) x=sqr(x);return {x};}
    u64 scale=mul(b,inv(a));u64 rhs=mul(mul(a,c),inv(sqr(b)));
    if(trace(rhs)) return {};
    u64 first=mul(scale,halftrace(rhs));return {first,first^scale};
}
std::pair<int,int> s3_join(const std::unordered_set<u64>& left,
                           const std::unordered_set<u64>& right,u64 t) {
    int hits=0,proposals=0;
    for(u64 c:left) {
        u64 ct=mul(c,t);
        for(u64 d:roots(1^sqr(ct),ct,sqr(c)^sqr(t))) {
            proposals++;
            if(!right.count(d)) continue;
            u64 z=mul(ct,d);
            if((sqr(z)^z^sqr(c^d^t))!=0) throw std::runtime_error("S3 root replay");
            hits++;
        }
    }
    return {hits,proposals};
}

struct Signature {
    u64 lo=0,hi=0;
    bool operator==(const Signature& b) const { return lo==b.lo && hi==b.hi; }
    bool operator<(const Signature& b) const {
        return hi==b.hi ? lo<b.lo : hi<b.hi;
    }
};
Signature operator^(Signature a,Signature b) { return {a.lo^b.lo,a.hi^b.hi}; }
struct SigHash {
    size_t operator()(Signature x) const {
        return Hash{}({x.lo,x.hi,false});
    }
};
struct PairSig { Signature value; int a,b; };
struct Result {
    int values,monomials,zero_terms,minimum_support;
    int s3_root_proposals,s3_hits;
};

Result analyze(const std::vector<Partial>& partials,
               const std::vector<Partial>& other,u64 target,bool left_side) {
    std::vector<u64> values;
    for (auto& p:partials) values.push_back(p.reciprocal);
    std::sort(values.begin(),values.end());
    values.erase(std::unique(values.begin(),values.end()),values.end());
    if (values.size()>128) throw std::runtime_error("signature width exceeded");
    for (u64 value:values)
        if ((value&1)!=0 || trace(value)!=0)
            throw std::runtime_error("trace-zero coordinate assumption");
    std::vector<Signature> sig;
    auto signature=[&](auto predicate) {
        Signature s;
        for (size_t i=0;i<values.size();i++) if (predicate(values[i])) {
            if (i<64) s.lo|=1ULL<<i; else s.hi|=1ULL<<(i-64);
        }
        sig.push_back(s);
    };
    signature([](u64){return true;});
    for (int bit=1;bit<41;bit++)
        signature([bit](u64 x){return (x>>bit)&1;});
    for (int i=1;i<41;i++) for (int j=i+1;j<41;j++)
        signature([i,j](u64 x){return ((x>>i)&1)&&((x>>j)&1);});
    if (sig.size()!=821) throw std::runtime_error("monomial count");
    int minimum=5,zeros=0;
    std::unordered_map<Signature,int,SigHash> first;
    first.reserve(sig.size());
    for (int i=0;i<int(sig.size());i++) {
        if (sig[i]==Signature{}) {minimum=1;zeros++;}
        auto [it,fresh]=first.emplace(sig[i],i);
        if (!fresh) minimum=std::min(minimum,2);
    }
    std::vector<PairSig> pairs;
    pairs.reserve(sig.size()*(sig.size()-1)/2);
    for (int i=0;i<int(sig.size());i++) for (int j=i+1;j<int(sig.size());j++) {
        Signature sum=sig[i]^sig[j];
        auto hit=first.find(sum);
        if (hit!=first.end() && hit->second!=i && hit->second!=j)
            minimum=std::min(minimum,3);
        pairs.push_back({sum,i,j});
    }
    if (minimum>3) {
        std::sort(pairs.begin(),pairs.end(),[](const PairSig& a,const PairSig& b){
            return a.value<b.value;
        });
        for (size_t i=1;i<pairs.size();i++) if (pairs[i].value==pairs[i-1].value) {
            auto a=pairs[i],b=pairs[i-1];
            if (a.a!=b.a && a.a!=b.b && a.b!=b.a && a.b!=b.b) {
                minimum=4; break;
            }
        }
    }
    std::unordered_set<u64> C,D;
    for (auto& p:partials) C.insert(p.reciprocal);
    for (auto& p:other) D.insert(p.reciprocal);
    auto [hits,proposals]=left_side?s3_join(C,D,target):s3_join(D,C,target);
    return {int(values.size()),int(sig.size()),zeros,minimum,proposals,hits};
}

int main(int argc,char** argv) {
    try {
        if (argc!=3) throw std::runtime_error("usage: sparse pairs.tsv result.json");
        std::ifstream input(argv[1]); if (!input) throw std::runtime_error("pairs input");
        std::string tag;int slots,targets;input>>tag>>slots>>targets;
        if (tag!="ECC2K41_ALLSEED4"||slots!=4||targets!=4)
            throw std::runtime_error("input header");
        std::array<std::vector<PairState>,4> lists;
        for (auto& list:lists) list.resize(COUNT);
        std::array<std::vector<bool>,4> seen;
        for (auto& v:seen) v.resize(COUNT,false);
        std::array<Point,4> raw{};int states=0,target_rows=0;
        while (input>>tag) {
            if (tag=="T") {int id;u64 x,y;input>>id>>x>>y;
                if(id<0||id>=4) throw std::runtime_error("target id");
                raw[id]={x,y,false};target_rows++;
            } else if (tag=="S") {
                int slot,id,a,b,ca,cb,sa,sb;u64 x,y;
                input>>slot>>id>>a>>b>>ca>>cb>>sa>>sb>>x>>y;
                if(slot<0||slot>=4||id<0||id>=COUNT||seen[slot][id]||
                   a>=b||ca<0||cb<0||ca>=128||cb>=128||ca==cb)
                    throw std::runtime_error("state row");
                lists[slot][id].point={x,y,false};
                lists[slot][id].columns.set(ca);lists[slot][id].columns.set(cb);
                seen[slot][id]=true;states++;
            } else throw std::runtime_error("tag");
        }
        if(states!=4*COUNT||target_rows!=4) throw std::runtime_error("table size");
        for(auto& v:seen) for(bool b:v) if(!b) throw std::runtime_error("missing state");
        u64 t=inv(raw[1].x);
        if(t!=344545435656ULL) throw std::runtime_error("target reciprocal");
        std::ofstream out(argv[2]);if(!out) throw std::runtime_error("result path");
        out<<"{\"status\":\"COMPLETE_N41_SPARSE_QUADRATIC_CENSUS\",\"cases\":[";
        bool first_case=true;
        auto evaluate=[&](bool witness,int case_id,std::array<int,4> starts) {
            auto left=region_pair(lists,0,starts[0],starts[1],16);
            auto right=region_pair(lists,2,starts[2],starts[3],16);
            if(left.empty()||right.empty()) return;
            auto L=analyze(left,right,t,true),R=analyze(right,left,t,false);
            if(witness && (L.s3_hits<1||R.s3_hits<1))
                throw std::runtime_error("witness S3 missing");
            out<<(first_case?"":",")<<"{\"kind\":\""<<(witness?"witness":"sample")
               <<"\",\"case_id\":"<<case_id<<",\"starts\":["
               <<starts[0]<<","<<starts[1]<<","<<starts[2]<<","<<starts[3]<<"]"
               <<",\"left_unique\":"<<L.values<<",\"right_unique\":"<<R.values
               <<",\"left_zero_terms\":"<<L.zero_terms
               <<",\"right_zero_terms\":"<<R.zero_terms
               <<",\"left_min_support_le4\":"<<L.minimum_support
               <<",\"right_min_support_le4\":"<<R.minimum_support
               <<",\"s3_proposals\":"<<L.s3_root_proposals
               <<",\"s3_hits\":"<<L.s3_hits<<"}";
            first_case=false;
        };
        const std::array<int,4> witness={17678,155,6169,16990};
        std::array<int,4> witness_start{};
        for(int i=0;i<4;i++) witness_start[i]=(witness[i]/16)*16;
        evaluate(true,-1,witness_start);
        std::mt19937_64 rng(202610140304ULL);int groups=COUNT/16;
        for(int k=0;k<8;k++) {
            std::array<int,4> starts{};
            for(int i=0;i<4;i++) starts[i]=int(rng()%groups)*16;
            evaluate(false,k,starts);
        }
        out<<"]}\n";
        std::cout<<"COMPLETE_N41_SPARSE_QUADRATIC_CENSUS\n";
        return 0;
    } catch(const std::exception& e) {std::cerr<<"ERROR "<<e.what()<<"\n";return 2;}
}
