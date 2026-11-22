// Exact fixed-seed source census and pair-output generation on a bounded prefix.
#define main archived_inverse_main
#include "../n131_w15_native_field_20261011/native_fast_sq.cpp"
#undef main

struct SourceEntry {uint32_t code;Fe w,p;};

static Fe halftrace(const Field& field,Fe value){
    Fe sum=value,power=value;
    for(int i=1;i<=(field.n-1)/2;++i){
        power=field.sq(field.sq(power));sum=xo(sum,power);
    }
    return sum;
}

static std::vector<Fe> batch_inverse(const Field& field,const std::vector<Fe>& input){
    const Fe one{1,0,0};
    std::vector<Fe> prefix(input.size()+1),result(input.size());
    prefix[0]=one;
    for(size_t i=0;i<input.size();++i){
        if(zero(input[i]))throw std::runtime_error("zero batch inverse input");
        prefix[i+1]=field.mul(prefix[i],input[i]);
    }
    Fe tail=field.inverse(prefix.back());
    for(size_t i=input.size();i-->0;){
        result[i]=field.mul(tail,prefix[i]);
        tail=field.mul(tail,input[i]);
    }
    if(!eq(tail,one))throw std::runtime_error("batch inverse replay failed");
    return result;
}

static Fe trace_mask(const Field& field){
    Fe mask{};
    for(int i=0;i<field.n;++i){
        Fe x{};
        if(i<64)x.lo=uint64_t(1)<<i;
        else if(i<128)x.mid=uint64_t(1)<<(i-64);
        else x.hi=uint64_t(1)<<(i-128);
        Fe current=x,sum{};
        for(int j=0;j<field.n;++j){sum=xo(sum,current);current=field.sq(current);}
        if(!zero(sum)&&!eq(sum,Fe{1,0,0}))throw std::runtime_error("trace basis not binary");
        if(eq(sum,Fe{1,0,0}))mask=xo(mask,x);
    }
    return mask;
}

static int trace(Fe x,Fe mask){
    return (__builtin_parityll(x.lo&mask.lo)^
            __builtin_parityll(x.mid&mask.mid)^
            __builtin_parityll(x.hi&mask.hi));
}

int main(int argc,char**argv){
try{
    if(argc!=2)throw std::runtime_error("usage: source_prefix source_n.txt");
    std::ifstream in(argv[1]);if(!in)throw std::runtime_error("source input open failed");
    std::string tag,word;int n,d;uint32_t limit,fixture;
    in>>tag>>n>>d;
    if(tag!="SOURCE"||(n!=41&&n!=131)||d<=0||d>28)
        throw std::runtime_error("bad source header");
    in>>word;Fe seed=decimal(word);
    in>>word;Fe C=decimal(word);
    in>>word;Fe H=decimal(word);
    in>>limit>>fixture;
    if(zero(seed)||zero(C)||zero(H)||limit==0||limit>(1u<<d)||fixture>=limit)
        throw std::runtime_error("bad source parameters");
    std::vector<Fe> wb(d),pb(d);
    for(int i=0;i<d;++i){
        in>>word;if(!in)throw std::runtime_error("missing w basis");wb[i]=decimal(word);
        in>>word;if(!in)throw std::runtime_error("missing product basis");pb[i]=decimal(word);
    }
    in>>word;if(!in.eof())throw std::runtime_error("trailing source input");
    Field field(n);Fe tmask=trace_mask(field);
    Fe invC=field.inverse(C),CH=field.mul(C,H);
    std::cout<<"TRACE ";write_fe(std::cout,tmask);std::cout<<"\n";
    uint64_t start=ticks();
    uint64_t valid_count=0,output_count=0,quadratic_fail=0,batches=0,digest=0;
    bool capped=false;
    Fe current_w{},current_p{};uint32_t previous_gray=0;
    constexpr uint32_t CHUNK=4096;
    for(uint32_t begin=0;begin<limit;begin+=CHUNK){
        if(ticks()-start>120000000000ULL){capped=true;break;}
        uint32_t end=std::min<uint32_t>(limit,begin+CHUNK);
        std::vector<SourceEntry> entries;entries.reserve(end-begin);
        std::vector<Fe> terms;terms.reserve(2*(end-begin));
        for(uint32_t i=begin;i<end;++i){
            uint32_t code=i^(i>>1);
            if(i){
                uint32_t diff=code^previous_gray;
                if(__builtin_popcount(diff)!=1)throw std::runtime_error("Gray step mismatch");
                int bit=__builtin_ctz(diff);
                current_w=xo(current_w,wb[bit]);
                current_p=xo(current_p,pb[bit]);
            }
            previous_gray=code;
            Fe other=xo(current_w,seed);
            if(zero(current_w)||zero(other))continue;
            entries.push_back({code,current_w,current_p});
            terms.push_back(current_w);terms.push_back(other);
        }
        auto inverse=batch_inverse(field,terms);++batches;
        std::vector<SourceEntry> valid;
        valid.reserve(entries.size());
        for(size_t i=0;i<entries.size();++i){
            Fe w=entries[i].w,other=xo(w,seed);
            if(trace(w,tmask)||trace(other,tmask)||
               trace(inverse[2*i],tmask)||trace(inverse[2*i+1],tmask))continue;
            valid.push_back(entries[i]);
        }
        std::vector<Fe> products;products.reserve(valid.size());
        for(const auto& row:valid){
            if(zero(row.p))throw std::runtime_error("zero source product");
            products.push_back(row.p);
        }
        auto invp=batch_inverse(field,products);++batches;
        for(size_t i=0;i<valid.size();++i){
            const auto& row=valid[i];
            Fe argument=field.mul(CH,field.sq(invp[i]));
            Fe h=halftrace(field,argument);
            if(!eq(xo(field.sq(h),h),argument)){++quadratic_fail;continue;}
            Fe scale=field.mul(row.p,invC);
            Fe c0=field.mul(scale,h),c1=xo(c0,scale);
            if(zero(c0)||zero(c1))throw std::runtime_error("zero pair output");
            for(Fe c:{c0,c1})
                if(!zero(xo(xo(field.mul(C,field.sq(c)),field.mul(row.p,c)),H)))
                    throw std::runtime_error("pair quadratic replay mismatch");
            ++valid_count;output_count+=2;
            digest^=c0.lo^c0.mid^c0.hi^c1.lo^c1.mid^c1.hi^row.code;
            if(row.code<4096){
                std::cout<<"PREFIX "<<row.code<<" ";write_fe(std::cout,c0);
                std::cout<<" ";write_fe(std::cout,c1);std::cout<<"\n";
            }
            if(row.code==fixture){
                std::cout<<"FIXTURE "<<row.code<<" ";write_fe(std::cout,c0);
                std::cout<<" ";write_fe(std::cout,c1);std::cout<<"\n";
            }
        }
    }
    uint64_t elapsed=ticks()-start;
    std::cout<<"RESULT "<<(capped?"WALL_CAP":"COMPLETE")<<" "<<n<<" "<<d
             <<" "<<limit<<" "<<valid_count<<" "<<output_count<<" "
             <<quadratic_fail<<" "<<batches<<" "<<elapsed<<" "<<rss()
             <<" "<<digest<<"\n";
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}
}
