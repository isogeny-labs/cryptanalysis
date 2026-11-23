// The bound-89 capacity is known from the previous complete census.
constexpr size_t capacity=3846525;

template<class Emit> void smoothTo(Emit emit) {
    std::vector<Word> live{1};
    emit(1);
    for (Word q:factors) {
        Word limit=(prime-1)/q;
        live.erase(std::remove_if(live.begin(),live.end(),[&](Word x){return x>limit;}),live.end());
        auto n=live.size();
        for (size_t i=0;i<n;++i) {
            for (uint64_t y=uint64_t(live[i])*q;y<prime;y*=q) {
                emit(Word(y));
                if (y<=limit) live.push_back(Word(y));
            }
        }
    }
}
int main(int argc,char** argv) {
    if (argc!=2) return 1;
    int run=std::atoi(argv[1]);
    @autoreleasepool {
        auto coords=generate<true>();
        size_t index=0;
        smoothTo([&](Word x){if (index>=coords.size() || coords[index++]!=x) std::abort();});
        if (index!=capacity || coords.size()!=capacity) return 2;
        inplaceLabels(coords);
        MetalLabels gpu{};
        gpu.setup();
        const int seq[]={0,1,3,2};
        std::puts("run,round,position,arm,gen_ms,label_ms,device_ms,count_ms,total_ms");
        for (int r=-1;r<12;++r) for (int j=0;j<4;++j) @autoreleasepool {
            int arm=(seq[j]+r+run+4)%4;
            std::vector<Word> owned;
            id<MTLBuffer> shared=nil;
            auto start=Clock::now();
            if (arm==0) owned=generate<true>();
            else if (arm==1) {
                owned.reserve(capacity);
                smoothTo([&](Word x){owned.push_back(x);});
            } else {
                shared=[gpu.device newBufferWithLength:capacity*sizeof(Word) options:MTLResourceStorageModeShared];
                if (!shared) return 3;
                Word* dst=static_cast<Word*>(shared.contents);
                size_t n=0;
                smoothTo([&](Word x){if (n==capacity) std::abort(); dst[n++]=x;});
                if (n!=capacity) return 4;
            }
            double gen=elapsed(start);
            auto labelStart=Clock::now();
            double device;
            const Word* out=nullptr;
            if (arm<2) {
                if (owned.size()!=capacity) return 5;
                device=gpu.apply(owned);
                out=owned.data();
            } else {
                device=gpu.dispatch(shared,capacity);
                out=static_cast<const Word*>(shared.contents);
                if (arm==3) {
                    owned.assign(out,out+capacity);
                    out=owned.data();
                }
            }
            double label=elapsed(labelStart);
            auto countStart=Clock::now();
            auto count=std::accumulate(out,out+capacity,0u);
            double countMs=elapsed(countStart);
            double total=elapsed(start);
            if (count!=1924024 || !std::equal(coords.begin(),coords.end(),out)) return 6;
            std::printf("%d,%d,%d,%d,%.6f,%.6f,%.6f,%.6f,%.6f\n",run,r,j,arm,
                        gen,label,device,countMs,total);
            // Keep the shared owner alive through validation of the raw pointer.
            (void)[shared length];
        }
    }
}
