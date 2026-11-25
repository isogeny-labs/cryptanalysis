#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#import <dispatch/dispatch.h>
#include "../m31-field-ffi/m31.h"
#include <chrono>
#include <algorithm>
#include <cstdio>
#include <random>
#include <cstdlib>
using Clock = std::chrono::steady_clock;
double elapsed(Clock::time_point t) { return std::chrono::duration<double>(Clock::now()-t).count(); }

int main() { @autoreleasepool {
    auto setup=Clock::now();
    id<MTLDevice> dev=MTLCreateSystemDefaultDevice();
    if (!dev) return 1;
    NSError *error=nil;
    NSString *source=[NSString stringWithContentsOfFile:@"../m31-metal-inverse/inverse.metal"
                                   encoding:NSUTF8StringEncoding error:&error];
    id<MTLLibrary> lib=[dev newLibraryWithSource:source options:nil error:&error];
    if (!lib) { NSLog(@"%@",error); return 2; }
    id<MTLComputePipelineState> pipe=[dev newComputePipelineStateWithFunction:
        [lib newFunctionWithName:@"batch8"] error:&error];
    if (!pipe) { NSLog(@"%@",error); return 3; }
    auto cpuQueue=dispatch_get_global_queue(QOS_CLASS_USER_INITIATED,0);
    id<MTLCommandQueue> queue=[dev newCommandQueue];
    constexpr uint32_t cap=1048576;
    id<MTLBuffer> input=[dev newBufferWithLength:4*cap options:MTLResourceStorageModeShared];
    id<MTLBuffer> output=[dev newBufferWithLength:4*cap options:MTLResourceStorageModeShared];
    if (!input || !output || !queue) return 4;
    fprintf(stderr,"%s, setup %.9f s\n",dev.name.UTF8String,elapsed(setup));
    auto *x=(uint32_t*)input.contents, *y=(uint32_t*)output.contents;
    std::mt19937 rng(291157);
    const uint32_t sizes[]={64,8192,32768,65536,98304,131072,196608,262147,524288,1048576};
    // Rotate the Williams row and its reverse to balance order and adjacency.
    const int order[]={0,1,4,2,3};
    for (int rep=-1;rep<20;++rep) for (int s=0;s<10;++s) {
        uint32_t n=sizes[(s+rep+10)%10];
        for (uint32_t i=0;i<n;++i) x[i]=rng();
        const uint32_t edges[]={0,1,2147483646,2147483647,2147483648u,4294967294u,4294967295u};
        for (unsigned i=0;i<7;++i) x[i]=edges[i];
        for (int slot=0;slot<5;++slot) { @autoreleasepool {
            const int row=(rep+10)%10;
            const int mode=(order[row<5 ? slot : 4-slot]+row%5)%5;
            double gpu=0;
            for (uint32_t i=0;i<n;++i) y[i]=UINT32_MAX;
            auto start=Clock::now();
            if (mode==0) m31_batch_inverse(x,y,n);
            else if (mode<4) {
                const size_t tasks = mode==1 ? 4 : (mode==2 ? 10 : 14);
                const size_t tiles=(n+63)/64;
                dispatch_apply(tasks,cpuQueue,^(size_t j) {
                    size_t begin=std::min<size_t>(n,64*(tiles*j/tasks));
                    size_t end=std::min<size_t>(n,64*(tiles*(j+1)/tasks));
                    m31_batch_inverse(x+begin,y+begin,end-begin);
                });
            }
            else {
                id<MTLCommandBuffer> command=[queue commandBuffer];
                id<MTLComputeCommandEncoder> enc=[command computeCommandEncoder];
                [enc setComputePipelineState:pipe];
                [enc setBuffer:input offset:0 atIndex:0];
                [enc setBuffer:output offset:0 atIndex:1];
                [enc setBytes:&n length:sizeof(n) atIndex:2];
                uint32_t threads=(n+7)/8;
                [enc dispatchThreads:MTLSizeMake(threads,1,1)
                   threadsPerThreadgroup:MTLSizeMake(MIN(256,pipe.maxTotalThreadsPerThreadgroup),1,1)];
                [enc endEncoding]; [command commit]; [command waitUntilCompleted];
                if (command.status!=MTLCommandBufferStatusCompleted) { NSLog(@"%@",command.error); return 5; }
                gpu=command.GPUEndTime-command.GPUStartTime;
            }
            double wall=elapsed(start);
            for (uint32_t i=0;i<n;++i) {
                uint32_t a=x[i]%2147483647u;
                if (y[i]>=2147483647u || (a ? uint64_t(a)*y[i]%2147483647u!=1 : y[i]!=0))
                    return 6;
            }
            if (rep>=0) printf("%d,%u,%d,%.9f,%.9f\n",rep,n,mode,wall,gpu);
        }}
    }
    return 0;
}}
