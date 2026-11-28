import Foundation
import Metal

private final class ScreenContext {
    let device: MTLDevice
    let queue: MTLCommandQueue
    let pipeline: MTLComputePipelineState
    let entries: MTLBuffer
    let bitmap: MTLBuffer
    let entryCount: Int
    let bitmapBits: Int

    init(_ points: UnsafeRawPointer, _ count: Int, _ bits: UnsafeRawPointer, _ words: Int, _ bitmapBits: Int, _ path: String) throws {
        guard let device=MTLCreateSystemDefaultDevice(), let queue=device.makeCommandQueue() else {
            throw NSError(domain:"m31-metal",code:1)
        }
        let source=try String(contentsOfFile:path,encoding:.utf8)
        let library=try device.makeLibrary(source:source,options:nil)
        guard let function=library.makeFunction(name:"compact_screen"),
              let entries=device.makeBuffer(bytes:points,length:count*24),
              let bitmap=device.makeBuffer(bytes:bits,length:words*8) else {
            throw NSError(domain:"m31-metal",code:2)
        }
        self.device=device; self.queue=queue
        self.pipeline=try device.makeComputePipelineState(function:function)
        self.entries=entries; self.bitmap=bitmap; self.entryCount=count; self.bitmapBits=bitmapBits
    }
    func run(_ targets: UnsafeRawPointer, _ count: Int, _ output: UnsafeMutableRawPointer) -> Int32 {
        let total=count*entryCount*2
        guard let targetBuffer=device.makeBuffer(bytes:targets,length:count*24),
              let flags=device.makeBuffer(length:total),
              let command=queue.makeCommandBuffer(),
              let encoder=command.makeComputeCommandEncoder() else { return 2 }
        encoder.setComputePipelineState(pipeline)
        encoder.setBuffer(targetBuffer,offset:0,index:0)
        encoder.setBuffer(entries,offset:0,index:1)
        encoder.setBuffer(bitmap,offset:0,index:2)
        encoder.setBuffer(flags,offset:0,index:3)
        var n=UInt32(entryCount)
        encoder.setBytes(&n,length:4,index:4)
        var width=UInt32(bitmapBits)
        encoder.setBytes(&width,length:4,index:5)
        encoder.dispatchThreads(MTLSize(width:total,height:1,depth:1),
                                threadsPerThreadgroup:MTLSize(width:min(256,pipeline.maxTotalThreadsPerThreadgroup),height:1,depth:1))
        encoder.endEncoding()
        command.commit(); command.waitUntilCompleted()
        if command.status != .completed { return 3 }
        output.copyMemory(from:flags.contents(),byteCount:total)
        return 0
    }
}

private var screenContext: ScreenContext?

@_cdecl("m31_metal_init")
public func m31MetalInit(_ points: UnsafeRawPointer?, _ count: Int32,
                         _ bits: UnsafeRawPointer?, _ words: Int32,
                         _ bitmapBits: Int32,
                         _ shaderPath: UnsafePointer<CChar>?) -> Int32 {
    guard let points, let bits, let shaderPath,
          count>0, (bitmapBits==20 || bitmapBits==22),
          words==(1 << (bitmapBits-6)), count<=262_144 else { return 1 }
    do {
        screenContext=try ScreenContext(points,Int(count),bits,Int(words),Int(bitmapBits),String(cString:shaderPath))
        return 0
    } catch { return 2 }
}

@_cdecl("m31_metal_screen")
public func m31MetalScreen(_ targets: UnsafeRawPointer?, _ count: Int32,
                           _ output: UnsafeMutableRawPointer?) -> Int32 {
    guard let screenContext, let targets, let output, count>0, count<=1024 else { return 1 }
    return screenContext.run(targets,Int(count),output)
}
