#include <sys/mman.h>
#include <unistd.h>
struct PageArray {
    size_t bytes;
    Word *data;
    explicit PageArray(size_t n) {
        auto page=size_t(getpagesize());
        bytes=((sizeof(Word)*n+page-1)/page)*page;
        data=static_cast<Word*>(mmap(nullptr,bytes,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANON,-1,0));
        if (data==MAP_FAILED) std::abort();
    }
    PageArray(const PageArray&)=delete;
    ~PageArray() { munmap(data,bytes); }
    id<MTLBuffer> wrap(id<MTLDevice> device) {
        auto b=[device newBufferWithBytesNoCopy:data length:bytes
                                     options:MTLResourceStorageModeShared deallocator:nil];
        if (!b || b.contents!=data) std::abort();
        return b;
    }
};

int main(int argc,char**argv) {
    if (argc!=2) return 1;
    unsigned run=std::atoi(argv[1]);
    std::mt19937 rng(9188+run);
    constexpr size_t sizes[]={32,32768,131072,262147,1048576,4194304};
    constexpr unsigned orders[][4]={{0,1,3,2},{1,2,0,3},{2,3,1,0},{3,0,2,1}};
    @autoreleasepool {
        MetalLabels gpu{};
        auto start=Clock::now();
        gpu.setup();
        double setup=elapsed(start);
        std::puts("run,rows,round,position,arm,setup_ms,reused_wrap_ms,wall_ms,device_ms");
        for (unsigned slot=0;slot<6;++slot) {
            size_t n=sizes[run%2 ? 5-slot : slot];
            PageArray fresh(n),reused(n);
            @autoreleasepool {
                start=Clock::now();
                auto persistent=reused.wrap(gpu.device);
                double wrap=elapsed(start);
                std::vector<Word> input(n),cpu(n),copied(n);
                for (unsigned round=0;round<16;++round) {
                    for (auto &x:input) x=rng()%prime;
                    input.front()=0; input.back()=prime-1;
                    for (unsigned pos=0;pos<4;++pos) @autoreleasepool {
                        unsigned arm=orders[(round+run)%4][pos];
                        Word *dest=(arm==0 ? cpu.data() : arm==1 ? copied.data() :
                                    arm==2 ? fresh.data : reused.data);
                        std::memcpy(dest,input.data(),n*sizeof(Word));
                        if (arm>=2 && n*sizeof(Word)<fresh.bytes) dest[n]=0x55555555;
                        double device=0;
                        start=Clock::now();
                        if (arm==0) inplaceLabels(cpu);
                        else if (arm==1) device=gpu.apply(copied);
                        else {
                            auto buffer=arm==2 ? fresh.wrap(gpu.device) : persistent;
                            device=gpu.dispatch(buffer,n);
                        }
                        double wall=elapsed(start);
                        if (arm>=2 && n*sizeof(Word)<fresh.bytes && dest[n]!=0x55555555) return 3;
                        std::printf("%u,%zu,%u,%u,%u,%.6f,%.6f,%.6f,%.6f\n",
                                    run,n,round,pos,arm,setup,wrap,wall,device);
                    }
                    if (cpu!=copied || std::memcmp(cpu.data(),fresh.data,n*sizeof(Word)) ||
                        std::memcmp(cpu.data(),reused.data,n*sizeof(Word))) return 2;
                }
            }
        }
    }
}
