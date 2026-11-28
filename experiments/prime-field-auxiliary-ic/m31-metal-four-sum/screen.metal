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
kernel void compact_screen(device const P *targets [[buffer(0)]], device const P *entries [[buffer(1)]],
                           device const ulong *bitmap [[buffer(2)]], device uchar *flags [[buffer(3)]],
                           constant uint &entryCount [[buffer(4)]],
                           constant uint &bitmapBits [[buffer(5)]], uint id [[thread_position_in_grid]]) {
  uint width=2*entryCount;
  P q=targets[id/width], b=entries[(id/2)%entryCount];
  if(!(id&1u) && b.finite && b.y!=0) b.y=MOD-b.y;
  P result=candidate(q,b);
  if(!result.finite) { flags[id]=2; return; }
  ulong bit=(result.x*0x9e3779b97f4a7c15ul)>>(64-bitmapBits);
  flags[id]=((bitmap[bit>>6]>>(bit&63))&1ul) ? 1 : 0;
}
