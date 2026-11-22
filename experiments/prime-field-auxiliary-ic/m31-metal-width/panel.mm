#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <random>

int main(int argc, char** argv) { @autoreleasepool {
    if (argc!=2) return 1;
    constexpr unsigned p=2147483647, cap=1048576;
    constexpr unsigned widths[]={4,8,16,32,8}, sizes[]={8192,65536,262147,cap};
    constexpr int order[]={0,1,4,2,3};
    NSError* error=nil;
    NSString* original=[NSString stringWithContentsOfFile:@"../m31-metal-inverse/inverse.metal"
        encoding:NSUTF8StringEncoding error:&error];
    if (!original) return 2;
    NSRange marker=[original rangeOfString:@"kernel void batch8"];
    if(marker.location==NSNotFound) return 2;
    NSString* prefix=[original substringToIndex:marker.location];
    NSString* body=[original substringFromIndex:marker.location];
    id<MTLDevice> device=MTLCreateSystemDefaultDevice();
    id<MTLCommandQueue> queue=[device newCommandQueue];
    id<MTLComputePipelineState> pipeline[5];
    for(int arm=0;arm<5;arm++) {
        NSString* width=[NSString stringWithFormat:@"%u",widths[arm]];
        NSString* source=[prefix stringByAppendingString:
            [body stringByReplacingOccurrencesOfString:@"8" withString:width]];
        auto lib=[device newLibraryWithSource:source options:nil error:&error];
        auto fn=[lib newFunctionWithName:[@"batch" stringByAppendingString:width]];
        pipeline[arm]=[device newComputePipelineStateWithFunction:fn error:&error];
        if(!pipeline[arm]) {NSLog(@"%@",error); return 3;}
    }
    auto in=[device newBufferWithLength:4*cap options:MTLResourceStorageModeShared];
    auto out=[device newBufferWithLength:4*cap options:MTLResourceStorageModeShared];
    if (!in || !out || !queue) return 4;
    auto x=(uint32_t*)in.contents, y=(uint32_t*)out.contents;
    std::mt19937 rng(std::strtoul(argv[1],nullptr,10));
    std::puts("round,n,arm,width,wall_us,device_us");
    for(int r=-1;r<30;r++) for(int s=0;s<4;s++) {
        unsigned n=sizes[(s+r+4)%4];
        for(unsigned i=0;i<n;i++) x[i]=rng();
        const unsigned edges[]={0,1,p-1,p,p+1,2*p,2*p+1};
        std::copy(edges,edges+7,x);
        for(int pos=0;pos<5;pos++) { @autoreleasepool {
            int arm=(order[(r>=0 && (r/5)%2) ? 4-pos : pos]+r+5)%5;
            std::fill_n(y,n,UINT32_MAX);
            auto start=std::chrono::steady_clock::now();
            auto cmd=[queue commandBuffer]; auto enc=[cmd computeCommandEncoder];
            [enc setComputePipelineState:pipeline[arm]];
            [enc setBuffer:in offset:0 atIndex:0]; [enc setBuffer:out offset:0 atIndex:1];
            [enc setBytes:&n length:sizeof(n) atIndex:2];
            [enc dispatchThreads:MTLSizeMake((n+widths[arm]-1)/widths[arm],1,1)
                threadsPerThreadgroup:MTLSizeMake(MIN(256,pipeline[arm].maxTotalThreadsPerThreadgroup),1,1)];
            [enc endEncoding]; [cmd commit]; [cmd waitUntilCompleted];
            double us=std::chrono::duration<double,std::micro>(std::chrono::steady_clock::now()-start).count();
            if(cmd.status!=MTLCommandBufferStatusCompleted) return 5;
            for(unsigned i=0;i<n;i++) {
                unsigned a=x[i]%p;
                if(y[i]>=p || (a ? uint64_t(a)*y[i]%p!=1 : y[i]!=0)) return 6;
            }
            if(r>=0) std::printf("%d,%u,%d,%u,%.3f,%.3f\n",r,n,arm,widths[arm],us,
                1e6*(cmd.GPUEndTime-cmd.GPUStartTime));
        }}
    }
}}
