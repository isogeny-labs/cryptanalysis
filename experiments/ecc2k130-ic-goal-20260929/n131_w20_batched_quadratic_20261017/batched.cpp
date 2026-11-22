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

struct BatchRow {Fe A,B,E,invA,invE;bool exceptional=false;};

// One Montgomery batch inversion normalizes all nonexceptional quadratics.
// For p(b)=u*b+v and A*b²+B*b+E=0, the linearized update is
// u'=(B/A)*u²+alpha*u, v'=(E/A)*u²+v²+alpha*v.
static LQuery lquery_batched(const Field&f,Fe target,const std::vector<LeftRow>&left,
                    Fe Cr,Fe Hr,const std::array<Fe,19>&alpha,
                    const std::array<Pivot,131>&pivot,
                    const std::vector<unsigned char>&valid,const std::vector<int>&columns,
                    int seedmask,uint64_t started,uint64_t cap_ns,uint64_t rss_cap){
    LQuery q;Fe one{1,0,0},t2=f.sq(target);
    std::vector<BatchRow> batch(left.size());
    std::vector<Fe> denominators;denominators.reserve(2*left.size());
    for(size_t i=0;i<left.size();++i){
        Fe c=left[i].x,B=f.mul(c,target),A=xo(one,f.sq(B)),E=xo(f.sq(c),t2);
        bool exceptional=zero(A)||zero(E);
        batch[i]={A,B,E,Fe{},Fe{},exceptional};
        if(!exceptional){denominators.push_back(A);denominators.push_back(E);}
    }
    std::vector<Fe> prefix(denominators.size()+1);
    prefix[0]=one;
    for(size_t i=0;i<denominators.size();++i)
        prefix[i+1]=f.mul(prefix[i],denominators[i]);
    std::vector<Fe> inverse(denominators.size());
    if(!denominators.empty()){
        Fe inverse_all=f.inverse(prefix.back());
        for(size_t i=denominators.size();i-->0;){
            inverse[i]=f.mul(inverse_all,prefix[i]);
            inverse_all=f.mul(inverse_all,denominators[i]);
        }
        if(!eq(inverse_all,one))throw std::runtime_error("batch inverse product check");
    }
    size_t offset=0;
    for(auto&entry:batch)if(!entry.exceptional){
        entry.invA=inverse[offset++];entry.invE=inverse[offset++];
    }
    if(offset!=denominators.size())throw std::runtime_error("batch inverse layout");
    for(size_t i=0;i<left.size();++i){
        if((q.left&255)==0){
            if(ticks()-started>=cap_ns){q.capped=true;break;}
            if(rss()>rss_cap){q.oom=true;break;}
        }
        const auto&row=left[i];const auto&entry=batch[i];
        Fe A=entry.A,B=entry.B,E=entry.E;
        std::vector<Fe> candidates;
        if(entry.exceptional){
            ++q.exceptional;
            candidates=roots(f,A,B,E);
        }else{
            Fe bovera=f.mul(B,entry.invA),eovera=f.mul(E,entry.invA);
            Fe u=xo(Cr,f.mul(Hr,f.mul(A,entry.invE)));
            Fe v=f.mul(Hr,f.mul(B,entry.invE));
            for(Fe a:alpha){
                Fe u2=f.sq(u),v2=f.sq(v);
                Fe next_u=xo(f.mul(bovera,u2),f.mul(a,u));
                Fe next_v=xo(xo(f.mul(eovera,u2),v2),f.mul(a,v));
                u=next_u;v=next_v;
            }
            if(zero(u)){
                if(zero(v)){++q.gate;candidates=roots(f,A,B,E);}
            }else{
                Fe resultant=xo(xo(f.mul(A,f.sq(v)),f.mul(B,f.mul(u,v))),
                                f.mul(E,f.sq(u)));
                if(zero(resultant)){
                    ++q.gate;
                    Fe d=f.mul(v,f.inverse(u));
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
                if(!entry.exceptional)throw std::runtime_error("gate returned non-span root");
                continue;
            }
            if(entry.exceptional)++q.gate;
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
            if(q.hits.size()<32)q.hits.push_back({row.x,d,row.code,code,disjoint});
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

int main(int argc,char**argv)try{
    if(argc!=8)throw std::runtime_error("usage: linearized positive|ordinary fixture support valid result cap_seconds rss_cap_bytes");
    std::string mode=argv[1];if(mode!="positive"&&mode!="ordinary")throw std::runtime_error("mode");
    uint64_t started=ticks(),cap_ns=std::stoull(argv[6])*1000000000ULL,rss_cap=std::stoull(argv[7]);
    std::ifstream in(argv[2]);std::string pos_t,ord_t,c_t,d_t,extra;
    int selected0,selected1;in>>pos_t>>ord_t>>c_t>>d_t>>selected0>>selected1;
    if(!in||in>>extra)throw std::runtime_error("fixture format");
    Field f(131);Fe one{1,0,0};
    Fe positive=standard(f,decimal(pos_t)),ordinary=standard(f,decimal(ord_t));
    Fe selected_c=standard(f,decimal(c_t)),selected_d=frob(f,standard(f,decimal(d_t)),18);
    Fe target=mode=="positive"?positive:ordinary;
    std::vector<int>columns(1<<20,-1);std::ifstream support(argv[3]);
    int mask,column,shift,rows=0;
    while(support>>mask>>column>>shift){
        if(mask<0||mask>=int(columns.size())||columns[mask]!=-1||shift<0||shift>=131)
            throw std::runtime_error("support row");
        columns[mask]=column;++rows;
    }
    if(!support.eof()||rows!=524493)throw std::runtime_error("support count");
    std::ifstream bits(argv[4],std::ios::binary);std::vector<unsigned char>valid(1<<16);
    bits.read(reinterpret_cast<char*>(valid.data()),valid.size());
    if(!bits||bits.get()!=EOF)throw std::runtime_error("bitmap format");
    int seedmask=898618;Fe s{uint64_t(seedmask)<<1,0,0};
    Fe h=halftrace(f,s),H=f.sq(h),C=xo(one,H),invC=f.inverse(C),HC=f.mul(H,C);
    Fe Cr=frob(f,C,18),Hr=frob(f,H,18);
    std::array<Fe,19>basis{},basis_rot{};std::array<Pivot,131>pivot{};
    for(int j=0;j<19;++j){
        Fe w{uint64_t(1)<<(j+1),0,0};basis[j]=f.mul(w,xo(w,s));
        basis_rot[j]=frob(f,basis[j],18);
        Fe value=basis_rot[j];int code=1<<j;
        while(!zero(value)){
            int k=highbit(value);
            if(zero(pivot[k].value)){pivot[k]={value,code};break;}
            value=xo(value,pivot[k].value);code^=pivot[k].code;
        }
        if(zero(value))throw std::runtime_error("product basis dependent");
    }
    auto alpha=lin_coefficients(f,basis_rot);
    std::vector<LeftRow>left;left.reserve(264090);int valid_codes=0;
    for(int code=0;code<(1<<19);++code){
        if(!permitted(valid,code))continue;
        int other=code^seedmask;
        if(columns[code]<0||columns[other]<0||columns[code]==columns[other])
            throw std::runtime_error("bitmap/source mismatch");
        Fe p{};for(int j=0;j<19;++j)if(code>>j&1)p=xo(p,basis[j]);
        for(Fe c:pair_roots(f,p,C,H,invC,HC))left.push_back({c,code,columns[code],columns[other]});
        ++valid_codes;
    }
    if(valid_codes!=132045||left.size()!=264090)throw std::runtime_error("left count");
    uint64_t setup_ns=ticks()-started,query_start=ticks();
    LQuery q=lquery_batched(f,target,left,Cr,Hr,alpha,pivot,valid,columns,seedmask,started,cap_ns,rss_cap);
    uint64_t query_ns=ticks()-query_start;
    bool selected_found=false;
    if(mode=="positive")for(const auto&hit:q.hits)
        if(eq(hit.c,selected_c)&&eq(hit.d,selected_d)&&hit.left_code==selected0&&
           hit.right_code==selected1&&hit.distinct)selected_found=true;
    if(mode=="positive"&&!q.capped&&!q.oom&&!selected_found)
        throw std::runtime_error("selected positive absent");
    const char*status=q.oom?"OOM":q.capped?"CENSORED_TIME":"COMPLETE_BATCHED_QUADRATIC_QUERY";
    std::ofstream out(argv[5]);if(!out)throw std::runtime_error("result open");
    out<<"{\"status\":\""<<status<<"\",\"mode\":\""<<mode
       <<"\",\"valid_codes\":"<<valid_codes<<",\"left_roots\":"<<left.size()
       <<",\"selected_positive_found\":"<<(selected_found?"true":"false")
       <<",\"setup_ns\":"<<setup_ns<<",\"query_ns\":"<<query_ns
       <<",\"peak_rss_bytes\":"<<rss()<<",\"query\":";
    emit_l(out,q);out<<"}\n";
    std::cout<<status<<" mode="<<mode<<" left="<<q.left<<" gate="<<q.gate
             <<" valid="<<q.valid_code<<" query_s="<<double(query_ns)/1e9<<"\n";
}catch(const std::exception&e){std::cerr<<"ERROR "<<e.what()<<"\n";return 1;}
