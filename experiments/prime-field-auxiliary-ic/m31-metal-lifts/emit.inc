#include <ctime>

void compactParents(std::vector<Word>& live, Word limit) {
    size_t n=0, i=0;
    for (;i+4<=live.size();i+=4) {
        Vec v=vld1q_u32(live.data()+i);
        if (vmaxvq_u32(v)<=limit) {
            if (n!=i) vst1q_u32(live.data()+n,v);
            n+=4;
        } else {
            for (size_t j=i;j<i+4;++j) {
                Word x=live[j];
                live[n]=x;
                n+=x<=limit;
            }
        }
    }
    for (;i<live.size();++i) {
        Word x=live[i];
        live[n]=x;
        n+=x<=limit;
    }
    live.resize(n);
}

template<bool compact,bool batch> void emitCoordinates(Word* dst) {
    std::vector<Word> live{1};
    size_t n=0;
    auto emit=[&](Word x){if (n>=capacity) std::abort(); dst[n++]=x;};
    emit(1);
    for (Word q:factors) {
        Word limit=(prime-1)/q;
        if constexpr (compact) compactParents(live,limit);
        else live.erase(std::remove_if(live.begin(),live.end(),[=](Word x){return x>limit;}),live.end());
        const size_t stop=live.size();
        Word threshold=limit/q;
        size_t i=0;
        while (i<stop) {
            if constexpr (batch) {
                if (stop-i>=4) {
                    Vec parents=vld1q_u32(live.data()+i);
                    if (vminvq_u32(parents)>threshold) {
                        if (capacity-n<4) std::abort();
                        vst1q_u32(dst+n,vmulq_n_u32(parents,q));
                        n+=4;
                        i+=4;
                        continue;
                    }
                }
            }
            for (uint64_t y=uint64_t(live[i++])*q;y<prime;y*=q) {
                emit(Word(y));
                if (y<=limit) live.push_back(Word(y));
            }
        }
    }
    if (n!=capacity) std::abort();
}

void generateArm(int arm,Word* dst) {
    if (arm==0) {
        size_t n=0;
        smoothTo([&](Word x){if (n>=capacity) std::abort(); dst[n++]=x;});
        if (n!=capacity) std::abort();
    } else if (arm==1) emitCoordinates<true,false>(dst);
    else if (arm==2) emitCoordinates<false,true>(dst);
    else emitCoordinates<true,true>(dst);
}
int main(int argc,char** argv) {
    if (argc!=2) return 1;
    int run=std::atoi(argv[1]);
    @autoreleasepool {
        auto ref=generate<true>();
        std::vector<Word> check(capacity);
        for (int arm=0;arm<4;++arm) {
            generateArm(arm,check.data());
            if (check!=ref) return 2;
        }
        inplaceLabels(ref);
        MetalLabels gpu{};
        gpu.setup();
        const int seq[]={0,1,3,2};
        std::puts("run,round,position,arm,gen_cpu_ms,gen_wall_ms,device_ms,total_cpu_ms,total_wall_ms");
        for (int r=-1;r<16;++r) for (int j=0;j<4;++j) @autoreleasepool {
            int arm=(seq[j]+r+run+4)%4;
            auto start=Clock::now();
            auto cpu=std::clock();
            id<MTLBuffer> __attribute__((objc_precise_lifetime)) buf=[gpu.device newBufferWithLength:capacity*sizeof(Word) options:MTLResourceStorageModeShared];
            if (!buf) return 3;
            auto data=static_cast<Word*>(buf.contents);
            generateArm(arm,data);
            double gen=elapsed(start);
            auto gcpu=std::clock()-cpu;
            double device=gpu.dispatch(buf,capacity);
            auto count=std::accumulate(data,data+capacity,0u);
            auto totalCpu=std::clock()-cpu;
            double wall=elapsed(start);
            if (count!=1924024 || !std::equal(ref.begin(),ref.end(),data)) return 4;
            std::printf("%d,%d,%d,%d,%.6f,%.6f,%.6f,%.6f,%.6f\n",run,r,j,arm,
                1000.0*gcpu/CLOCKS_PER_SEC,gen,device,1000.0*totalCpu/CLOCKS_PER_SEC,wall);
        }
    }
}
