// Solve the right source code from the target S3 equation before extracting roots.
#include "../n131_w20_affine_product_recovery_20261017/implicit_core.hpp"
#include "affine_prefix.hpp"

struct CodeLinearBasis {
    std::array<Fe,131> row{};
    std::array<uint32_t,131> label{};
    int rank=0;
    bool add(Fe value,uint32_t code) {
        while(!zero(value)) {
            int k=highbit(value);
            if(zero(row[k])) {row[k]=value;label[k]=code;++rank;return true;}
            value=xo(value,row[k]);code^=label[k];
        }
        return false;
    }
    bool recover(Fe value,uint32_t &code) const {
        code=0;
        while(!zero(value)) {
            int k=highbit(value);
            if(zero(row[k]))return false;
            value=xo(value,row[k]);code^=label[k];
        }
        return true;
    }
};

struct LinearQuery {
    uint64_t left=0,full_span=0,source=0,distinct=0;
    uint64_t exceptional=0,rank_defect=0,root_fallback=0;
    bool capped=false,oom=false;
    std::vector<Hit> hits;
};

static LinearQuery query_linear(const Field&f,Fe target,const std::vector<Row>&left,
         const std::array<Fe,19>&basis,const std::vector<unsigned char>&valid,
         const std::vector<int>&columns,Fe C,Fe H,
         uint64_t start,uint64_t cap_ns,uint64_t rss_cap) {
    LinearQuery q;const Fe one{1,0,0},t2=f.sq(target);
    auto record=[&](const Row&row,Fe d,uint32_t code) {
        if(code>=(1U<<19)||!valid_code(valid,int(code)))return;
        ++q.source;
        int other=int(code)^898618;
        if(columns[code]<0||columns[other]<0||columns[code]==columns[other])
            throw std::runtime_error("source columns");
        bool distinct=row.c0!=columns[code]&&row.c0!=columns[other]&&
                      row.c1!=columns[code]&&row.c1!=columns[other];
        q.distinct+=distinct;
        if(q.hits.size()<32)q.hits.push_back({row.x,d,row.code,int(code),distinct});
    };
    for(const Row&row:left) {
        if((q.left&255)==0) {
            if(ticks()-start>=cap_ns){q.capped=true;break;}
            if(rss()>rss_cap){q.oom=true;break;}
        }
        Fe c=row.x,B=f.mul(c,target),A=xo(one,f.sq(B));
        Fe D=xo(f.sq(c),t2),U=xo(f.mul(C,D),f.mul(H,A)),V=f.mul(H,B);
        if(zero(D)||zero(U)) {
            ++q.exceptional;
            for(Fe d:roots(f,A,B,D)) {
                ++q.root_fallback;
                if(zero(d))continue;
                Fe p=xo(f.mul(C,d),f.mul(H,f.inverse(d)));
                InverseBasis inverse;
                for(int j=0;j<19;++j)inverse.add(basis[j],1U<<j);
                uint32_t code=0;
                if(!inverse.recover(p,code))continue;
                ++q.full_span;record(row,d,code);
            }
        } else {
            // D*p = U*d+V. Substituting d=(D*p+V)/U in
            // A*d^2+B*d+D=0 gives K*p^2+L*p=R.
            Fe K=f.mul(A,f.sq(D)),L=f.mul(B,f.mul(U,D));
            Fe R=xo(xo(f.mul(A,f.sq(V)),f.mul(B,f.mul(U,V))),
                    f.mul(D,f.sq(U)));
            CodeLinearBasis linear;
            for(int j=0;j<19;++j)
                linear.add(xo(f.mul(K,f.sq(basis[j])),f.mul(L,basis[j])),1U<<j);
            if(linear.rank<19) {
                ++q.rank_defect;
                InverseBasis inverse;
                for(int j=0;j<19;++j)inverse.add(basis[j],1U<<j);
                for(Fe d:roots(f,A,B,D)) {
                    ++q.root_fallback;
                    if(zero(d))continue;
                    Fe p=xo(f.mul(C,d),f.mul(H,f.inverse(d)));
                    uint32_t code=0;
                    if(!inverse.recover(p,code))continue;
                    ++q.full_span;record(row,d,code);
                }
            } else {
                uint32_t code=0;
                if(linear.recover(R,code)) {
                    Fe p{};
                    for(int j=0;j<19;++j)if(code>>j&1)p=xo(p,basis[j]);
                    Fe d=f.mul(xo(f.mul(D,p),V),f.inverse(U));
                    if(!satisfies(f,A,B,D,d)||zero(d)||
                       !satisfies(f,C,p,H,d))
                        throw std::runtime_error("linear candidate replay");
                    ++q.full_span;record(row,d,code);
                }
            }
        }
        ++q.left;
    }
    return q;
}

static void emit_query(std::ostream&out,const LinearQuery&q) {
    out<<"{\"left\":"<<q.left<<",\"full_span\":"<<q.full_span
       <<",\"source\":"<<q.source<<",\"distinct\":"<<q.distinct
       <<",\"exceptional\":"<<q.exceptional
       <<",\"rank_defect\":"<<q.rank_defect
       <<",\"root_fallback\":"<<q.root_fallback
       <<",\"capped\":"<<(q.capped?"true":"false")
       <<",\"oom\":"<<(q.oom?"true":"false")<<",\"hits\":[";
    for(size_t i=0;i<q.hits.size();++i) {
        if(i)out<<",";const Hit&h=q.hits[i];
        out<<"{\"c\":";write_fe(out,h.c);
        out<<",\"d\":";write_fe(out,h.d);
        out<<",\"codes\":["<<h.code0<<","<<h.code1<<"]"
           <<",\"distinct\":"<<(h.distinct?"true":"false")<<"}";
    }
    out<<"]}";
}

