// Stream the complete W29 pair-output domain, then query an exact two-pair terminal.
#include "source_helpers.hpp"

#include <cstdio>
#include <cstring>

struct ProductBasis {
    std::array<Fe,131> pivot{};
    std::array<uint32_t,131> masks{};
    void insert(Fe value,uint32_t mask) {
        while(!zero(value)) {
            int k=highbit(value);
            if(zero(pivot[k])) {pivot[k]=value;masks[k]=mask;return;}
            value=xo(value,pivot[k]);mask^=masks[k];
        }
        throw std::runtime_error("dependent product basis");
    }
    bool decode(Fe value,uint32_t& mask)const {
        mask=0;
        while(!zero(value)) {
            int k=highbit(value);
            if(zero(pivot[k]))return false;
            value=xo(value,pivot[k]);mask^=masks[k];
        }
        return true;
    }
};

struct LinearHalftrace {
    std::array<Fe,131> image{};
    explicit LinearHalftrace(const Field& f) {
        for(int k=0;k<131;++k){
            Fe e{};
            if(k<64)e.lo=uint64_t(1)<<k;
            else if(k<128)e.mid=uint64_t(1)<<(k-64);
            else e.hi=uint64_t(1)<<(k-128);
            image[k]=halftrace(f,f.sq(e));
        }
    }
    Fe apply(Fe x)const {
        Fe out{};
        while(x.lo){int k=__builtin_ctzll(x.lo);out=xo(out,image[k]);x.lo&=x.lo-1;}
        while(x.mid){int k=__builtin_ctzll(x.mid);out=xo(out,image[k+64]);x.mid&=x.mid-1;}
        while(x.hi){int k=__builtin_ctzll(x.hi);out=xo(out,image[k+128]);x.hi&=x.hi-1;}
        return out;
    }
};

static void pack(Fe x,unsigned char out[17]) {
    for(int i=0;i<8;++i){out[i]=(x.lo>>(8*i))&255;out[8+i]=(x.mid>>(8*i))&255;}
    out[16]=x.hi&7;
}
static Fe unpack(const unsigned char in[17]) {
    Fe x{};
    for(int i=0;i<8;++i){x.lo|=uint64_t(in[i])<<(8*i);x.mid|=uint64_t(in[8+i])<<(8*i);}
    x.hi=in[16];return x;
}

struct SourceInput {Fe seed,C,H;uint32_t limit,fixture;std::vector<Fe> wb,pb;};
static SourceInput read_source(const char* path) {
    std::ifstream in(path);if(!in)throw std::runtime_error("source input open failed");
    std::string tag,word;int n,d;SourceInput s{};
    in>>tag>>n>>d;
    if(tag!="SOURCE"||n!=131||d!=28)throw std::runtime_error("source header mismatch");
    in>>word;s.seed=decimal(word);in>>word;s.C=decimal(word);in>>word;s.H=decimal(word);
    in>>s.limit>>s.fixture;
    if(s.limit==0||s.limit>(uint32_t(1)<<28)||s.fixture>=s.limit)throw std::runtime_error("bad source domain");
    for(int i=0;i<d;++i){in>>word;s.wb.push_back(decimal(word));in>>word;s.pb.push_back(decimal(word));}
    in>>word;if(!in.eof())throw std::runtime_error("trailing source input");
    return s;
}

