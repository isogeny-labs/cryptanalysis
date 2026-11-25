#import <dispatch/dispatch.h>
constexpr size_t numFactors=sizeof(factors)/sizeof(factors[0]);
using Offsets=std::array<size_t,numFactors+1>;

// Split the primes in two. A new product has largest prime q precisely
// when its component on q's side is new and the other component already exists.
Offsets countOffsets() {
    std::vector<Word> sides[2]={{1},{1}};
    Offsets offsets{1};
    for (size_t i=0;i<numFactors;++i) {
        Word q=factors[i];
        auto& same=sides[i%2];
        const auto& other=sides[1-i%2];
        std::vector<Word> extra;
        size_t count=0;
        for (Word x:same) {
            if (uint64_t(x)*q>=prime) break;
            for (uint64_t y=uint64_t(x)*q;y<prime;y*=q) {
                extra.push_back(Word(y));
                count+=std::upper_bound(other.begin(),other.end(),Word((prime-1)/y))-other.begin();
            }
        }
        offsets[i+1]=offsets[i]+count;
        std::sort(extra.begin(),extra.end());
        size_t old=same.size();
        same.insert(same.end(),extra.begin(),extra.end());
        std::inplace_merge(same.begin(),same.begin()+old,same.end());
    }
    return offsets;
}

struct SupportWalk {
    Word *out,*end;
    std::array<Word,numFactors> support;

    void emit(Word v) {
        if (out==end) std::abort();
        *out++=v;
    }
    // base already contains one copy of every selected prime. Additional
    // exponents vary in ascending prime order, largest prime varying fastest.
    void exponents(uint64_t base,size_t depth) {
        Word q=support[depth-1];
        if (base*q>=prime) {emit(Word(base)); return;}
        if (depth==1) {
            for (uint64_t y=base;y<prime;y*=q) emit(Word(y));
            return;
        }
        for (uint64_t y=base;y<prime;y*=q) exponents(y,depth-1);
    }
    void groups(Word base,size_t smallest,size_t depth) {
        exponents(base,depth);
        for (size_t j=0;j<smallest;++j) {
            uint64_t v=uint64_t(base)*factors[j];
            if (v>=prime) break;
            support[depth]=factors[j];
            groups(Word(v),j,depth+1);
        }
    }
    void largest(size_t i) {
        support[0]=factors[i];
        groups(factors[i],i,1);
    }
};

void fillSupport(int arm,Word* dst,const Offsets& cache) {
    if (!arm) {emitCoordinates<true,true>(dst);return;}
    dst[0]=1;
    if (arm==1) {
        SupportWalk walk{dst+1,dst+capacity,{}};
        for (size_t i=0;i<numFactors;++i) walk.largest(i);
        if (walk.out!=walk.end) std::abort();
        return;
    }
    Offsets offsets=arm==2 ? countOffsets() : cache;
    if (offsets.back()!=capacity) std::abort();
    dispatch_apply(4,dispatch_get_global_queue(QOS_CLASS_USER_INITIATED,0),^(size_t worker){
        for (size_t i=worker;i<numFactors;i+=4) {
            SupportWalk walk{dst+offsets[i],dst+offsets[i+1],{}};
            walk.largest(i);
            if (walk.out!=walk.end) std::abort();
        }
    });
}

int main(int argc,char** argv) {
    if (argc!=2) return 1;
    int run=std::atoi(argv[1]);
    @autoreleasepool {
        const Offsets cache=countOffsets();
        auto ref=generate<true>();
        std::vector<Word> check(capacity);
        for (int arm=0;arm<4;++arm) {
            fillSupport(arm,check.data(),cache);
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
            fillSupport(arm,data,cache);
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
