// Recover a right W20 source product directly from an S3 root and the target.
#include "implicit_core.hpp"

struct InverseBasis {
    std::array<Fe,131> pivot{};
    std::array<uint32_t,131> label{};
    int rank=0;
    void add(Fe value,uint32_t code) {
        while(!zero(value)) {
            int k=highbit(value);
            if(zero(pivot[k])){pivot[k]=value;label[k]=code;++rank;return;}
            value=xo(value,pivot[k]);code^=label[k];
        }
        throw std::runtime_error("dependent product basis");
    }
    bool recover(Fe value,uint32_t &code) const {
        code=0;
        while(!zero(value)) {
            int k=highbit(value);
            if(zero(pivot[k]))return false;
            value=xo(value,pivot[k]);code^=label[k];
        }
        return true;
    }
};

struct AffineQuery {
    uint64_t processed=0,link_roots=0,space_hits=0,source_hits=0,distinct_hits=0;
    uint64_t exceptional_D=0,zero_root=0,invD_checks=0;
    uint64_t inverse_prep_ns=0,root_and_recovery_ns=0;
    bool capped=false,oom=false;
    std::vector<Hit> hits;
};

// Montgomery's trick: one field inversion per nonzero chunk.
static bool inverse_D_batch(const Field&f,const std::vector<Fe>&D,
                            std::vector<Fe>&out,uint64_t start,uint64_t cap_ns,
                            uint64_t rss_cap,bool &capped,bool &oom) {
    constexpr size_t CHUNK=4096;
    out.resize(D.size());
    std::vector<Fe> prefix(CHUNK);
    for(size_t base=0;base<D.size();base+=CHUNK){
        if(ticks()-start>=cap_ns){capped=true;return false;}
        if(rss()>rss_cap){oom=true;return false;}
        size_t stop=std::min(base+CHUNK,D.size()),used=0;
        Fe product{1,0,0};
        for(size_t i=base;i<stop;++i){
            if(zero(D[i]))continue;
            prefix[used++]=product;
            product=f.mul(product,D[i]);
        }
        Fe running=f.inverse(product);
        for(size_t i=stop;i-->base;){
            if(zero(D[i]))continue;
            out[i]=f.mul(running,prefix[--used]);
            running=f.mul(running,D[i]);
        }
        if(used||!eq(running,Fe{1,0,0}))throw std::runtime_error("batch inverse drift");
    }
    return true;
}

static AffineQuery query_affine(const Field&f,Fe target,const std::vector<Row>&left,
           const InverseBasis&basis,const std::vector<unsigned char>&valid,
           const std::vector<int>&columns,Fe Crot,Fe Hrot,
           uint64_t start,uint64_t cap_ns,uint64_t rss_cap) {
    AffineQuery q;Fe one{1,0,0},target2=f.sq(target);
    std::vector<Fe>D(left.size());
    for(size_t i=0;i<left.size();++i)D[i]=xo(f.sq(left[i].x),target2);
    std::vector<Fe>invD;
    uint64_t prep=ticks();
    if(!inverse_D_batch(f,D,invD,start,cap_ns,rss_cap,q.capped,q.oom)){
        q.inverse_prep_ns=ticks()-prep;return q;
    }
    q.inverse_prep_ns=ticks()-prep;
    uint64_t work=ticks();
    for(size_t i=0;i<left.size();++i){
        if((i&255)==0){
            if(ticks()-start>=cap_ns){q.capped=true;break;}
            if(rss()>rss_cap){q.oom=true;break;}
        }
        const Row&row=left[i];Fe c=row.x,B=f.mul(c,target),A=xo(one,f.sq(B));
        Fe u{},M{},N{};
        if(!zero(D[i])){
            if((i&1023)==0){
                if(!eq(f.mul(D[i],invD[i]),one))throw std::runtime_error("inverse D check");
                ++q.invD_checks;
            }
            u=f.mul(Hrot,invD[i]);
            M=xo(Crot,f.mul(u,A));N=f.mul(u,B);
        } else ++q.exceptional_D;
        for(Fe d:roots(f,A,B,D[i])){
            ++q.link_roots;
            if(!satisfies(f,A,B,D[i],d))throw std::runtime_error("S3 root drift");
            if(zero(d)){++q.zero_root;continue;}
            Fe product=zero(D[i])?xo(f.mul(Crot,d),f.mul(Hrot,f.inverse(d)))
                                  :xo(f.mul(M,d),N);
            if(!satisfies(f,Crot,product,Hrot,d))
                throw std::runtime_error("affine product identity drift");
            uint32_t code=0;
            if(!basis.recover(product,code))continue;
            ++q.space_hits;
            if(code>=(1U<<19)||!valid_code(valid,int(code)))continue;
            ++q.source_hits;
            int other=int(code)^898618;
            if(columns[code]<0||columns[other]<0||columns[code]==columns[other])
                throw std::runtime_error("valid code column drift");
            bool distinct=row.c0!=columns[code]&&row.c0!=columns[other]&&
                          row.c1!=columns[code]&&row.c1!=columns[other];
            q.distinct_hits+=distinct;
            if(q.hits.size()<32)q.hits.push_back({c,d,row.code,int(code),distinct});
        }
        ++q.processed;
    }
    q.root_and_recovery_ns=ticks()-work;
    return q;
}

