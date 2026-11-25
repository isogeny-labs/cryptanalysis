// Independent numeric-order count of W29 fixed-seed endpoint-valid codes.
#define main archived_inverse_main
#include "../n131_w15_native_field_20261011/native_fast_sq.cpp"
#undef main

static Fe make_trace_mask(const Field& field){
    Fe answer{};
    for(int bit_index=0;bit_index<field.n;++bit_index){
        Fe basis{};
        if(bit_index<64)basis.lo=uint64_t(1)<<bit_index;
        else if(bit_index<128)basis.mid=uint64_t(1)<<(bit_index-64);
        else basis.hi=uint64_t(1)<<(bit_index-128);
        Fe sum{},power=basis;
        for(int j=0;j<field.n;++j){sum=xo(sum,power);power=field.sq(power);}
        if(eq(sum,Fe{1,0,0}))answer=xo(answer,basis);
        else if(!zero(sum))throw std::runtime_error("bad field trace");
    }
    return answer;
}

static int trace_parity(Fe value,Fe mask){
    return __builtin_parityll(value.lo&mask.lo)^
           __builtin_parityll(value.mid&mask.mid)^
           __builtin_parityll(value.hi&mask.hi);
}

static void invert_batch(const Field& field,const std::vector<Fe>& input,
                         std::vector<Fe>& result){
    const Fe one{1,0,0};
    std::vector<Fe> prefix(input.size()+1);
    result.resize(input.size());prefix[0]=one;
    for(size_t i=0;i<input.size();++i){
        if(zero(input[i]))throw std::runtime_error("zero independent inverse input");
        prefix[i+1]=field.mul(prefix[i],input[i]);
    }
    Fe tail=field.inverse(prefix.back());
    for(size_t i=input.size();i-->0;){
        result[i]=field.mul(tail,prefix[i]);tail=field.mul(tail,input[i]);
    }
    if(!eq(tail,one))throw std::runtime_error("inverse product replay");
}

int main(int argc,char**argv){
try{
    if(argc!=2)throw std::runtime_error("usage: independent_count source_n131_full.txt");
    std::ifstream in(argv[1]);if(!in)throw std::runtime_error("input open failed");
    std::string tag,word;int n,d;uint32_t limit,fixture;
    in>>tag>>n>>d;
    if(tag!="SOURCE"||n!=131||d!=28)throw std::runtime_error("wrong source header");
    in>>word;Fe seed=decimal(word);
    in>>word;Fe C=decimal(word);
    in>>word;Fe H=decimal(word);
    in>>limit>>fixture;
    if(limit!=(1u<<28)||fixture!=22||zero(seed)||zero(C)||zero(H))
        throw std::runtime_error("wrong full-source identity");
    std::vector<Fe> wb(d);
    for(int i=0;i<d;++i){
        in>>word;if(!in)throw std::runtime_error("missing w basis");wb[i]=decimal(word);
        in>>word;if(!in)throw std::runtime_error("missing p basis");
    }
    in>>word;if(!in.eof())throw std::runtime_error("trailing source bytes");
    Field field(n);Fe tmask=make_trace_mask(field);
    const uint64_t start=ticks();
    uint64_t checked=0,valid=0,inverse_batches=0;
    constexpr uint32_t CHUNK=8192;
    std::vector<Fe> terms,inverses;
    std::vector<uint32_t> indices;
    for(uint32_t begin=0;begin<limit;begin+=CHUNK){
        if(ticks()-start>590000000000ULL)break;
        uint32_t end=std::min<uint32_t>(limit,begin+CHUNK);
        terms.clear();indices.clear();
        terms.reserve(2*(end-begin));indices.reserve(end-begin);
        for(uint32_t code=begin;code<end;++code){
            Fe w{};uint32_t bits=code;
            while(bits){int bit_index=__builtin_ctz(bits);w=xo(w,wb[bit_index]);bits&=bits-1;}
            Fe other=xo(w,seed);
            if(zero(w)||zero(other))continue;
            if(trace_parity(w,tmask)||trace_parity(other,tmask))continue;
            indices.push_back(code);
            terms.push_back(w);terms.push_back(other);
        }
        invert_batch(field,terms,inverses);++inverse_batches;
        for(size_t i=0;i<indices.size();++i){
            if(trace_parity(inverses[2*i],tmask)==0 &&
               trace_parity(inverses[2*i+1],tmask)==0)++valid;
        }
        checked=end;
    }
    uint64_t elapsed=ticks()-start;
    std::cout<<"TRACE ";write_fe(std::cout,tmask);std::cout<<"\n";
    std::cout<<"RESULT "<<(checked==limit?"COMPLETE":"WALL_CAP")
             <<" "<<checked<<" "<<valid<<" "<<inverse_batches
             <<" "<<elapsed<<" "<<rss()<<"\n";
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}
}
