#!/usr/bin/env python3
"""CT35 independent F101 operation counts. No CT33/34 imports.
Development audit only: [pcc:unverified].
"""
import json
from collections import Counter
from math import isqrt
P=101
CASES=[
 dict(tag='E109',a=1,b=46,n=109,mid=(26,58),end=(59,27),
      h0=(72,100,35,1),h1=(99,94,75,1)),
 dict(tag='E113',a=44,b=21,n=113,mid=(69,50),end=(23,7),
      h0=(59,46,8,1),h1=(53,19,40,1))]
class Meter:
 def __init__(self):self.c=Counter()
 def add(self,a,b):self.c['fp_add']+=1;return(a+b)%P
 def sub(self,a,b):self.c['fp_add']+=1;return(a-b)%P
 def mul(self,a,b):self.c['fp_mul']+=1;return(a*b)%P
 def inv(self,a):
  if a%P==0:raise ZeroDivisionError('zero denominator')
  self.c['fp_inv']+=1;return pow(a,-1,P)
 def snap(self):return {v:self.c[v] for v in ('fp_add','fp_mul','fp_inv')}
class Silent:
 @staticmethod
 def add(a,b):return(a+b)%P
 @staticmethod
 def sub(a,b):return(a-b)%P
 @staticmethod
 def mul(a,b):return(a*b)%P
 @staticmethod
 def inv(a):return pow(a,-1,P)
Z=Silent()
def norm(a):
 a=[v%P for v in a]
 while len(a)>1 and a[-1]==0:a.pop()
 return a or [0]
def padd(a,b,m):
 return norm([m.add(a[i] if i<len(a) else 0,b[i] if i<len(b) else 0) for i in range(max(len(a),len(b)))])
def psub(a,b,m):
 return norm([m.sub(a[i] if i<len(a) else 0,b[i] if i<len(b) else 0) for i in range(max(len(a),len(b)))])
def pscale(a,k,m):return norm([m.mul(c,k) for c in a])
def pmul(a,b,m):
 out=[0]*(len(a)+len(b)-1)
 for i,c in enumerate(a):
  for j,d in enumerate(b):out[i+j]=m.add(out[i+j],m.mul(c,d))
 return norm(out)
def pder(a,m):return norm([m.mul(a[i],i) for i in range(1,len(a))])
def psq(a,m):return pmul(a,a,m)
def velu(a,b,h,m):
 f=[b,a,0,1]
 dh=pder(h,m);d2h=pder(dh,m);df=pder(f,m)
 hh=psq(h,m);s1=(-h[-2])%P
 left=pmul([(-2*s1)%P,2*(len(h)-1)+1],hh,m)
 right=pscale(pmul(pmul(df,dh,m),h,m),2,m)
 corr=pscale(pmul(f,psub(psq(dh,m),pmul(h,d2h,m),m),m),4,m)
 return padd(psub(left,right,m),corr,m)
def pull(h,N,D,m):
 degree=len(h)-1;ns=[[1]];ds=[[1]]
 for i in range(degree):
  ns.append(pmul(ns[-1],N,m));ds.append(pmul(ds[-1],D,m))
 result=[0]
 for i,c in enumerate(h):result=padd(result,pscale(pmul(ns[i],ds[degree-i],m),c,m),m)
 return result
def paired_horner(f,x,m):
 value=f[-1];prime=0
 for c in reversed(f[:-1]):
  prime=m.add(m.mul(prime,x),value)
  value=m.add(m.mul(value,x),c)
 return value,prime
def map_with_kernel(Q,N,K,m):
 if Q is None:return None
 x,y=Q
 nv,nd=paired_horner(N,x,m);kv,kd=paired_horner(K,x,m)
 iv=m.inv(kv);iv2=m.mul(iv,iv);iv3=m.mul(iv2,iv)
 xx=m.mul(nv,iv2)
 num=m.sub(m.mul(nd,kv),m.mul(m.mul(2,nv),kd))
 yy=m.mul(m.mul(y,num),iv3)
 return xx,yy
def point_add(A,B,a,m):
 if A is None:return B
 if B is None:return A
 x,y=A;u,v=B
 if x==u and m.add(y,v)==0:return None
 if A==B:
  if y==0:return None
  numer=m.add(m.mul(3,m.mul(x,x)),a);denom=m.mul(2,y)
 else:
  numer=m.sub(v,y);denom=m.sub(u,x)
 slope=m.mul(numer,m.inv(denom))
 xx=m.sub(m.sub(m.mul(slope,slope),x),u)
 yy=m.sub(m.mul(slope,m.sub(x,xx)),y)
 return xx,yy
def mulpt(Q,k,a,m):
 R=None
 while k:
  if k&1:R=point_add(R,Q,a,m)
  Q=point_add(Q,Q,a,m);k>>=1
 return R
