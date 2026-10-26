#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#include <mach-o/dyld.h>
#include "wire.hpp"
#include <algorithm>
class CcMetal {
    id<MTLDevice> device;
    id<MTLCommandQueue> queue;
    id<MTLComputePipelineState> add,mul,rho;
    std::string label;
    static std::runtime_error error(NSError *e,const char *fallback) {
        return std::runtime_error(e ? e.localizedDescription.UTF8String : fallback);
    }
public:
    CcMetal(int ordinal,const char *) {
        NSArray<id<MTLDevice>> *devices=MTLCopyAllDevices();
        if (static_cast<NSUInteger>(ordinal)>=devices.count)
            throw std::runtime_error("no Metal device at requested ordinal");
        device=devices[ordinal];label=device.name.UTF8String;queue=[device newCommandQueue];
        // Resolve the actual executable even when launched through PATH.
        std::vector<char> executable(1024);std::uint32_t length=1024;
        if (_NSGetExecutablePath(executable.data(),&length)!=0) {
            executable.resize(length);
            if (_NSGetExecutablePath(executable.data(),&length)!=0)
                throw std::runtime_error("cannot locate Metal worker executable");
        }
        NSString *path=[[NSString stringWithUTF8String:executable.data()] stringByDeletingLastPathComponent];
        NSURL *url=[NSURL fileURLWithPath:[path stringByAppendingPathComponent:@"certicom.metallib"]];
        NSError *err=nil;
        id<MTLLibrary> library=[device newLibraryWithURL:url error:&err];
        if (!library) throw error(err,"cannot load certicom.metallib beside worker");
        add=[device newComputePipelineStateWithFunction:[library newFunctionWithName:@"certicom_add"] error:&err];
        if (!add) throw error(err,"cannot create addition pipeline");
        mul=[device newComputePipelineStateWithFunction:[library newFunctionWithName:@"certicom_mul"] error:&err];
        if (!mul) throw error(err,"cannot create multiplication pipeline");
        rho=[device newComputePipelineStateWithFunction:[library newFunctionWithName:@"certicom_rho"] error:&err];
        if (!rho || !queue) throw error(err,"cannot create Metal rho pipeline/queue");
    }
    const char *kind() const {return "metal";}
    const std::string &name() const {return label;}
    void execute(CcRequest &r) {
        @autoreleasepool {
            std::size_t bytes=r.n*(r.op==3 ? sizeof(CcRho) : sizeof(CcPoint));
            const void *first=r.op==3 ? static_cast<const void *>(r.states.data()) : r.left.data();
            id<MTLBuffer> a=[device newBufferWithBytes:first length:bytes options:MTLResourceStorageModeShared];
            cc_u32 dummy=0;
            const void *second=&dummy;std::size_t secondBytes=sizeof(dummy);
            if (r.op==1) {second=r.right.data();secondBytes=r.n*sizeof(CcPoint);}
            if (r.op==2) {second=r.scalars.data();secondBytes=r.n*sizeof(CcInteger);}
            id<MTLBuffer> b=[device newBufferWithBytes:second length:secondBytes options:MTLResourceStorageModeShared];
            id<MTLBuffer> out=[device newBufferWithLength:bytes options:MTLResourceStorageModeShared];
            if (!a || !b || !out) throw std::runtime_error("Metal buffer allocation failed");
            id<MTLComputePipelineState> pipeline=r.op==1 ? add : (r.op==2 ? mul : rho);
            id<MTLCommandBuffer> command=[queue commandBuffer];
            id<MTLComputeCommandEncoder> enc=[command computeCommandEncoder];
            if (!command || !enc) throw std::runtime_error("Metal command allocation failed");
            [enc setComputePipelineState:pipeline];
            [enc setBytes:&r.curve length:sizeof(CcCurve) atIndex:0];
            [enc setBuffer:a offset:0 atIndex:1];[enc setBuffer:b offset:0 atIndex:2];
            [enc setBuffer:out offset:0 atIndex:3];[enc setBytes:&r.n length:4 atIndex:4];
            if (r.op==3) [enc setBytes:&r.steps length:4 atIndex:5];
            NSUInteger width=std::min<NSUInteger>(64,pipeline.maxTotalThreadsPerThreadgroup);
            [enc dispatchThreads:MTLSizeMake(r.n,1,1) threadsPerThreadgroup:MTLSizeMake(width,1,1)];
            [enc endEncoding];[command commit];[command waitUntilCompleted];
            if (command.status!=MTLCommandBufferStatusCompleted)
                throw error(command.error,"Metal command did not complete");
            if (r.op==3) std::memcpy(r.rho.data(),out.contents,bytes);
            else std::memcpy(r.points.data(),out.contents,bytes);
        }
    }
};
int main(int argc,char **argv) {
    @autoreleasepool {return cc_worker_main<CcMetal>(argc,argv);}
}
