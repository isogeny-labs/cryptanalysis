// Compare equal sets of public labels with misses grouped or dispersed.
#include "coordinate-cache.hpp"
#include <algorithm>
#include <chrono>
#include <fstream>
#include <iostream>
#include <numeric>
#include <random>
#include <string>

struct Panel {
    std::vector<Batch> x{1024};
    std::vector<Labels> labels{1024};
    explicit Panel(const char* file) {
        std::ifstream in(file);
        for(unsigned i=0;i<1024;++i) for(unsigned j=0;j<32;++j) {
            unsigned bit;
            if(!(in>>x[i][j]>>bit) || x[i][j]>=p || bit>1) std::abort();
            labels[i][j]=bit;
        }
    }
};

// Only misses enter the arithmetic batch. Remember where each result belongs.
void compact(const CoordinateCache& cache,const std::vector<Batch>& x,std::vector<Labels>& out) {
    Batch pending{};
    std::array<uint8_t*,32> destinations{};
    unsigned used=0;
    auto flush=[&] {
        auto result=classify<3>(pending);
        for(unsigned i=0;i<used;++i) *destinations[i]=result[i];
        used=0;
    };
    for(size_t i=0;i<x.size();++i) for(unsigned j=0;j<32;++j) {
        uint32_t key=x[i][j],word=cache.slots[cache.probe(key)];
        if(word==p) {
            pending[used]=key;
            destinations[used++]=&out[i][j];
            if(used==32) flush();
        } else out[i][j]=word>>31;
    }
    if(used) flush();
}

int main(int argc,char** argv) {
    if(argc!=4 && argc!=5) return 1;
    bool random_layout=argc==5 && std::string(argv[4])=="random";
    if(argc==5 && !random_layout) return 1;
    unsigned seed=std::stoul(argv[1]);
    Panel hot(argv[2]), unseen(argv[3]);
    std::vector<uint32_t> keys;
    for(auto panel : {&hot,&unseen})
        for(const auto& batch:panel->x) keys.insert(keys.end(),batch.begin(),batch.end());
    std::sort(keys.begin(),keys.end());
    if(std::adjacent_find(keys.begin(),keys.end())!=keys.end()) return 2;
    std::vector<unsigned> ids(32768);
    std::iota(ids.begin(),ids.end(),0);
    std::mt19937 rng(seed);
    std::shuffle(ids.begin(),ids.end(),rng);
    std::vector<Batch> inputs(1024);
    std::vector<Labels> oracle(1024),out(1024);
    std::cout<<"misses_per_32,layout,position,method,elapsed_ns\n";
    auto slots=ids;
    std::shuffle(slots.begin(),slots.end(),rng);
    for(unsigned misses : {0,1,4,8,16,32}) for(bool spread : {true,false}) {
        if(random_layout && !spread) continue;
        unsigned hit=0,miss=0;
        for(unsigned i=0;i<32768;++i) {
            bool absent=random_layout ? slots[i]<1024*misses : spread ? i%32<misses : i/32<32*misses;
            unsigned id=ids[absent?32768-1024*misses+miss++:hit++];
            auto& panel=absent?unseen:hot;
            inputs[i/32][i%32]=panel.x[id/32][id%32];
            oracle[i/32][i%32]=panel.labels[id/32][id%32];
        }
        if(miss!=1024*misses || hit+miss!=32768) return 2;
        std::array<unsigned,3> order={0,1,2};
        for(unsigned n=0;n<seed%6;++n) std::next_permutation(order.begin(),order.end());
        for(unsigned pos=0;pos<3;++pos) {
            auto method=order[pos];
            auto begin=std::chrono::steady_clock::now();
            if(method==0) {
                for(unsigned pass=0;pass<16;++pass) {
                    for(unsigned i=0;i<1024;++i) out[i]=classify<3>(inputs[i]);
                    asm volatile("" : : "r"(out.data()) : "memory");
                }
            } else {
                CoordinateCache cache(hot.x);
                for(unsigned pass=0;pass<16;++pass) {
                    if(method==1) for(unsigned i=0;i<1024;++i) out[i]=cache.lookup(inputs[i]);
                    else compact(cache,inputs,out);
                    asm volatile("" : : "r"(out.data()) : "memory");
                }
            }
            auto ns=std::chrono::duration_cast<std::chrono::nanoseconds>(
                std::chrono::steady_clock::now()-begin).count();
            if(out!=oracle) return 3;
            std::cout<<misses<<','<<(random_layout?"random":spread?"spread":"grouped")<<','<<pos<<','
                     <<std::array{"arithmetic","batch","compact"}[method]<<','<<ns<<'\n';
        }
    }
    CoordinateCache cache(hot.x);
    for(unsigned missing=1;missing<32;++missing) {
        std::vector<Batch> tail(1,hot.x[0]);
        Labels expected=hot.labels[0];
        for(unsigned j=0;j<missing;++j) {
            tail[0][j]=unseen.x[0][0];
            expected[j]=unseen.labels[0][0];
        }
        std::vector<Labels> result(1);
        compact(cache,tail,result);
        if(result[0]!=expected) return 4;
    }
}
