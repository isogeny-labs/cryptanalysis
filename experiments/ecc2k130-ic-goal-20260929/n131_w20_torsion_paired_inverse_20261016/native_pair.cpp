// Fuse the two torsion-partner source-span tests in one S3 quadratic algebra.
#include "native_helpers.hpp"

struct PairQuery {
    LQuery side[2];
    uint64_t roots_recovered=0;
};

static void score(const Field&f, const LeftRow&row, Fe d, int side,
                  Fe A,Fe B,Fe E,Fe Cr,Fe Hr,
                  const std::array<Pivot,131>&pivot,
                  const std::vector<unsigned char>&valid,
                  const std::vector<int>&columns,int seedmask,PairQuery&out){
    if(zero(d))return;
    if(!satisfies(f,A,B,E,d))throw std::runtime_error("quadratic candidate");
    Fe e=side?f.inverse(d):d;
    Fe p=xo(f.mul(Cr,e),f.mul(Hr,f.inverse(e)));
    int code=recover(p,pivot);
    if(code<0)return;
    LQuery&q=out.side[side];++q.full_span;
    if(!permitted(valid,code))return;
    ++q.valid_code;
    if(!satisfies(f,Cr,p,Hr,e))throw std::runtime_error("pair source");
    int other=code^seedmask;
    if(columns[code]<0||columns[other]<0||columns[code]==columns[other])
        throw std::runtime_error("source columns");
    bool distinct=row.c0!=columns[code]&&row.c0!=columns[other]&&
                  row.c1!=columns[code]&&row.c1!=columns[other];
    q.distinct+=distinct;
    if(q.hits.size()<32)q.hits.push_back({row.x,e,row.code,code,distinct});
}

static PairQuery fused_query(const Field&f,Fe target,const std::vector<LeftRow>&left,
    Fe Cr,Fe Hr,const std::array<Fe,19>&alpha,const std::array<Pivot,131>&pivot,
    const std::vector<unsigned char>&valid,const std::vector<int>&columns,
    int seedmask,uint64_t started,uint64_t cap_ns,uint64_t rss_cap){
    PairQuery out;Fe one{1,0,0},t2=f.sq(target),partner=f.inverse(target);
    for(const auto&row:left){
        uint64_t n=out.side[0].left;
        if((n&255)==0){
            if(ticks()-started>=cap_ns){out.side[0].capped=out.side[1].capped=true;break;}
            if(rss()>rss_cap){out.side[0].oom=out.side[1].oom=true;break;}
        }
        Fe c=row.x,B=f.mul(c,target),A=xo(one,f.sq(B)),E=xo(f.sq(c),t2);
        if(zero(A)||zero(E)){
            // Direct exact fallback covers the reciprocal chart exceptions.
            ++out.side[0].exceptional;++out.side[1].exceptional;
            std::vector<LeftRow>singleton{row};
            auto qa=lquery(f,target,singleton,Cr,Hr,alpha,pivot,valid,columns,
                           seedmask,started,cap_ns,rss_cap);
            auto qb=lquery(f,partner,singleton,Cr,Hr,alpha,pivot,valid,columns,
                           seedmask,started,cap_ns,rss_cap);
            for(int side=0;side<2;++side){
                LQuery&dst=out.side[side];const LQuery&src=side?qb:qa;
                dst.gate+=src.gate;dst.full_span+=src.full_span;
                dst.valid_code+=src.valid_code;dst.distinct+=src.distinct;
                for(const Hit&h:src.hits)if(dst.hits.size()<32)dst.hits.push_back(h);
            }
        }else{
            // E*p(d) = U*d+V. For p(d)=Cr*d+Hr/d and the torsion partner
            // p(1/d)=Cr/d+Hr*d, both use the same quadratic A*d^2+B*d+E.
            Fe U[2]={xo(f.mul(Cr,E),f.mul(Hr,A)),
                     xo(f.mul(Cr,A),f.mul(Hr,E))};
            Fe V[2]={f.mul(Hr,B),f.mul(Cr,B)};
            Fe den=E;
            for(Fe a:alpha){
                Fe ad=f.mul(A,den),g=f.mul(a,ad);
                for(int side=0;side<2;++side){
                    Fe u2=f.sq(U[side]);
                    Fe nu=xo(f.mul(u2,B),f.mul(g,U[side]));
                    Fe nv=xo(xo(f.mul(u2,E),f.mul(A,f.sq(V[side]))),f.mul(g,V[side]));
                    U[side]=nu;V[side]=nv;
                }
                den=f.mul(A,f.sq(den));
            }
            for(int side=0;side<2;++side){
                std::vector<Fe> candidates;
                if(zero(U[side])){
                    if(zero(V[side])){
                        ++out.side[side].gate;
                        candidates=roots(f,A,B,E);
                    }
                }else{
                    Fe resultant=xo(xo(f.mul(A,f.sq(V[side])),
                            f.mul(B,f.mul(U[side],V[side]))),f.mul(E,f.sq(U[side])));
                    if(zero(resultant)){
                        ++out.side[side].gate;
                        candidates.push_back(f.mul(V[side],f.inverse(U[side])));
                    }
                }
                for(Fe d:candidates){
                    ++out.roots_recovered;
                    score(f,row,d,side,A,B,E,Cr,Hr,pivot,valid,columns,seedmask,out);
                }
            }
        }
        ++out.side[0].left;++out.side[1].left;
    }
    return out;
}

