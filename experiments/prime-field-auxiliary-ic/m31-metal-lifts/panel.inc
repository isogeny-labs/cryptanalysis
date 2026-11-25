#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#include <cstring>
using Clock=std::chrono::steady_clock;
double elapsed(Clock::time_point start) {
    return std::chrono::duration<double,std::milli>(Clock::now()-start).count();
}
struct MetalLabels {
    id<MTLDevice> device;
    id<MTLCommandQueue> queue;
    id<MTLComputePipelineState> pipeline;

    void setup(NSString *name=@"labels") {
        device=MTLCreateSystemDefaultDevice();
        NSError *error=nil;
        NSString *src=[NSString stringWithContentsOfFile:@"lifts.metal"
                            encoding:NSUTF8StringEncoding error:&error];
        if (!device || !src) { NSLog(@"Metal setup: %@",error); std::exit(1); }
        auto lib=[device newLibraryWithSource:src options:nil error:&error];
        auto fn=[lib newFunctionWithName:name];
        if (!fn) { NSLog(@"shader: %@",error); std::exit(2); }
        pipeline=[device newComputePipelineStateWithFunction:fn error:&error];
        queue=[device newCommandQueue];
        if (!pipeline || !queue) { NSLog(@"pipeline: %@",error); std::exit(3); }
    }

    double dispatch(id<MTLBuffer> buf, size_t words) {
        auto cmd=[queue commandBuffer];
        auto enc=[cmd computeCommandEncoder];
        [enc setComputePipelineState:pipeline];
        [enc setBuffer:buf offset:0 atIndex:0];
        [enc dispatchThreads:MTLSizeMake(words,1,1)
            threadsPerThreadgroup:MTLSizeMake(std::min<NSUInteger>(256,pipeline.maxTotalThreadsPerThreadgroup),1,1)];
        [enc endEncoding];
        [cmd commit];
        [cmd waitUntilCompleted];
        if (cmd.status!=MTLCommandBufferStatusCompleted) { NSLog(@"dispatch: %@",cmd.error); std::exit(5); }
        return 1000*(cmd.GPUEndTime-cmd.GPUStartTime);
    }

    double apply(std::vector<Word>& x) {
        size_t bytes=x.size()*sizeof(Word);
        auto buf=[device newBufferWithBytes:x.data() length:bytes options:MTLResourceStorageModeShared];
        if (!buf) std::exit(4);
        double deviceTime=dispatch(buf,x.size());
        std::memcpy(x.data(),buf.contents,bytes);
        return deviceTime;
    }
};
int main(int argc,char** argv) {
  if (argc!=2) return 1;
  int run=std::atoi(argv[1]);
  @autoreleasepool {
    MetalLabels gpu{};
    std::vector<Word> reference;
    std::puts("process,round,position,gpu,setup_ms,gen_ms,label_ms,device_ms,total_wall_ms,count");
    for (int r=0;r<=12;++r) for (int pos=0;pos<2;++pos) @autoreleasepool {
      bool metal=(run+r+pos)%2;
      auto start=Clock::now();
      double setup=0;
      if (metal && r==0) { gpu.setup(); setup=elapsed(start); }
      auto genStart=Clock::now();
      auto data=generate<true>();
      double gen=elapsed(genStart);
      auto labelStart=Clock::now();
      double device=0;
      if (metal) device=gpu.apply(data);
      else inplaceLabels(data);
      double label=elapsed(labelStart);
      auto count=std::accumulate(data.begin(),data.end(),0u);
      double total=elapsed(start);
      if (count!=1924024 || data.size()!=3846525) return 6;
      if (reference.empty()) reference=data;
      else if (data!=reference) return 7;
      std::printf("%d,%d,%d,%d,%.6f,%.6f,%.6f,%.6f,%.6f,%u\n",run,r,pos,int(metal),
                  setup,gen,label,device,total,count);
    }
  }
}
