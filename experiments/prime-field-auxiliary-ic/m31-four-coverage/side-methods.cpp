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
    if (argc!=2) return 1;
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
    std::vector<Labels> out(rows.size());
    std::puts("round,arm,ns_per_coordinate");
    for (int round=0;round<12;++round) for (int j=0;j<3;++j) {
        int arm=(round+(round/3%2?2-j:j))%3;
#ifdef M31_CUBIC_PANEL
        auto fn=arm==0?classify<2>:arm==1?classify<3>:classify<4>;
        const char* label=arm==0?"parity":arm==1?"control":"wide";
#else
        auto fn=arm==0?classify<0>:arm==1?classify<1>:classify<2>;
        const char* label=arm==0?"jacobi":arm==1?"full":"parity";
#endif
        auto start=std::chrono::steady_clock::now();
        for(size_t i=0;i<rows.size();++i) out[i]=fn(rows[i].x);
        double ns=std::chrono::duration<double,std::nano>(std::chrono::steady_clock::now()-start).count();
        for(size_t i=0;i<rows.size();++i) if(out[i]!=rows[i].label) return 3;
        if(round>=3) std::printf("%d,%s,%.4f\n",round-3,
            label,ns/(32*rows.size()));
    }
}