int main(int argc,char**argv)try{
    if(argc!=7)throw std::runtime_error("usage: native_pair charts.txt support valid result cap_seconds rss_cap_bytes");
    uint64_t started=ticks(),cap_ns=std::stoull(argv[5])*1000000000ULL;
    uint64_t rss_cap=std::stoull(argv[6]);Field f(131);Fe one{1,0,0};
    std::ifstream input(argv[1]);std::array<Fe,4>targets;
    for(int i=0;i<4;++i){std::string str;input>>str;if(!input)throw std::runtime_error("target input");
        targets[i]=standard(f,decimal(str));}
    std::string extra;if(input>>extra)throw std::runtime_error("target count");
    if(!eq(f.mul(targets[0],targets[1]),one)||
       !eq(f.mul(targets[2],targets[3]),one))throw std::runtime_error("torsion pairing");
    std::vector<int>columns(1<<20,-1);std::ifstream support(argv[2]);
    int mask,column,shift,rows=0;
    while(support>>mask>>column>>shift){
        if(mask<0||mask>=int(columns.size())||columns[mask]!=-1||shift<0||shift>=131)
            throw std::runtime_error("support row");
        columns[mask]=column;++rows;
    }
    if(!support.eof()||rows!=524493)throw std::runtime_error("support count");
    std::ifstream bits(argv[3],std::ios::binary);std::vector<unsigned char>valid(1<<16);
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
    auto first=fused_query(f,targets[0],left,Cr,Hr,alpha,pivot,valid,columns,
                           seedmask,started,cap_ns,rss_cap);
    auto second=fused_query(f,targets[2],left,Cr,Hr,alpha,pivot,valid,columns,
                            seedmask,started,cap_ns,rss_cap);
    uint64_t query_ns=ticks()-query_start;
    std::ofstream out(argv[4]);if(!out)throw std::runtime_error("result open");
    const char*status=(first.side[0].oom||second.side[0].oom)?"OOM":
        (first.side[0].capped||second.side[0].capped)?"CENSORED_TIME":
        "COMPLETE_FUSED_PAIR_QUERY";
    out<<"{\"status\":\""<<status
       <<"\",\"valid_codes\":"<<valid_codes<<",\"left_roots\":"<<left.size()
       <<",\"setup_ns\":"<<setup_ns<<",\"query_ns\":"<<query_ns
       <<",\"peak_rss_bytes\":"<<rss()<<",\"roots_recovered\":"
       <<first.roots_recovered+second.roots_recovered<<",\"queries\":[";
    for(int j=0;j<4;++j){if(j)out<<",";
        emit_l(out,j<2?first.side[j]:second.side[j-2]);}
    out<<"]}\n";
    std::cout<<status<<" "<<double(query_ns)/1e9<<" s\n";
}catch(const std::exception&e){std::cerr<<"ERROR "<<e.what()<<"\n";return 1;}
