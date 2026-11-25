int main(int argc,char **argv) {
    if (argc!=2) return 1;
    int run=std::atoi(argv[1]);
    @autoreleasepool {
        MetalLabels gpu{};
        auto start=Clock::now();
        gpu.setup();
        double setup=elapsed(start);
        std::mt19937 rng(9170+run);
        constexpr size_t sizes[]={32,1024,8192,32768,65536,131072,262147,1048576,4194304};
        std::printf("run,round,rows,gpu_first,setup_ms,neon_ms,metal_wall_ms,metal_device_ms\n");
        for (int round=0;round<14;++round) for (int slot=0;slot<9;++slot) @autoreleasepool {
            size_t n=sizes[(slot+round+run)%9];
            std::vector<Word> cpu(n);
            for (auto &x:cpu) x=rng()%prime;
            cpu[0]=0; cpu[1]=prime-1;
            auto metal=cpu;
            bool gpuFirst=(round+run)%2;
            double cpuTime=0,metalTime=0,deviceTime=0;
            for (unsigned pos=0;pos<2;++pos) {
                auto t=Clock::now();
                if (pos==unsigned(!gpuFirst)) {
                    deviceTime=gpu.apply(metal);
                    metalTime=elapsed(t);
                } else {
                    inplaceLabels(cpu);
                    cpuTime=elapsed(t);
                }
            }
            if (cpu!=metal) return 2;
            std::printf("%d,%d,%zu,%d,%.6f,%.6f,%.6f,%.6f\n",run,round,n,int(gpuFirst),
                        setup,cpuTime,metalTime,deviceTime);
        }
    }
}
