// Four contiguous largest-prime ranges. Their output counts are discovered
// from generation itself. Only the first range writes directly to the result.
void gatherSupport(Word* dst) {
    static constexpr Word bounds[]={47,67,79,89};
    struct Piece { Word* base; size_t used; };
    Piece pieces[4]{};
    pieces[0].base=dst;
    for (size_t i=1;i<4;++i) {
        pieces[i].base=static_cast<Word*>(std::malloc(capacity*sizeof(Word)));
        if (!pieces[i].base) std::abort();
    }
    auto *storage=pieces;
    dispatch_apply(4,dispatch_get_global_queue(QOS_CLASS_USER_INITIATED,0),^(size_t w){
        Word* begin=storage[w].base;
        SupportWalk walk{begin,begin+capacity,{}};
        if (w==0) walk.emit(1);
        for (size_t i=0;i<numFactors;++i) {
            if (factors[i]>bounds[w]) break;
            if (w==0 || factors[i]>bounds[w-1]) walk.largest(i);
        }
        storage[w].used=walk.out-begin;
    });
    size_t pos=pieces[0].used;
    for (size_t i=1;i<4;++i) {
        if (pieces[i].used>capacity-pos) std::abort();
        std::memcpy(dst+pos,pieces[i].base,pieces[i].used*sizeof(Word));
        pos+=pieces[i].used;
        std::free(pieces[i].base);
    }
    if (pos!=capacity) std::abort();
}

int main(int argc,char** argv) {
    if (argc!=2) return 1;
    int run=std::atoi(argv[1]);
    @autoreleasepool {
        auto fill=[](int arm,Word* dst){ if (arm<2) emitCoordinates<true,true>(dst); else gatherSupport(dst); };
        auto ref=generate<true>();
        std::vector<Word> check(capacity);
        for (int arm=0;arm<4;++arm) {
            fill(arm,check.data());
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
            fill(arm,data);
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