int main(int argc,char**argv)try {
    if(argc!=7)throw std::runtime_error("usage: code_linear fixture support valid result cap_seconds rss_cap");
    uint64_t start=ticks(),cap_ns=std::stoull(argv[5])*1000000000ULL;
    uint64_t rss_cap=std::stoull(argv[6]);
    std::ifstream fixture(argv[1]);
    std::string pzt,ozt,lzt,rzt,extra;int expected_left,expected_right;
    fixture>>pzt>>ozt>>lzt>>rzt>>expected_left>>expected_right;
    if(!fixture||fixture>>extra)throw std::runtime_error("fixture format");
    Field f(131);Fe one{1,0,0};
    Fe positive=standard(f,decimal(pzt)),ordinary=standard(f,decimal(ozt));
    Fe selected_c=standard(f,decimal(lzt));
    Fe selected_d=frob(f,standard(f,decimal(rzt)),18);
    std::vector<int>columns(1<<20,-1);std::ifstream support(argv[2]);
    int mask,column,shift,n=0;
    while(support>>mask>>column>>shift) {
        if(mask<0||mask>=int(columns.size())||columns[mask]!=-1||shift<0||shift>=131)
            throw std::runtime_error("support row");
        columns[mask]=column;++n;
    }
    if(!support.eof()||n!=524493)throw std::runtime_error("support count");
    std::ifstream bitmap(argv[3],std::ios::binary);std::vector<unsigned char>valid(1<<16);
    bitmap.read(reinterpret_cast<char*>(valid.data()),valid.size());
    if(!bitmap||bitmap.get()!=EOF)throw std::runtime_error("bitmap format");
    Fe s{uint64_t(898618)<<1,0,0},h=halftrace(f,s),H=f.sq(h),C=xo(one,H);
    Fe invC=f.inverse(C),HC=f.mul(H,C),Crot=frob(f,C,18),Hrot=frob(f,H,18);
    std::array<Fe,19>raw_basis{},right_basis{};
    InverseBasis source_inverse;
    for(int j=0;j<19;++j) {
        Fe w{uint64_t(1)<<(j+1),0,0};
        raw_basis[j]=f.mul(w,xo(w,s));right_basis[j]=frob(f,raw_basis[j],18);
        source_inverse.add(right_basis[j],1U<<j);
    }
    if(source_inverse.rank!=19)throw std::runtime_error("source rank");
    std::vector<Row>left;left.reserve(264090);int codes=0;
    for(int code=0;code<(1<<19);++code) {
        if(!valid_code(valid,code))continue;
        int other=code^898618;
        if(columns[code]<0||columns[other]<0||columns[code]==columns[other])
            throw std::runtime_error("source columns");
        Fe p{};for(int j=0;j<19;++j)if(code>>j&1)p=xo(p,raw_basis[j]);
        for(Fe c:pair_roots(f,p,C,H,invC,HC))
            left.push_back({c,code,columns[code],columns[other]});
        ++codes;
    }
    if(codes!=132045||left.size()!=264090)throw std::runtime_error("source count");
    uint64_t setup_ns=ticks()-start,pos_start=ticks();
    LinearQuery pos=query_linear(f,positive,left,right_basis,valid,columns,Crot,Hrot,start,cap_ns,rss_cap);
    uint64_t pos_ns=ticks()-pos_start,ord_start=ticks();
    LinearQuery ord=query_linear(f,ordinary,left,right_basis,valid,columns,Crot,Hrot,start,cap_ns,rss_cap);
    uint64_t ord_ns=ticks()-ord_start;
    bool witness=false;
    for(const Hit&hit:pos.hits)
        if(eq(hit.c,selected_c)&&eq(hit.d,selected_d)&&hit.code0==expected_left&&
           hit.code1==expected_right&&hit.distinct)witness=true;
    if(!pos.capped&&!pos.oom&&!witness)throw std::runtime_error("positive witness");
    const char*status=pos.oom||ord.oom?"OOM":pos.capped||ord.capped?"CENSORED_TIME":"COMPLETE_CODE_LINEAR";
    std::ofstream out(argv[4]);if(!out)throw std::runtime_error("result write");
    out<<"{\"status\":\""<<status<<"\",\"valid_codes\":"<<codes
       <<",\"left_roots\":"<<left.size()<<",\"setup_ns\":"<<setup_ns
       <<",\"positive_query_ns\":"<<pos_ns<<",\"ordinary_query_ns\":"<<ord_ns
       <<",\"peak_rss_bytes\":"<<rss()<<",\"positive\":";
    emit_query(out,pos);out<<",\"ordinary\":";emit_query(out,ord);out<<"}\n";
    if(!out)throw std::runtime_error("result write");
    std::cout<<status<<" positive="<<pos.distinct<<" ordinary="<<ord.distinct<<"\n";
    return pos.capped||ord.capped||pos.oom||ord.oom?2:0;
}catch(const std::exception&e){std::cerr<<"ERROR "<<e.what()<<"\n";return 1;}