static void emit_affine(std::ostream&out,const AffineQuery&q){
    out<<"{\"processed_left_roots\":"<<q.processed
       <<",\"link_roots\":"<<q.link_roots
       <<",\"space_hits\":"<<q.space_hits
       <<",\"source_hits\":"<<q.source_hits
       <<",\"distinct_column_hits\":"<<q.distinct_hits
       <<",\"exceptional_D\":"<<q.exceptional_D
       <<",\"zero_root\":"<<q.zero_root
       <<",\"invD_checks\":"<<q.invD_checks
       <<",\"inverse_prep_ns\":"<<q.inverse_prep_ns
       <<",\"root_and_recovery_ns\":"<<q.root_and_recovery_ns
       <<",\"capped\":"<<(q.capped?"true":"false")
       <<",\"oom\":"<<(q.oom?"true":"false")<<",\"hits\":[";
    for(size_t i=0;i<q.hits.size();++i){
        if(i)out<<",";const Hit&h=q.hits[i];out<<"{\"c\":";write_fe(out,h.c);
        out<<",\"d\":";write_fe(out,h.d);
        out<<",\"codes\":["<<h.code0<<","<<h.code1<<"]"
           <<",\"distinct\":"<<(h.distinct?"true":"false")<<"}";
    }
    out<<"]}";
}

