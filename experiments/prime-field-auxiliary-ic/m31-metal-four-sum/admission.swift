import Foundation
import Metal

// Exact public M31 affine candidate screen. This is a component admission,
// independent of the Rust collector and its required certificate replay.
let p: UInt64 = 2_147_483_647
struct XY { var x: UInt64; var y: UInt64 }
struct GPUPoint { var x: UInt64; var y: UInt64; var finite: UInt64 }
func red(_ a: UInt64) -> UInt64 {
    var x = (a & p) + (a >> 31)
    if x >= p { x -= p }
    return x
}
func add(_ a: UInt64, _ b: UInt64) -> UInt64 { red(a + b) }
func sub(_ a: UInt64, _ b: UInt64) -> UInt64 { a >= b ? a - b : p - (b - a) }
func mul(_ a: UInt64, _ b: UInt64) -> UInt64 { red(a * b) }
func powMod(_ x: UInt64, _ e: UInt64) -> UInt64 {
    var a = x, n = e, y: UInt64 = 1
    while n != 0 { if n & 1 != 0 { y = mul(y,a) }; a = mul(a,a); n >>= 1 }
    return y
}
func pointAdd(_ a: XY?, _ b: XY?) -> XY? {
    guard let a else { return b }; guard let b else { return a }
    let dx = sub(b.x,a.x), dy = sub(b.y,a.y)
    if dx == 0 && dy != 0 { return nil }
    let slope: UInt64
    if dx == 0 {
        if a.y == 0 { return nil }
        slope = mul(add(mul(3,mul(a.x,a.x)),2),powMod(add(a.y,a.y),p-2))
    } else { slope = mul(dy,powMod(dx,p-2)) }
    let x = sub(sub(mul(slope,slope),a.x),b.x)
    return XY(x:x,y:sub(mul(slope,sub(a.x,x)),a.y))
}
let shader = """
#include <metal_stdlib>
using namespace metal;
struct P { ulong x; ulong y; ulong finite; };
constant ulong MOD = 2147483647ul;
ulong red(ulong a) { ulong x=(a & MOD)+(a >> 31); return x>=MOD ? x-MOD : x; }
ulong fadd(ulong a,ulong b) { return red(a+b); }
ulong fsub(ulong a,ulong b) { return a>=b ? a-b : MOD-(b-a); }
ulong times(ulong a,ulong b) { return red(a*b); }
ulong power(ulong a,ulong e) { ulong y=1; while(e) { if(e&1ul) y=times(y,a); a=times(a,a); e>>=1; } return y; }
P candidate(P a, P b) {
  if(!a.finite) return b;
  if(!b.finite) return a;
  ulong dx=fsub(b.x,a.x), dy=fsub(b.y,a.y);
  if(dx==0 && dy!=0) return P{0,0,0};
  ulong s;
  if(dx==0) {
    if(a.y==0) return P{0,0,0};
    s=times(fadd(times(3ul,times(a.x,a.x)),2ul),power(fadd(a.y,a.y),MOD-2));
  } else s=times(dy,power(dx,MOD-2));
  ulong x=fsub(fsub(times(s,s),a.x),b.x);
  return P{x,fsub(times(s,fsub(a.x,x)),a.y),1};
}
kernel void candidates(device const P *left [[buffer(0)]], device const P *right [[buffer(1)]],
                       device P *out [[buffer(2)]], uint id [[thread_position_in_grid]]) {
  out[id]=candidate(left[id],right[id]);
}
kernel void screen(device const P *left [[buffer(0)]], device const P *right [[buffer(1)]],
                   device const ulong *bitmap [[buffer(2)]], device uchar *flags [[buffer(3)]],
                   uint id [[thread_position_in_grid]]) {
  P result=candidate(left[id],right[id]);
  if(!result.finite) { flags[id]=2; return; }
  ulong bit=(result.x*0x9e3779b97f4a7c15ul)>>44;
  flags[id]=((bitmap[bit>>6]>>(bit&63))&1ul) ? 1 : 0;
}
kernel void compact_screen(device const P *targets [[buffer(0)]], device const P *entries [[buffer(1)]],
                           device const ulong *bitmap [[buffer(2)]], device uchar *flags [[buffer(3)]],
                           constant uint &entryCount [[buffer(4)]], uint id [[thread_position_in_grid]]) {
  uint width=2*entryCount;
  P q=targets[id/width], b=entries[(id/2)%entryCount];
  if(id&1u && b.finite && b.y!=0) b.y=MOD-b.y;
  P result=candidate(q,b);
  if(!result.finite) { flags[id]=2; return; }
  ulong bit=(result.x*0x9e3779b97f4a7c15ul)>>44;
  flags[id]=((bitmap[bit>>6]>>(bit&63))&1ul) ? 1 : 0;
}
"""
guard let device=MTLCreateSystemDefaultDevice(),
      let queue=device.makeCommandQueue() else { fatalError("Metal unavailable") }
