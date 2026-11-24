#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <vector>
using W=uint32_t;
constexpr W p=2147483647;
W mul(W x,W y){return uint64_t(x)*y%p;}
W add(W x,W y){W z=x+y;return z>=p?z-p:z;}
W sub(W x,W y){return x>=y?x-y:x+(p-y);}
W inv(W x){
    if(!x)std::abort();
    W acc=1;
    for(W e=p-2;e;e>>=1){if(e&1)acc=mul(acc,x);x=mul(x,x);}
    return acc;
}
struct Point{W x,y;};
Point fromSlope(Point a,Point b,W m){
    W x=sub(sub(mul(m,m),a.x),b.x);
    return {x,sub(mul(m,sub(a.x,x)),a.y)};
}
Point twice(Point a){return fromSlope(a,a,mul(add(mul(3,mul(a.x,a.x)),2),inv(add(a.y,a.y))));}
struct Request{Point a,b;unsigned next,weight;};
struct State{Point pt;unsigned next;};
using Clock=std::chrono::steady_clock;
template<unsigned Width>
std::vector<W> census(const std::array<Point,17>& basis){
    std::array<std::array<Point,5>,17> multiples{};
    std::array<std::vector<State>,4> states;
    std::vector<W> out;out.reserve(28033);
    for(unsigned i=0;i<basis.size();++i){
        auto& v=multiples[i];v[1]=basis[i];v[2]=twice(v[1]);
        v[3]=fromSlope(v[2],v[1],mul(sub(v[2].y,v[1].y),inv(sub(v[2].x,v[1].x))));
        v[4]=twice(v[2]);
        for(unsigned w=1;w<4;++w)states[w].push_back({v[w],i+1});
        out.push_back(v[4].x);
    }
    std::array<Request,Width> batch;unsigned used=0;
    auto flush=[&](){
        if(!used)return;
        std::array<W,Width> before,delta;
        W prod=1;
        for(unsigned k=0;k<used;++k){
            auto r=batch[k];before[k]=prod;delta[k]=sub(r.a.x,r.b.x);
            prod=mul(prod,delta[k]);
        }
        W reciprocal=inv(prod);
        for(unsigned k=used;k-->0;){
            auto r=batch[k];W slope=mul(sub(r.a.y,r.b.y),mul(before[k],reciprocal));
            reciprocal=mul(reciprocal,delta[k]);
            Point c=fromSlope(r.a,r.b,slope);
            if(r.weight==4)out.push_back(c.x);else states[r.weight].push_back({c,r.next});
        }
        used=0;
    };
    for(unsigned w=1;w<4;++w){
        for(auto s:states[w])for(unsigned j=s.next;j<basis.size();++j){
            for(unsigned m=1;m<=4-w;++m){
                Point b=multiples[j][m];
                for(int sign=0;sign<2;++sign){
                    batch[used++]={s.pt,b,j+1,w+m};
                    if(used==Width)flush();
                    b.y=sub(0,b.y);
                }
            }
        }
        flush();
    }
    return out;
}
int main(int argc,char**argv){
    if(argc!=3)return 1;
    std::array<Point,17> basis;
    for(auto& pt:basis)if(!(std::cin>>pt.x>>pt.y))return 2;
    int arm=std::atoi(argv[1]);
    auto start=Clock::now();
    auto xs=arm==1?census<1>(basis):arm==32?census<32>(basis):census<128>(basis);
    auto elapsed=std::chrono::duration<double,std::milli>(Clock::now()-start).count();
    std::sort(xs.begin(),xs.end());
    if(xs.size()!=28033||std::adjacent_find(xs.begin(),xs.end())!=xs.end())return 3;
    auto f=std::fopen(argv[2],"wb");if(!f)return 4;
    if(std::fwrite(xs.data(),sizeof(W),xs.size(),f)!=xs.size()||std::fclose(f))return 5;
    std::cout<<elapsed<<'\n';
}