int main(int argc,char**argv)try{
    if(argc!=8)throw std::runtime_error("usage: affine fixture support valid result cap_seconds rss_cap rotation");
    const uint64_t start=ticks(),cap_ns=std::stoull(argv[5])*1000000000ULL;
    const uint64_t rss_cap=std::stoull(argv[6]);
    int rotation=std::stoi(argv[7]);if(rotation!=18)throw std::runtime_error("rotation drift");
    std::ifstream fixture(argv[1]);
    std::string pos_z_text,ord_z_text,left_z_text,right_z_text;
    int expected_left_code,expected_right_code;
    fixture>>pos_z_text>>ord_z_text>>left_z_text>>right_z_text
           >>expected_left_code>>expected_right_code;
    std::string extra;
    if(!fixture||fixture>>extra)throw std::runtime_error("fixture format");
    Field f(131);Fe one{1,0,0};
    Fe positive=standard(f,decimal(pos_z_text));
    Fe ordinary=standard(f,decimal(ord_z_text));
    Fe selected_c=standard(f,decimal(left_z_text));
    Fe selected_d=frob(f,standard(f,decimal(right_z_text)),rotation);
    if(zero(positive)||zero(ordinary)||zero(selected_c)||zero(selected_d))
        throw std::runtime_error("zero fixture coordinate");
    Fe v=f.mul(selected_c,positive),A=xo(one,f.sq(v)),D=xo(f.sq(selected_c),f.sq(positive));
    if(!satisfies(f,A,v,D,selected_d))throw std::runtime_error("positive S3 drift");
    std::vector<int>columns(1<<20,-1);std::ifstream support(argv[2]);
    int mask,column,shift,support_rows=0;
    while(support>>mask>>column>>shift){
        if(mask<0||mask>=int(columns.size())||columns[mask]!=-1||shift<0||shift>=131)
            throw std::runtime_error("support row");
        columns[mask]=column;++support_rows;
    }
    if(!support.eof()||support_rows!=524493)throw std::runtime_error("support count");
    std::ifstream bitmap(argv[3],std::ios::binary);std::vector<unsigned char>valid(1<<16);
    bitmap.read(reinterpret_cast<char*>(valid.data()),valid.size());
    if(!bitmap||bitmap.get()!=EOF)throw std::runtime_error("valid bitmap format");
    const int seedmask=898618;Fe s{uint64_t(seedmask)<<1,0,0};
    Fe h=halftrace(f,s),H=f.sq(h),C=xo(one,H),invC=f.inverse(C),HC=f.mul(H,C);
    Fe Crot=frob(f,C,rotation),Hrot=frob(f,H,rotation);
    InverseBasis basis;
    std::array<Fe,19>source_basis{},raw_basis{};
    for(int j=0;j<19;++j){
        Fe w{uint64_t(1)<<(j+1),0,0};
        raw_basis[j]=f.mul(w,xo(w,s));
        source_basis[j]=frob(f,raw_basis[j],rotation);
        basis.add(source_basis[j],1U<<j);
    }
    if(basis.rank!=19)throw std::runtime_error("source rank drift");
    std::vector<Row>left;left.reserve(264090);
    int codes=0;
    for(int code=0;code<(1<<19);++code){
        if(!valid_code(valid,code))continue;
        int other=code^seedmask;
        if(columns[code]<0||columns[other]<0||columns[code]==columns[other])
            throw std::runtime_error("valid/source mismatch");
        Fe unrot{};for(int j=0;j<19;++j)if(code>>j&1)unrot=xo(unrot,raw_basis[j]);
        if(zero(unrot))throw std::runtime_error("zero valid product");
        auto rr=pair_roots(f,unrot,C,H,invC,HC);
        for(Fe c:rr)left.push_back({c,code,columns[code],columns[other]});
        ++codes;
    }
    if(codes!=132045||left.size()!=264090)throw std::runtime_error("left root count");
    bool found_left=false;
    for(const Row&row:left)if(row.code==expected_left_code&&eq(row.x,selected_c))found_left=true;
    uint32_t selected_code=0;
    Fe positive_p=xo(f.mul(Crot,selected_d),f.mul(Hrot,f.inverse(selected_d)));
    if(!found_left||!basis.recover(positive_p,selected_code)||
       int(selected_code)!=expected_right_code||!valid_code(valid,int(selected_code)))
        throw std::runtime_error("selected source absent");
    uint64_t setup_ns=ticks()-start;
    uint64_t positive_start=ticks();
    AffineQuery pos=query_affine(f,positive,left,basis,valid,columns,Crot,Hrot,start,cap_ns,rss_cap);
    uint64_t positive_ns=ticks()-positive_start;
    bool selected_found=false;
    for(const Hit&hit:pos.hits)if(eq(hit.c,selected_c)&&eq(hit.d,selected_d)&&
        hit.code0==expected_left_code&&hit.code1==expected_right_code&&hit.distinct)
        selected_found=true;
    if(!pos.capped&&!pos.oom&&!selected_found)
        throw std::runtime_error("selected positive relation missing");
    uint64_t ordinary_start=ticks();
    AffineQuery ord=query_affine(f,ordinary,left,basis,valid,columns,Crot,Hrot,start,cap_ns,rss_cap);
    uint64_t ordinary_ns=ticks()-ordinary_start;
    const char*status=ord.oom||pos.oom?"OOM":ord.capped||pos.capped?"CENSORED_TIME":"COMPLETE_AFFINE_PAIR_RECOVERY";
    std::ofstream out(argv[4]);if(!out)throw std::runtime_error("result write");
    out<<"{\"status\":\""<<status<<"\",\"valid_codes\":"<<codes
       <<",\"left_roots\":"<<left.size()<<",\"basis_rank\":"<<basis.rank
       <<",\"selected_positive_found\":"<<(selected_found?"true":"false")
       <<",\"setup_ns\":"<<setup_ns<<",\"positive_query_ns\":"<<positive_ns
       <<",\"ordinary_query_ns\":"<<ordinary_ns
       <<",\"peak_rss_bytes\":"<<rss()<<",\"positive\":";
    emit_affine(out,pos);out<<",\"ordinary\":";emit_affine(out,ord);out<<"}\n";
    if(!out)throw std::runtime_error("result write failure");
    std::cout<<status<<" codes="<<codes<<" left="<<left.size()
             <<" ordinary_hits="<<ord.distinct_hits
             <<" ordinary_s="<<double(ordinary_ns)/1e9<<"\n";
    return 0;
}catch(const std::exception&e){std::cerr<<"ERROR "<<e.what()<<"\n";return 1;}
