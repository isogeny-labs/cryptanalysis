struct Totals {
    Word yes=0,checksum=0,slice=0,visited=0;
    void combine(Totals t) {
        yes+=t.yes; checksum^=t.checksum; slice+=t.slice; visited+=t.visited;
    }
    bool valid() const {
        return yes==1073752646u && checksum==1602806244u && slice==536874593u && visited==prime;
    }
};
static_assert(sizeof(Totals)==16);

static Totals on_cpu() {
    std::vector<Word> block;
    Totals result;
    for (uint64_t base=0;base<prime;base+=65536) {
        block.resize(std::min<uint64_t>(65536,prime-base));
        std::iota(block.begin(),block.end(),Word(base));
        inplaceLabels(block);
        for (size_t j=0;j<block.size();++j) {
            Word x=Word(base+j),yes=block[j];
            result.yes+=yes;
            result.checksum^=x*yes;
            result.slice+=yes*Word((x&4)==0);
        }
        result.visited+=Word(block.size());
    }
    return result;
}

static Totals on_gpu(double &setup,double &device) {
    auto t=Clock::now();
    MetalLabels m;
    m.setup(@"field_totals");
    if (m.pipeline.maxTotalThreadsPerThreadgroup<256) std::exit(3);
    auto out=[m.device newBufferWithLength:256*sizeof(Totals) options:MTLResourceStorageModeShared];
    if (!out) std::exit(4);
    setup=elapsed(t);
    Totals result;
    for (uint64_t base=0;base<prime;base+=1u<<26) @autoreleasepool {
        Word range[]={Word(base),Word(std::min<uint64_t>(1u<<26,prime-base))};
        auto cmd=[m.queue commandBuffer];
        auto enc=[cmd computeCommandEncoder];
        [enc setComputePipelineState:m.pipeline];
        [enc setBuffer:out offset:0 atIndex:0];
        [enc setBytes:range length:sizeof(range) atIndex:1];
        [enc dispatchThreadgroups:MTLSizeMake(256,1,1) threadsPerThreadgroup:MTLSizeMake(256,1,1)];
        [enc endEncoding]; [cmd commit]; [cmd waitUntilCompleted];
        if (cmd.status!=MTLCommandBufferStatusCompleted) { NSLog(@"%@",cmd.error); std::exit(5); }
        device+=1000*(cmd.GPUEndTime-cmd.GPUStartTime);
        for (size_t i=0;i<256;++i) {
            Totals v;
            std::memcpy(&v,(char*)out.contents+i*sizeof(v),sizeof(v));
            result.combine(v);
        }
    }
    return result;
}

int main(int argc,char **argv) {
    if (argc!=2) return 1;
    int run=std::atoi(argv[1]);
    std::puts("run,arm,wall_ms,setup_ms,device_ms,visited,lifts,xor,bit2_zero");
    for (int pos=0;pos<2;++pos) @autoreleasepool {
        int arm=(run+pos)%2;
        double setup=0,device=0;
        auto start=Clock::now();
        auto v=arm ? on_gpu(setup,device) : on_cpu();
        double wall=elapsed(start);
        if (!v.valid()) return 2;
        std::printf("%d,%d,%.6f,%.6f,%.6f,%u,%u,%u,%u\n",run,arm,wall,setup,device,
                    v.visited,v.yes,v.checksum,v.slice);
        std::fflush(stdout);
    }
}