static void produce(const SourceInput& s,const char* path) {
    Field f(131);Fe tmask=trace_mask(f),invC=f.inverse(s.C),CH=f.mul(s.C,s.H);
    FILE* out=std::fopen(path,"wb");if(!out)throw std::runtime_error("output open failed");
    uint64_t start=ticks(),valid=0,outputs=0,fail=0,digest=0;
    Fe w{},p{};uint32_t old=0;
    constexpr uint32_t CHUNK=4096;
    for(uint32_t begin=0;begin<s.limit;begin+=CHUNK){
        if(ticks()-start>560000000000ULL)throw std::runtime_error("PRODUCER_WALL_CAP");
        std::vector<SourceEntry> entries;entries.reserve(CHUNK);
        std::vector<Fe> terms;terms.reserve(CHUNK*2);
        for(uint32_t i=begin;i<std::min<uint32_t>(s.limit,begin+CHUNK);++i){
            uint32_t code=i^(i>>1);
            if(i){uint32_t diff=code^old;if(__builtin_popcount(diff)!=1)throw std::runtime_error("Gray step mismatch");
                int bit=__builtin_ctz(diff);w=xo(w,s.wb[bit]);p=xo(p,s.pb[bit]);}
            old=code;Fe other=xo(w,s.seed);
            if(zero(w)||zero(other))continue;
            entries.push_back({code,w,p});terms.push_back(w);terms.push_back(other);
        }
        auto inverse=batch_inverse(f,terms);
        std::vector<SourceEntry> kept;kept.reserve(entries.size());
        for(size_t i=0;i<entries.size();++i){Fe other=xo(entries[i].w,s.seed);
            if(trace(entries[i].w,tmask)||trace(other,tmask)||trace(inverse[2*i],tmask)||trace(inverse[2*i+1],tmask))continue;
            kept.push_back(entries[i]);}
        std::vector<Fe> products;products.reserve(kept.size());
        for(const auto& row:kept){if(zero(row.p))throw std::runtime_error("zero product");products.push_back(row.p);}
        auto invp=batch_inverse(f,products);
        unsigned char block[CHUNK*2*17];size_t used=0;
        for(size_t i=0;i<kept.size();++i){
            const auto& row=kept[i];Fe arg=f.mul(CH,f.sq(invp[i])),h=halftrace(f,arg);
            if(!eq(xo(f.sq(h),h),arg)){++fail;continue;}
            Fe scale=f.mul(row.p,invC),c0=f.mul(scale,h),c1=xo(c0,scale);
            if(zero(c0)||zero(c1))throw std::runtime_error("zero output");
            for(Fe c:{c0,c1})if(!zero(xo(xo(f.mul(s.C,f.sq(c)),f.mul(row.p,c)),s.H)))
                throw std::runtime_error("quadratic check failed");
            pack(c0,block+used);used+=17;pack(c1,block+used);used+=17;
            ++valid;outputs+=2;digest^=c0.lo^c0.mid^c0.hi^c1.lo^c1.mid^c1.hi^row.code;
            if(row.code==s.fixture){std::cout<<"FIXTURE "<<row.code<<" ";write_fe(std::cout,c0);
                std::cout<<" ";write_fe(std::cout,c1);std::cout<<"\n";}
        }
        if(std::fwrite(block,1,used,out)!=used)throw std::runtime_error("stream write failed");
    }
    if(std::fclose(out))throw std::runtime_error("stream close failed");
    std::cout<<"PRODUCE COMPLETE "<<valid<<" "<<outputs<<" "<<fail<<" "<<digest
             <<" "<<(ticks()-start)<<" "<<rss()<<"\n";
}

struct RightInput {Fe C,H;ProductBasis basis;};
static RightInput read_right(const char* path) {
    std::ifstream in(path);if(!in)throw std::runtime_error("right input open failed");
    std::string tag,word;int n,d;size_t count;RightInput r{};
    in>>tag>>n>>d;if(tag!="TERMINAL"||n!=131||d!=28)throw std::runtime_error("right header mismatch");
    in>>word;r.C=decimal(word);in>>word;r.H=decimal(word);in>>word;in>>count;
    for(int i=0;i<d;++i){in>>word;r.basis.insert(decimal(word),uint32_t(1)<<i);}
    if(!in)throw std::runtime_error("right basis incomplete");
    return r;
}