def negate(Q):return(Q[0],(-Q[1])%P) if Q else None
def all_points(a,b):
 sqroots={}
 for y in range(P):sqroots.setdefault(y*y%P,[]).append(y)
 return [None]+[(x,y) for x in range(P) for y in sqroots.get((x*x*x+a*x+b)%P,())]
def bsgs(B,Q,n,a,m):
 width=isqrt(n)+1;baby={};R=None
 for j in range(width):
  baby.setdefault(R,j);R=point_add(R,B,a,m)
 step=negate(mulpt(B,width,a,m));R=Q
 for i in range(width+1):
  if R in baby:
   k=(i*width+baby[R])%n
   if mulpt(B,k,a,m)==Q:return k
  R=point_add(R,step,a,m)
 raise RuntimeError('BSGS failed')
def run_case(c):
 a,b,n=c['a'],c['b'],c['n'];h0=list(c['h0']);h1=list(c['h1'])
 first_setup=Meter();N0=velu(a,b,h0,first_setup);N1=velu(*c['mid'],h1,first_setup)
 direct_setup=Meter();N0check=velu(a,b,h0,direct_setup)
 if N0check!=N0:raise AssertionError('first map mismatch')
 H=pull(h1,N0,psq(h0,direct_setup),direct_setup)
 K=pmul(h0,H,direct_setup);N49=velu(a,b,K,direct_setup)
 if not(len(K)==25 and len(H)==22 and len(N49)==50):raise AssertionError('kernel degree')
 src=all_points(a,b);dst=all_points(*c['end'])
 if len(src)!=n or len(dst)!=n:raise AssertionError('curve order')
 mapped={};setdst=set(dst);direct_eval=Meter();chain_eval=Meter()
 for q in src:
  direct=map_with_kernel(q,N49,K,direct_eval)
  chain=map_with_kernel(map_with_kernel(q,N0,h0,chain_eval),N1,h1,chain_eval)
  if direct!=chain or direct not in setdst:raise AssertionError(('maps',q,direct,chain))
  mapped[q]=direct
 G=src[1];T=mapped[G];bad=N49.copy();bad[-2]=(bad[-2]+1)%P
 controls={
  'bad_direct_numerator_rejected':any(map_with_kernel(q,bad,K,Z)!=mapped[q] for q in src[1:]),
  'wrong_dest_curve_rejected':any((v[1]*v[1]-v[0]**3-c['end'][0]*v[0]-(c['end'][1]+1))%P!=0 for v in mapped.values() if v is not None)}
 if not all(controls.values()):raise AssertionError('mutation not rejected')
 seen=set();src_cost=Meter();direct49=Meter();chain77=Meter()
 for k in range(n):
  q=mulpt(G,k,a,Z)
  if q in seen:raise AssertionError('duplicate generator multiple')
  seen.add(q)
  if bsgs(G,q,n,a,src_cost)!=k:raise AssertionError('source DLP')
  q49=map_with_kernel(q,N49,K,direct49)
  g49=map_with_kernel(G,N49,K,direct49)
  if (q49,g49)!=(mapped[q],T):raise AssertionError('49 map')
  if bsgs(g49,q49,n,c['end'][0],direct49)!=k:raise AssertionError('49 DLP')
  q77=map_with_kernel(map_with_kernel(q,N0,h0,chain77),N1,h1,chain77)
  g77=map_with_kernel(map_with_kernel(G,N0,h0,chain77),N1,h1,chain77)
  if (q77,g77)!=(mapped[q],T):raise AssertionError('77 map')
  if bsgs(g77,q77,n,c['end'][0],chain77)!=k:raise AssertionError('77 DLP')
 single49=Meter();single77=Meter();q=src[1]
 map_with_kernel(q,N49,K,single49)
 map_with_kernel(map_with_kernel(q,N0,h0,single77),N1,h1,single77)
 return dict(case=c['tag'],n=n,all_points_mapped=n,verified_cold_DLPs_each=n,
  source_curve=[a,b],dest_curve=list(c['end']),kernel_pairs=24,
  one_nonzero_map_direct49=single49.snap(),one_nonzero_map_7plus7=single77.snap(),
  setup_7plus7_from_h0h1=first_setup.snap(),setup_direct49_from_h0h1=direct_setup.snap(),
  cold_all_direct_BSGS=src_cost.snap(),cold_all_49_transfer_plus_BSGS=direct49.snap(),
  cold_all_7plus7_transfer_plus_BSGS=chain77.snap(),
  negative_controls=controls,no_speedup_claim=True,standing='pcc:unverified')
if __name__=='__main__':
 for c in CASES:print(json.dumps(run_case(c),sort_keys=True))
 print('CT35 PASS [pcc:unverified]')
