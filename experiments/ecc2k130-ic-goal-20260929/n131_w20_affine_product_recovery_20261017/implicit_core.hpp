// Target-conditioned S3 query of two W20 pair-output sources, without
// constructing their Cartesian partial-sum table.
#define main archived_right_main
#include "../n131_target_derived_right_block_20261013/native_right.cpp"
#undef main
#include "../n131_w18_pair_output_tables_20261013/quadratic_base.hpp"
#include <unordered_map>

struct Row {Fe x;int code,c0,c1;};
struct Hit {Fe c,d;int code0,code1;bool distinct;};
struct Query {uint64_t left=0,link_roots=0,hash_hits=0,distinct_hits=0,checked=0;
              bool capped=false,oom=false;std::vector<Hit> hits;};

static Fe frob(const Field&f,Fe v,int n){for(int i=0;i<n;++i)v=f.sq(v);return v;}
static Fe standard(const Field&f,Fe z){return f.mul(z,f.inverse(xo(z,Fe{1,0,0})));}
static bool valid_code(const std::vector<unsigned char>&v,int code){
    return (v[code>>3]>>(code&7))&1;
}
static std::array<Fe,2> pair_roots(const Field&f,Fe p,Fe C,Fe H,Fe invC,Fe HC){
    Fe invp=f.inverse(p),delta=f.mul(p,invC);
    Fe t=f.mul(HC,f.sq(invp));
    if(trace(f,t))throw std::runtime_error("valid pair code nonsplit");
    Fe a=f.mul(delta,halftrace(f,t));
    if(!satisfies(f,C,p,H,a))throw std::runtime_error("pair root check");
    return {a,xo(a,delta)};
}
static Query query(const Field&f,Fe z,const std::vector<Row>&left,
                   const std::unordered_map<Fe,Row,FeHash,FeEq>&right,
                   uint64_t start,uint64_t cap_ns,uint64_t rss_cap){
    Query q;Fe z2=f.sq(z),one{1,0,0};
    for(const Row&row:left){
        if((q.left&255)==0){
            if(ticks()-start>=cap_ns){q.capped=true;break;}
            if(rss()>rss_cap){q.oom=true;break;}
        }
        Fe c=row.x,v=f.mul(c,z),A=xo(one,f.sq(v)),D=xo(f.sq(c),z2);
        for(Fe d:roots(f,A,v,D)){
            ++q.link_roots;
            if(!satisfies(f,A,v,D,d))throw std::runtime_error("S3 root check");
            auto it=right.find(d);
            if(it==right.end())continue;
            ++q.hash_hits;
            const Row&r=it->second;
            bool distinct=row.c0!=r.c0&&row.c0!=r.c1&&
                          row.c1!=r.c0&&row.c1!=r.c1;
            q.distinct_hits+=distinct;
            if(q.hits.size()<32)q.hits.push_back({c,d,row.code,r.code,distinct});
        }
        ++q.left;
    }
    return q;
}
static void emit_query(std::ostream&out,const Query&q){
    out<<"{\"processed_left_roots\":"<<q.left
       <<",\"link_roots\":"<<q.link_roots
       <<",\"hash_hits\":"<<q.hash_hits
       <<",\"distinct_column_hits\":"<<q.distinct_hits
       <<",\"capped\":"<<(q.capped?"true":"false")
       <<",\"oom\":"<<(q.oom?"true":"false")<<",\"hits\":[";
    for(size_t i=0;i<q.hits.size();++i){if(i)out<<",";
        const auto&h=q.hits[i];out<<"{\"c\":";write_fe(out,h.c);
        out<<",\"d\":";write_fe(out,h.d);
        out<<",\"codes\":["<<h.code0<<","<<h.code1<<"]"
           <<",\"distinct\":"<<(h.distinct?"true":"false")<<"}";
    }
    out<<"]}";
}

