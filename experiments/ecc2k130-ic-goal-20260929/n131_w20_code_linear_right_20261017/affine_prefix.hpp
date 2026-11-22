
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