static void query(const SourceInput& s,const RightInput& r,Fe t,const char* path,uint64_t expected) {
    if(zero(t))throw std::runtime_error("zero target reciprocal");
    Field f(131);const Fe one{1,0,0};Fe invt=f.inverse(t);LinearHalftrace linear(f);
    ProductBasis left;for(int i=0;i<28;++i)left.insert(s.pb[i],uint32_t(1)<<i);
    FILE* in=std::fopen(path,"rb");if(!in)throw std::runtime_error("stream open failed");
    constexpr size_t CHUNK=4096;unsigned char block[CHUNK*17];
    uint64_t start=ticks(),seen=0,roots=0,trace_ok=0,exceptional=0,hits=0,digest=0;
    while(seen<expected){
        if(ticks()-start>570000000000ULL){std::cout<<"QUERY WALL_CAP "<<seen<<" "<<roots<<" "<<hits<<" "<<(ticks()-start)<<" "<<rss()<<"\n";std::fclose(in);return;}
        size_t count=std::min<uint64_t>(CHUNK,expected-seen);
        if(std::fread(block,17,count,in)!=count)throw std::runtime_error("short stream");
        std::vector<Fe> c(count),A(count),B(count),terms;terms.reserve(2*count);
        std::vector<size_t> ic(count),ia(count,~size_t(0));
        for(size_t i=0;i<count;++i){c[i]=unpack(block+17*i);if(zero(c[i]))throw std::runtime_error("zero left output");
            B[i]=f.mul(c[i],t);A[i]=xo(one,f.sq(B[i]));
            ic[i]=terms.size();terms.push_back(c[i]);
            if(!zero(A[i])){ia[i]=terms.size();terms.push_back(A[i]);}
        }
        auto inv=batch_inverse(f,terms);
        std::vector<Fe> candidates;std::vector<size_t> owner;
        candidates.reserve(2*count);owner.reserve(2*count);
        for(size_t i=0;i<count;++i){
            if(zero(A[i])){++exceptional;Fe d=f.mul(f.sq(xo(c[i],t)),f.mul(inv[ic[i]],invt));
                if(!zero(d)){candidates.push_back(d);owner.push_back(i);}continue;}
            Fe z=xo(xo(c[i],inv[ic[i]]),xo(t,invt));
            Fe q=f.sq(z),h=linear.apply(z);
            if(!eq(xo(f.sq(h),h),q))continue;
            ++trace_ok;Fe scale=f.mul(B[i],inv[ia[i]]),d0=f.mul(scale,h),d1=xo(d0,scale);
            if(!zero(d0)){candidates.push_back(d0);owner.push_back(i);}
            if(!zero(d1)){candidates.push_back(d1);owner.push_back(i);}
        }
        auto invD=batch_inverse(f,candidates);
        for(size_t j=0;j<candidates.size();++j){
            Fe d=candidates[j],p=f.mul(xo(f.mul(r.C,f.sq(d)),r.H),invD[j]);
            uint32_t rc=0;bool member=r.basis.decode(p,rc);
            Fe cd=f.mul(c[owner[j]],d),cdt=f.mul(cd,t);
            Fe s3=xo(f.sq(xo(xo(c[owner[j]],d),t)),xo(cdt,f.sq(cdt)));
            if(!zero(s3))throw std::runtime_error("S3 check failed");
            if(j<2&&seen<CHUNK){std::cout<<"SAMPLE "<<(seen+owner[j])<<" ";write_fe(std::cout,c[owner[j]]);
                std::cout<<" ";write_fe(std::cout,d);std::cout<<" "<<(member?int64_t(rc):-1)<<"\n";}
            digest^=p.lo^p.mid^p.hi^(member?rc:0);
            if(member){++hits;Fe invc=inv[ic[owner[j]]];
                Fe lp=f.mul(xo(f.mul(s.C,f.sq(c[owner[j]])),s.H),invc);uint32_t lc=0;
                if(!left.decode(lp,lc))throw std::runtime_error("left code decode failed");
                std::cout<<"HIT "<<(seen+owner[j])<<" "<<lc<<" "<<rc<<" ";
                write_fe(std::cout,c[owner[j]]);std::cout<<" ";write_fe(std::cout,d);
                std::cout<<"\n";}
        }
        seen+=count;roots+=candidates.size();
    }
    if(std::fgetc(in)!=EOF)throw std::runtime_error("trailing stream");
    std::fclose(in);
    std::cout<<"QUERY COMPLETE "<<seen<<" "<<trace_ok<<" "<<exceptional<<" "<<roots<<" "<<hits
             <<" "<<digest<<" "<<(ticks()-start)<<" "<<rss()<<"\n";
}

int main(int argc,char** argv){try{
    if(argc<4)throw std::runtime_error("usage: full_stream produce source out | query source right stream target expected");
    std::string mode=argv[1];SourceInput s=read_source(argv[2]);
    if(mode=="produce"&&argc==4)produce(s,argv[3]);
    else if(mode=="query"&&argc==7)query(s,read_right(argv[3]),decimal(argv[5]),argv[4],std::stoull(argv[6]));
    else throw std::runtime_error("bad arguments");
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
