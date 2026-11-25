// Compare public M31 lift labels on full 32-coordinate auxiliary fibers.
#include <arm_neon.h>
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <iostream>
#include <random>
#include <vector>

#include "side-kernel.hpp"
struct Fiber { Batch x; Labels label; };

int main(int argc,char** argv) {
    if (argc!=3) return 1;
    std::vector<Fiber> rows;
    uint32_t x,b;
    while (std::cin>>x>>b) {
        Fiber f;
        for (int i=0;i<32;++i) {
            if (i && !(std::cin>>x>>b)) return 2;
            if (x>=p || b>1) return 2;
            f.x[i]=x; f.label[i]=b;
        }
        rows.push_back(f);
    }
    if (rows.size()!=1024) return 2;
    std::mt19937 rng(std::stoul(argv[1]));
    std::shuffle(rows.begin(),rows.end(),rng);
    const size_t tile=std::stoul(argv[2]);
    if (!tile || tile>rows.size()) return 4;
    std::vector<Batch> scratch(tile);
    std::vector<Labels> out(rows.size());
    std::puts("round,arm,ns_per_coordinate");
    for (int round=0;round<36;++round) for (int j=0;j<3;++j) {
        int arm=(round+(round/3%2?2-j:j))%3;
        auto start=std::chrono::steady_clock::now();
        if (arm<2) {
            auto fn=arm==0?classify<3>:classify<4>;
            for(size_t i=0;i<rows.size();++i) out[i]=fn(rows[i].x);
        } else {
            for(size_t base=0;base<rows.size();base+=tile) {
                size_t width=std::min(tile,rows.size()-base);
                for(size_t i=0;i<width;++i) for(size_t k=0;k<32;k+=2) {
                    auto x=vld1_u32(&rows[base+i].x[k]);
                    vst1_u32(&scratch[i][k],cubic_pair(x));
                }
                for(size_t i=0;i<width;++i) out[base+i]=classify<3,true>(scratch[i]);
            }
        }
        double ns=std::chrono::duration<double,std::nano>(std::chrono::steady_clock::now()-start).count();
        for(size_t i=0;i<rows.size();++i) if(out[i]!=rows[i].label) return 3;
        if(round>=6) std::printf("%d,%d,%.5f\n",round-6,arm,ns/(32*rows.size()));
    }
}
