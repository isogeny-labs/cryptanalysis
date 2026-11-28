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
uchar screen_x(ulong x, bool finite, device const ulong *bitmap,
               uint bitmapBits, device const ulong *coarse,
               uint screenMode, device const uint *xhash) {
  if(!finite) return 2;
  ulong hash=x*0x9e3779b97f4a7c15ul;
  if(screenMode!=0) {
    ulong coarseBit=hash>>44;
    if(((coarse[coarseBit>>6]>>(coarseBit&63))&1ul)==0) return 0;
  }
  ulong bit=hash>>(64-bitmapBits);
  if(((bitmap[bit>>6]>>(bit&63))&1ul)==0) return 0;
  if(screenMode==2 || screenMode==3) {
    uint slot=uint(hash>>47);
    for(uint probes=0; probes<(1u<<17); ++probes) {
      uint key=xhash[slot];
      if(key==uint(x)) return 1;
      if(key==0xffffffffu) return 0;
      slot=(slot+1u)&((1u<<17)-1u);
    }
    return 0;
  }
  return 1;
}
kernel void compact_screen(device const P *targets [[buffer(0)]], device const P *entries [[buffer(1)]],
                           device const ulong *bitmap [[buffer(2)]], device uchar *flags [[buffer(3)]],
                           constant uint &entryCount [[buffer(4)]],
                           constant uint &bitmapBits [[buffer(5)]],
                           device const ulong *coarse [[buffer(6)]],
                           constant uint &useCoarse [[buffer(7)]],
                           device const uint *xhash [[buffer(8)]], uint id [[thread_position_in_grid]]) {
  uint width=2*entryCount;
  P q=targets[id/width], b=entries[(id/2)%entryCount];
  if(!(id&1u) && b.finite && b.y!=0) b.y=MOD-b.y;
  P result=candidate(q,b);
  flags[id]=screen_x(result.x,result.finite!=0,bitmap,bitmapBits,coarse,useCoarse,xhash);
}
kernel void compact_screen_paired(device const P *targets [[buffer(0)]],
                                  device const P *entries [[buffer(1)]],
                                  device const ulong *bitmap [[buffer(2)]],
                                  device uchar *flags [[buffer(3)]],
                                  constant uint &entryCount [[buffer(4)]],
                                  constant uint &bitmapBits [[buffer(5)]],
                                  device const ulong *coarse [[buffer(6)]],
                                  constant uint &screenMode [[buffer(7)]],
                                  device const uint *xhash [[buffer(8)]],
                                  uint id [[thread_position_in_grid]]) {
  P q=targets[id/entryCount], b=entries[id%entryCount];
  if(!q.finite || !b.finite || q.x==b.x) {
    P negb=b;
    if(negb.finite && negb.y!=0) negb.y=MOD-negb.y;
    P minus=candidate(q,negb), plus=candidate(q,b);
    flags[2*id]=screen_x(minus.x,minus.finite!=0,bitmap,bitmapBits,coarse,screenMode,xhash);
    flags[2*id+1]=screen_x(plus.x,plus.finite!=0,bitmap,bitmapBits,coarse,screenMode,xhash);
    return;
  }
  ulong inv=power(fsub(b.x,q.x),MOD-2);
  ulong negy=b.y==0 ? 0 : MOD-b.y;
  ulong minusSlope=times(fsub(negy,q.y),inv);
  ulong plusSlope=times(fsub(b.y,q.y),inv);
  ulong minusX=fsub(fsub(times(minusSlope,minusSlope),q.x),b.x);
  ulong plusX=fsub(fsub(times(plusSlope,plusSlope),q.x),b.x);
  flags[2*id]=screen_x(minusX,true,bitmap,bitmapBits,coarse,screenMode,xhash);
  flags[2*id+1]=screen_x(plusX,true,bitmap,bitmapBits,coarse,screenMode,xhash);
}
