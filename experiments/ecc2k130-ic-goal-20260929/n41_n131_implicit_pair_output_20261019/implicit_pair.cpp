// Recover the unique fixed-seed source product from a proposed pair output.
#define main archived_inverse_main
#include "../n131_w15_native_field_20261011/native_fast_sq.cpp"
#undef main

#include <sstream>

struct CodeBasis {
    std::array<Fe,131> pivot{};
    std::array<uint32_t,131> code{};
    int rank=0;
    void insert(Fe value,uint32_t mask) {
        while(!zero(value)) {
            int k=highbit(value);
            if(zero(pivot[k])) {pivot[k]=value;code[k]=mask;++rank;return;}
            value=xo(value,pivot[k]);mask^=code[k];
        }
        throw std::runtime_error("product basis dependency");
    }
    bool decode(Fe value,uint32_t& mask) const {
        mask=0;
        while(!zero(value)) {
            int k=highbit(value);
            if(zero(pivot[k])) return false;
            value=xo(value,pivot[k]);mask^=code[k];
        }
        return true;
    }
};

struct SplitMix64 {
    uint64_t state;
    uint64_t next() {
        uint64_t z=(state+=0x9e3779b97f4a7c15ULL);
        z=(z^(z>>30))*0xbf58476d1ce4e5b9ULL;
        z=(z^(z>>27))*0x94d049bb133111ebULL;
        return z^(z>>31);
    }
};

int main(int argc,char**argv) {
try {
    if(argc!=2)throw std::runtime_error("usage: implicit_pair input_n.txt");
    std::ifstream in(argv[1]);
    if(!in)throw std::runtime_error("input open failed");
    std::string tag,word;
    int n,d;
    uint64_t samples,seed;
    in>>tag>>n>>d;
    if(tag!="PAIR"||(n!=41&&n!=131)||d<=0||d>32)
        throw std::runtime_error("bad input header");
    in>>word;Fe C=decimal(word);
    in>>word;Fe H=decimal(word);
    in>>samples>>seed;
    if(!in||zero(C)||zero(H)||samples>1000000)
        throw std::runtime_error("bad input parameters");
    Field field(n);
    CodeBasis basis;
    for(int i=0;i<d;++i) {
        in>>word;if(!in)throw std::runtime_error("missing basis value");
        basis.insert(decimal(word),uint32_t(1)<<i);
    }
    if(basis.rank!=d)throw std::runtime_error("basis rank mismatch");
    int positives;
    in>>tag>>positives;
    if(tag!="POS"||positives!=64)throw std::runtime_error("bad positive header");
    auto recover=[&](Fe c,Fe inverse,uint32_t& code,Fe& p) {
        p=field.mul(xo(field.mul(C,field.sq(c)),H),inverse);
        return basis.decode(p,code);
    };
    for(int i=0;i<positives;++i) {
        uint32_t expected;
        in>>word>>expected;
        if(!in)throw std::runtime_error("missing positive control");
        Fe c=decimal(word),p{};uint32_t actual=0;
        if(zero(c)||!recover(c,field.inverse(c),actual,p)||actual!=expected)
            throw std::runtime_error("positive output inversion mismatch");
        if(!zero(xo(xo(field.mul(C,field.sq(c)),field.mul(p,c)),H)))
            throw std::runtime_error("positive pair quadratic mismatch");
        std::cout<<"POS "<<i<<" "<<word<<" "<<actual<<"\n";
    }
    in>>word;
    if(!in.eof())throw std::runtime_error("trailing input");
    const uint64_t query_start=ticks();
    SplitMix64 rng{seed};
    uint64_t checked=0,hits=0,batch_inversions=0;
    uint64_t digest=0;
    constexpr size_t CHUNK=4096;
    std::vector<Fe> value(CHUNK),prefix(CHUNK+1),inverse(CHUNK);
    const Fe one{1,0,0};
    while(checked<samples) {
        if(ticks()-query_start>120000000000ULL)break;
        size_t count=std::min<uint64_t>(CHUNK,samples-checked);
        for(size_t i=0;i<count;++i) {
            Fe c{rng.next(),n==41?0:rng.next(),n==41?0:(rng.next()&7)};
            if(n==41)c.lo&=((uint64_t(1)<<41)-1);
            if(zero(c))c=one;
            value[i]=c;
        }
        prefix[0]=one;
        for(size_t i=0;i<count;++i)prefix[i+1]=field.mul(prefix[i],value[i]);
        Fe tail=field.inverse(prefix[count]);++batch_inversions;
        for(size_t i=count;i-->0;) {
            inverse[i]=field.mul(tail,prefix[i]);
            tail=field.mul(tail,value[i]);
        }
        if(!eq(tail,one))throw std::runtime_error("batch inverse mismatch");
        for(size_t i=0;i<count;++i) {
            Fe p{};uint32_t code=0;
            bool member=recover(value[i],inverse[i],code,p);
            if(member)++hits;
            digest^=p.lo^p.mid^p.hi^(member?code:0);
            if(checked+i<64) {
                std::cout<<"SAMPLE "<<(checked+i)<<" ";write_fe(std::cout,value[i]);
                std::cout<<" ";write_fe(std::cout,p);
                std::cout<<" "<<(member?int64_t(code):-1)<<"\n";
            }
        }
        checked+=count;
    }
    const uint64_t elapsed=ticks()-query_start;
    std::cout<<"RESULT "<<(checked==samples?"COMPLETE":"WALL_CAP")
             <<" "<<n<<" "<<d<<" "<<checked<<" "<<hits<<" "<<batch_inversions
             <<" "<<elapsed<<" "<<rss()<<" "<<digest<<"\n";
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}
}
