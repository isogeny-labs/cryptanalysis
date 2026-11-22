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

