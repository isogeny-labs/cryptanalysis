import Foundation
import Metal

private struct WirePoint { var x: UInt64; var y: UInt64; var finite: UInt64 }

private final class ScreenContext {
    let device: MTLDevice
    let queue: MTLCommandQueue
    let pipeline: MTLComputePipelineState
    let entries: MTLBuffer
    let bitmap: MTLBuffer
    let coarse: MTLBuffer
    let entryCount: Int
    let bitmapBits: Int
    let useCoarse: Int

    init(_ points: UnsafeRawPointer, _ count: Int, _ bits: UnsafeRawPointer, _ words: Int, _ bitmapBits: Int, _ useCoarse: Int, _ path: String) throws {
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
        let coarse: MTLBuffer
        if useCoarse != 0 {
            var coarseWords=[UInt64](repeating:0,count:16_384)
            let coordinates=points.assumingMemoryBound(to:WirePoint.self)
            for i in 0..<count where coordinates[i].finite != 0 {
                let bit=Int((coordinates[i].x &* 0x9e3779b97f4a7c15) >> 44)
                coarseWords[bit >> 6] |= UInt64(1) << UInt64(bit & 63)
            }
            guard let buffer=device.makeBuffer(bytes:coarseWords,length:coarseWords.count*8) else {
                throw NSError(domain:"m31-metal",code:3)
            }
            coarse=buffer
        } else { coarse=bitmap }
        self.entries=entries; self.bitmap=bitmap; self.coarse=coarse
        self.entryCount=count; self.bitmapBits=bitmapBits; self.useCoarse=useCoarse
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
        encoder.setBuffer(coarse,offset:0,index:6)
        var coarseEnabled=UInt32(useCoarse)
        encoder.setBytes(&coarseEnabled,length:4,index:7)
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
                         _ bitmapBits: Int32, _ useCoarse: Int32,
                         _ shaderPath: UnsafePointer<CChar>?) -> Int32 {
    guard let points, let bits, let shaderPath,
          count>0, (bitmapBits==20 || bitmapBits==22),
          (useCoarse==0 || (useCoarse==1 && bitmapBits==22)),
          words==(1 << (bitmapBits-6)), count<=262_144 else { return 1 }
    do {
        screenContext=try ScreenContext(points,Int(count),bits,Int(words),Int(bitmapBits),Int(useCoarse),String(cString:shaderPath))
        return 0
    } catch { return 2 }
}

@_cdecl("m31_metal_screen")
public func m31MetalScreen(_ targets: UnsafeRawPointer?, _ count: Int32,
                           _ output: UnsafeMutableRawPointer?) -> Int32 {
    guard let screenContext, let targets, let output, count>0, count<=1024 else { return 1 }
    return screenContext.run(targets,Int(count),output)
}
