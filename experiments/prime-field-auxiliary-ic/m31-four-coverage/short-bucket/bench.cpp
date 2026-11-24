#include <algorithm>
#include <array>
#include <arm_neon.h>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <random>
#include <unordered_set>
#include <vector>
using Key=uint32_t;
using Clock=std::chrono::steady_clock;
double ns(Clock::time_point a){return std::chrono::duration<double,std::nano>(Clock::now()-a).count();}
template<int Width,class Offset,int Mode>
void bench(const std::vector<Key>& keys,const std::vector<Key>& input,const std::vector<uint8_t>& expected,int arm,unsigned seed,int round){
    std::vector<uint8_t> out(input.size(),2);
    auto start=Clock::now();
    auto sorted=keys;
    std::sort(sorted.begin(),sorted.end());
    std::vector<Offset> offsets((1u<<Width)+1);
    unsigned i=0;
    for(unsigned b=0;b<offsets.size();++b){
        while(i<sorted.size() && (sorted[i]>>(31-Width))<b)++i;
        offsets[b]=i;
    }
    if constexpr(Mode==2)sorted.resize(sorted.size()+4,0xffffffffu);
    double build=ns(start);
    start=Clock::now();
    for(size_t j=0;j<input.size();++j){
        Key x=input[j];unsigned b=x>>(31-Width);
        auto lo=sorted.data()+offsets[b], hi=sorted.data()+offsets[b+1];
        if constexpr(Mode==0)out[j]=std::binary_search(lo,hi,x);
        if constexpr(Mode==1)out[j]=std::find(lo,hi,x)!=hi;
        if constexpr(Mode==2){
            // Following buckets have different high bits; sentinel words exceed every key.
            auto needle=vdupq_n_u32(x);
            uint32x4_t hits=vceqq_u32(vld1q_u32(lo),needle);
            while(hi-lo>4){lo+=4;hits=vorrq_u32(hits,vceqq_u32(vld1q_u32(lo),needle));}
            out[j]=vmaxvq_u32(hits)!=0;
        }
    }
    double probe=ns(start);
    if(out!=expected)std::abort();
    std::cout<<seed<<','<<round<<','<<arm<<','<<build<<','<<probe<<'\n';
}
int main(int argc,char** argv){
    unsigned first=std::stoul(argv[1]);
    int selected=argc>2?std::stoi(argv[2]):-1;
    for(unsigned seed=first;seed<first+8;++seed){
        std::mt19937 gen(seed);std::vector<Key> input(673130);
        for(auto& x:input)x=gen()>>1;
        std::unordered_set<Key> ref;std::vector<Key> keys;
        while(keys.size()<28033){Key x=gen()>>1;if(ref.insert(x).second)keys.push_back(x);}
        // Include every key once in a separate correctness replay before timing panels.
        auto check=keys;check.push_back(0);check.push_back(0x7fffffff);
        for(int i=0;i<8;++i)input[i*79031]=keys[i];
        std::vector<uint8_t> expected(input.size()),truth(check.size());
        for(size_t i=0;i<input.size();++i)expected[i]=ref.contains(input[i]);
        for(size_t i=0;i<check.size();++i)truth[i]=ref.contains(check[i]);
        for(int r=-1;r<6;++r){
            std::vector<int> order={0,1,2,3,4,5,6};
            if(selected>=0)order={0,selected};
            std::shuffle(order.begin(),order.end(),gen);
            for(int a:order){
                auto& xs=r<0?check:input;auto& ys=r<0?truth:expected;
#define ARM(ID,W,T,M) case ID: bench<W,T,M>(keys,xs,ys,a,seed,r);break
                switch(a){ARM(0,12,uint32_t,0);ARM(1,12,uint16_t,0);ARM(2,12,uint16_t,1);ARM(3,12,uint16_t,2);ARM(4,14,uint16_t,2);ARM(5,15,uint16_t,2);ARM(6,16,uint16_t,2);}
#undef ARM
            }
        }
    }
}
