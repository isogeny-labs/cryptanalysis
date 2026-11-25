// Division-free linearized product-span test in the target S3 quadratic algebra.
#define main archived_right_main
#include "../n131_target_derived_right_block_20261013/native_right.cpp"
#undef main
#include "../n131_w18_pair_output_tables_20261013/quadratic_base.hpp"

struct LeftRow {Fe x;int code,c0,c1;};
struct Pivot {Fe value;int code=0;};
struct Hit {Fe c,d;int left_code,right_code;bool distinct;};
static Fe frob(const Field&f,Fe v,int n){for(int i=0;i<n;++i)v=f.sq(v);return v;}
static Fe standard(const Field&f,Fe z){return f.mul(z,f.inverse(xo(z,Fe{1,0,0})));}
static bool permitted(const std::vector<unsigned char>&v,int c){return (v[c>>3]>>(c&7))&1;}
static std::array<Fe,2> pair_roots(const Field&f,Fe p,Fe C,Fe H,Fe invC,Fe HC){
    Fe ip=f.inverse(p),delta=f.mul(p,invC),t=f.mul(HC,f.sq(ip));
    if(trace(f,t))throw std::runtime_error("valid pair nonsplit");
    Fe a=f.mul(delta,halftrace(f,t));
    if(!satisfies(f,C,p,H,a))throw std::runtime_error("pair root failure");
    return {a,xo(a,delta)};
}
static int recover(Fe p,const std::array<Pivot,131>&pivot){
    int code=0;
    while(!zero(p)){
        int k=highbit(p);
        if(zero(pivot[k].value))return -1;
        p=xo(p,pivot[k].value);code^=pivot[k].code;
    }
    return code;
}

struct LQuery {
    uint64_t left=0,gate=0,full_span=0,valid_code=0,distinct=0,exceptional=0;
    bool capped=false,oom=false;
    std::vector<Hit> hits;
};

static std::array<Fe,19> lin_coefficients(const Field&f,const std::array<Fe,19>&basis){
    std::array<Fe,19> alpha{};
    for(int i=0;i<19;++i){
        Fe value=basis[i];
        for(int j=0;j<i;++j)value=xo(f.sq(value),f.mul(alpha[j],value));
        if(zero(value))throw std::runtime_error("linearized product basis dependent");
        alpha[i]=value;
    }
    return alpha;
}

static LQuery lquery(const Field&f,Fe target,const std::vector<LeftRow>&left,
                    Fe Cr,Fe Hr,const std::array<Fe,19>&alpha,
                    const std::array<Pivot,131>&pivot,
                    const std::vector<unsigned char>&valid,const std::vector<int>&columns,
                    int seedmask,uint64_t started,uint64_t cap_ns,uint64_t rss_cap){
    LQuery q;Fe one{1,0,0},t2=f.sq(target);
    for(const auto&row:left){
        if((q.left&255)==0){
            if(ticks()-started>=cap_ns){q.capped=true;break;}
            if(rss()>rss_cap){q.oom=true;break;}
        }
        Fe c=row.x,B=f.mul(c,target),A=xo(one,f.sq(B)),E=xo(f.sq(c),t2);
        std::vector<Fe> candidates;
        bool exceptional=zero(A)||zero(E);
        if(exceptional){
            ++q.exceptional;
            candidates=roots(f,A,B,E);
        }else{
            // In F[b]/(A*b²+B*b+E), E*p(b)=(Cr*E+Hr*A)*b+Hr*B.
            Fe U=xo(f.mul(Cr,E),f.mul(Hr,A)),V=f.mul(Hr,B),den=E;
            for(Fe a:alpha){
                Fe u2=f.sq(U),ad=f.mul(A,den),g=f.mul(a,ad);
                Fe next_u=xo(f.mul(u2,B),f.mul(g,U));
                Fe next_v=xo(xo(f.mul(u2,E),f.mul(A,f.sq(V))),f.mul(g,V));
                den=f.mul(A,f.sq(den));
                U=next_u;V=next_v;
            }
            if(zero(U)){
                if(zero(V)){++q.gate;candidates=roots(f,A,B,E);}
            }else{
                Fe resultant=xo(xo(f.mul(A,f.sq(V)),f.mul(B,f.mul(U,V))),
                                f.mul(E,f.sq(U)));
                if(zero(resultant)){
                    ++q.gate;
                    Fe d=f.mul(V,f.inverse(U));
                    if(!satisfies(f,A,B,E,d))throw std::runtime_error("resultant root check");
                    candidates.push_back(d);
                }
            }
        }
        for(Fe d:candidates){
            if(zero(d))continue;
            if(!satisfies(f,A,B,E,d))throw std::runtime_error("S3 candidate failure");
            Fe p=xo(f.mul(Cr,d),f.mul(Hr,f.inverse(d)));
            int code=recover(p,pivot);
            if(code<0){
                if(!exceptional)throw std::runtime_error("gate returned non-span root");
                continue;
            }
            if(exceptional)++q.gate;
            ++q.full_span;
            if(!permitted(valid,code))continue;
            ++q.valid_code;
            if(!satisfies(f,Cr,p,Hr,d))throw std::runtime_error("pair equation");
            int other=code^seedmask;
            if(columns[code]<0||columns[other]<0||columns[code]==columns[other])
                throw std::runtime_error("valid code source mismatch");
            bool disjoint=row.c0!=columns[code]&&row.c0!=columns[other]&&
                          row.c1!=columns[code]&&row.c1!=columns[other];
            q.distinct+=disjoint;
            if(q.hits.size()<32)q.hits.push_back({c,d,row.code,code,disjoint});
        }
        ++q.left;
    }
    return q;
}

static void emit_l(std::ostream&out,const LQuery&q){
    out<<"{\"left\":"<<q.left<<",\"gate_hits\":"<<q.gate
       <<",\"full_span_hits\":"<<q.full_span<<",\"valid_code_hits\":"<<q.valid_code
       <<",\"distinct_column_hits\":"<<q.distinct
       <<",\"exceptional_quadratics\":"<<q.exceptional
       <<",\"capped\":"<<(q.capped?"true":"false")
       <<",\"oom\":"<<(q.oom?"true":"false")<<",\"hits\":[";
    for(size_t i=0;i<q.hits.size();++i){
        if(i)out<<",";const auto&h=q.hits[i];out<<"{\"c\":";write_fe(out,h.c);
        out<<",\"d\":";write_fe(out,h.d);
        out<<",\"codes\":["<<h.left_code<<","<<h.right_code<<"]"
           <<",\"distinct\":"<<(h.distinct?"true":"false")<<"}";
    }
    out<<"]}";
}