let g=XY(x:1,y:814455902), q=XY(x:1767503692,y:244402461)
let columns=Int(CommandLine.arguments.dropFirst().first ?? "195")!
let lanes=Int(CommandLine.arguments.dropFirst(2).first ?? "1")!
precondition(columns>0 && columns<=512)
precondition(lanes>0 && lanes<=64)
var base=[XY]()
var baseX: UInt64=0
while base.count<columns {
    let rhs=add(add(mul(mul(baseX,baseX),baseX),mul(2,baseX)),14)
    let y=powMod(rhs,(p+1)/4)
    if mul(y,y)==rhs { base.append(XY(x:baseX,y:min(y,p-y))) }
    baseX += 1
}
var seen=Set<UInt64>(), entries=[XY?]()
for i in 0..<columns {
    for j in i..<columns {
        for negative in [false,true] {
            if i==j && negative { continue }
            let second=negative ? XY(x:base[j].x,y:base[j].y==0 ? 0 : p-base[j].y) : base[j]
            let sum=pointAdd(base[i],second)
            let canonical=sum.map { $0.y>p/2 ? XY(x:$0.x,y:p-$0.y) : $0 }
            let key=canonical?.x ?? p
            if seen.insert(key).inserted { entries.append(canonical) }
        }
    }
}
var left=[GPUPoint](), right=[GPUPoint]()
var laneTarget: XY?=q
for _ in 0..<lanes {
    let target=laneTarget!
    for point in entries {
        for negative in [false,true] {
            if point == nil && negative { continue }
            let b=negative ? point.map { XY(x:$0.x,y:$0.y==0 ? 0 : p-$0.y) } : point
            left.append(GPUPoint(x:target.x,y:target.y,finite:1))
            right.append(GPUPoint(x:b?.x ?? 0,y:b?.y ?? 0,finite:b == nil ? 0 : 1))
        }
    }
    laneTarget=pointAdd(laneTarget,g)
}
// Explicit vertical, doubling and identity probes precede ordinary candidates.
let specials: [(XY?,XY?)] = [(q,XY(x:q.x,y:p-q.y)),(g,g),(nil,q),(q,nil)]
for i in 0..<specials.count {
    let (a,b)=specials[i]
    left[i]=GPUPoint(x:a?.x ?? 0,y:a?.y ?? 0,finite:a == nil ? 0 : 1)
    right[i]=GPUPoint(x:b?.x ?? 0,y:b?.y ?? 0,finite:b == nil ? 0 : 1)
}
let n=left.count
var bitmap=[UInt64](repeating:0,count:1 << 14)
func bitmapBit(_ x: UInt64) -> Int { Int((x &* 0x9e3779b97f4a7c15) >> 44) }
for point in entries {
    if let point {
        let bit=bitmapBit(point.x)
        bitmap[bit >> 6] |= UInt64(1) << UInt64(bit & 63)
    }
}
func cpu(_ v: GPUPoint) -> XY? { v.finite == 0 ? nil : XY(x:v.x,y:v.y) }
let t0=CFAbsoluteTimeGetCurrent()
let library=try device.makeLibrary(source:shader,options:nil)
let pipeline=try device.makeComputePipelineState(function:library.makeFunction(name:"candidates")!)
let tLibrary=CFAbsoluteTimeGetCurrent()
let byteCount=n*MemoryLayout<GPUPoint>.stride
let aBuf=device.makeBuffer(bytes:left,length:byteCount)!
let bBuf=device.makeBuffer(bytes:right,length:byteCount)!
let oBuf=device.makeBuffer(length:byteCount)!
let tBuffers=CFAbsoluteTimeGetCurrent()
let command=queue.makeCommandBuffer()!
let encoder=command.makeComputeCommandEncoder()!
encoder.setComputePipelineState(pipeline)
encoder.setBuffer(aBuf,offset:0,index:0)
encoder.setBuffer(bBuf,offset:0,index:1)
encoder.setBuffer(oBuf,offset:0,index:2)
encoder.dispatchThreads(MTLSize(width:n,height:1,depth:1),threadsPerThreadgroup:MTLSize(width:256,height:1,depth:1))
encoder.endEncoding(); command.commit(); command.waitUntilCompleted()
let charged=CFAbsoluteTimeGetCurrent()-t0
let dispatch=CFAbsoluteTimeGetCurrent()-tBuffers
precondition(command.status == .completed)
let output=oBuf.contents().bindMemory(to:GPUPoint.self,capacity:n)
var mismatches=0
let cpuStart=CFAbsoluteTimeGetCurrent()
var checksum: UInt64=0
var digest: UInt64=14_695_981_039_346_656_037
var expectedPoints=[XY?]()
expectedPoints.reserveCapacity(n)
for i in 0..<n {
    let expected=pointAdd(cpu(left[i]),cpu(right[i]))
    expectedPoints.append(expected)
    checksum ^= expected?.x ?? 0
    for word in [expected?.x ?? p, expected?.y ?? p] {
        digest=(digest ^ word) &* 1_099_511_628_211
    }
}
let cpuSeconds=CFAbsoluteTimeGetCurrent()-cpuStart
for i in 0..<n {
    let expected=expectedPoints[i]
    let got=cpu(output[i])
    if expected?.x != got?.x || expected?.y != got?.y { mismatches += 1; if mismatches<5 { fputs("mismatch at \(i)\n",stderr) } }
}
let screenStart=CFAbsoluteTimeGetCurrent()
let screenPipeline=try device.makeComputePipelineState(function:library.makeFunction(name:"screen")!)
let bitmapBuf=device.makeBuffer(bytes:bitmap,length:bitmap.count*8)!
let flagBuf=device.makeBuffer(length:n)!
let screenCmd=queue.makeCommandBuffer()!
let screenEncoder=screenCmd.makeComputeCommandEncoder()!
screenEncoder.setComputePipelineState(screenPipeline)
screenEncoder.setBuffer(aBuf,offset:0,index:0)
screenEncoder.setBuffer(bBuf,offset:0,index:1)
screenEncoder.setBuffer(bitmapBuf,offset:0,index:2)
screenEncoder.setBuffer(flagBuf,offset:0,index:3)
screenEncoder.dispatchThreads(MTLSize(width:n,height:1,depth:1),threadsPerThreadgroup:MTLSize(width:256,height:1,depth:1))
screenEncoder.endEncoding(); screenCmd.commit(); screenCmd.waitUntilCompleted()
let screenSeconds=CFAbsoluteTimeGetCurrent()-screenStart
precondition(screenCmd.status == .completed)
let flags=flagBuf.contents().bindMemory(to:UInt8.self,capacity:n)
var flagMismatches=0, positives=0
for i in 0..<n {
    let expected: UInt8
    if let point=expectedPoints[i] {
        let bit=bitmapBit(point.x)
        expected=(bitmap[bit >> 6] & (UInt64(1) << UInt64(bit & 63))) == 0 ? 0 : 1
    } else { expected=2 }
    if flags[i] != expected { flagMismatches += 1 }
    if flags[i] != 0 { positives += 1 }
}
var compactTargets=[GPUPoint](), compactEntries=[GPUPoint]()
var nextTarget: XY?=q
for _ in 0..<lanes {
    let target=nextTarget!
    compactTargets.append(GPUPoint(x:target.x,y:target.y,finite:1))
    nextTarget=pointAdd(nextTarget,g)
}
for point in entries { compactEntries.append(GPUPoint(x:point?.x ?? 0,y:point?.y ?? 0,finite:point == nil ? 0 : 1)) }
let compactStart=CFAbsoluteTimeGetCurrent()
let compactPipeline=try device.makeComputePipelineState(function:library.makeFunction(name:"compact_screen")!)
let targetBuf=device.makeBuffer(bytes:compactTargets,length:compactTargets.count*MemoryLayout<GPUPoint>.stride)!
let entryBuf=device.makeBuffer(bytes:compactEntries,length:compactEntries.count*MemoryLayout<GPUPoint>.stride)!
let compactFlagBuf=device.makeBuffer(length:n)!
let compactCmd=queue.makeCommandBuffer()!
let compactEncoder=compactCmd.makeComputeCommandEncoder()!
compactEncoder.setComputePipelineState(compactPipeline)
compactEncoder.setBuffer(targetBuf,offset:0,index:0)
compactEncoder.setBuffer(entryBuf,offset:0,index:1)
compactEncoder.setBuffer(bitmapBuf,offset:0,index:2)
compactEncoder.setBuffer(compactFlagBuf,offset:0,index:3)
var entryCount=UInt32(entries.count)
compactEncoder.setBytes(&entryCount,length:4,index:4)
compactEncoder.dispatchThreads(MTLSize(width:n,height:1,depth:1),threadsPerThreadgroup:MTLSize(width:256,height:1,depth:1))
compactEncoder.endEncoding(); compactCmd.commit(); compactCmd.waitUntilCompleted()
let compactSeconds=CFAbsoluteTimeGetCurrent()-compactStart
precondition(compactCmd.status == .completed)
let compactFlags=compactFlagBuf.contents().bindMemory(to:UInt8.self,capacity:n)
var compactMismatches=0
for i in 4..<n { if compactFlags[i] != flags[i] { compactMismatches += 1 } }
print("{\"schema\":\"m31-metal-admission/v1\",\"device\":\"\(device.name)\",\"columns\":\(columns),\"lanes\":\(lanes),\"entries\":\(entries.count),\"n\":\(n),\"mismatches\":\(mismatches),\"flag_mismatches\":\(flagMismatches),\"compact_flag_mismatches\":\(compactMismatches),\"bitmap_positives\":\(positives),\"gpu_setup_dispatch_wall_s\":\(charged),\"screen_pipeline_dispatch_wall_s\":\(screenSeconds),\"compact_setup_dispatch_wall_s\":\(compactSeconds),\"library_pipeline_wall_s\":\(tLibrary-t0),\"buffers_wall_s\":\(tBuffers-tLibrary),\"dispatch_wait_wall_s\":\(dispatch),\"cpu_affine_wall_s\":\(cpuSeconds),\"checksum\":\(checksum),\"digest\":\(digest)}")
if mismatches != 0 || flagMismatches != 0 || compactMismatches != 0 { exit(1) }
