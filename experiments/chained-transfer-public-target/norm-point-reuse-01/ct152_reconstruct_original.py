#!/usr/bin/env python3
"""CT152 standalone seeded original q223 source reconstruction; no Rust imports.
Exact arithmetic and audit of the matching original-source constants.
Developer-producer test only; [pcc:unverified].
"""
from math import sqrt, isqrt, ceil
import json
import sys

q=223
MOD=(1<<64)-1
def require(cond,why):
 if not cond: raise ValueError("CT152 rejected: "+why)
def rng_init(seed):
 x=(seed^0x9E3779B97F4A7C15)&MOD
 for _ in range(4): x,n=rng_next(x)
 return x
def rng_next(x):
 x ^= x>>12; x ^= (x<<25)&MOD; x ^= x>>27
 x &=MOD
 return x,(x*0x2545F4914F6CDD1D)&MOD
class RNG:
 def __init__(self,seed):self.s=rng_init(seed)
 def below(self,n):self.s,o=rng_next(self.s);return o%n

c=next(i for i in range(2,q) if pow(i,(q-1)//3,q)!=1)
w=pow(c,(q-1)//3,q);w2=w*w%q
O=(0,0,0);I=(1,0,0)
def add(a,b):return tuple((x+y)%q for x,y in zip(a,b))
def sub(a,b):return tuple((x-y)%q for x,y in zip(a,b))
def neg(a):return tuple(-x%q for x in a)
def mul(a,b):
 a0,a1,a2=a;b0,b1,b2=b
 return ((a0*b0+c*(a1*b2+a2*b1))%q,
         (a0*b1+a1*b0+c*a2*b2)%q,(a0*b2+a1*b1+a2*b0)%q)
def scl(a,n):return tuple(x*n%q for x in a)
def frob(a):return (a[0],a[1]*w%q,a[2]*w2%q)
def inv(a):
 require(a!=O,"field inverse zero")
 ac=frob(a); aa=frob(ac);b=mul(ac,aa);n=mul(a,b)
 require(n[1:]==(0,0),"field inversion norm")
 return scl(b,pow(n[0],-1,q))
def powk(a,n):
 v=I
 while n:
  if n&1:v=mul(v,a)
  a=mul(a,a);n>>=1
 return v
def sqrtk(a):
 if a==O:return O
 y=powk(a,(q**3+1)//4)
 return y if mul(y,y)==a else None
def randk(r):return (r.below(q),r.below(q),r.below(q))
def resnz(u,v):
 d0=sub(u[0],v[0]);d1=sub(u[1],v[1])
 return add(sub(mul(d0,d0),mul(mul(u[1],d0),d1)),mul(u[0],mul(d1,d1)))!=O
def det(m):
 return add(sub(mul(m[0][0],sub(mul(m[1][1],m[2][2]),mul(m[1][2],m[2][1]))),
                mul(m[0][1],sub(mul(m[1][0],m[2][2]),mul(m[1][2],m[2][0])))),
            mul(m[0][2],sub(mul(m[1][0],m[2][1]),mul(m[1][1],m[2][0]))))
class Ec:
 def __init__(self,a2,a4,a6):self.a2,self.a4,self.a6=a2,a4,a6
 def right(self,x):
  x2=mul(x,x)
  return add(add(mul(x2,x),mul(self.a2,x2)),add(mul(self.a4,x),self.a6))
 def on(self,p):return p is None or mul(p[1],p[1])==self.right(p[0])
 def minus(self,p):return None if p is None else (p[0],neg(p[1]))
 def plus(self,p0,p1):
  if p0 is None:return p1
  if p1 is None:return p0
  x0,y0=p0;x1,y1=p1
  if x0==x1:
   if add(y0,y1)==O:return None
   v=add(add(scl(mul(x0,x0),3),mul(scl(self.a2,2),x0)),self.a4)
   lam=mul(v,inv(scl(y0,2)))
  else:lam=mul(sub(y1,y0),inv(sub(x1,x0)))
  xx=sub(sub(sub(mul(lam,lam),self.a2),x0),x1)
  yy=sub(mul(lam,sub(x0,xx)),y0)
  return xx,yy
 def times(self,p,n):
  s=None
  while n:
   if n&1:s=self.plus(s,p)
   p=self.plus(p,p);n>>=1
  return s
 def rand(self,r):
  while True:
   x=randk(r);y=sqrtk(self.right(x))
   if y is not None:return (x,y)
 def order_bsgs(self,r):
  n0=q**3+1;h=int(2*(float(q)**1.5))+2
  p=self.rand(r);s=ceil(sqrt(2*h+1))+1
  baby={}; cur=None
  for b in range(s):
   baby.setdefault(cur,b);cur=self.plus(cur,p)
  target=self.minus(self.times(p,n0-h))
  sp=self.times(p,s);nsp=self.minus(sp)
  hits=[];g=target;a=0
  while a*s<=2*h+s:
   if g in baby:
    m=a*s+baby[g]
    if m<=2*h:hits.append(n0-h+m)
   g=self.plus(g,nsp);a+=1
  return hits[0] if len(set(hits))==1 else None
def prime(n):
 if n<2:return False
 return all(n%i!=0 for i in range(2,isqrt(n)+1))
def validated_source(row):
 require(row['trial']==91, "unexpected seeded selected trial")
 require(row['order']==11_092_292 and row['ell']==2_773_073, "source order changed")
 require(row['a2']==(127,56,199) and row['a4']==(152,35,36)
         and row['a6']==(212,109,150), "source model altered")
 require(row['g']==((162,197,140),(45,11,207)), "generator altered")
 e=Ec(row['a2'],row['a4'],row['a6'])
 require(e.on(row['g']) and e.times(row['g'],row['ell']) is None,
         "selected generator not ell-torsion point on curve")
 require(row['g'] is not None and prime(row['ell']) and row['order']==4*row['ell'],
         "non-prime or malformed order")
 size=q**3;rad=isqrt(4*size)
 require((size+1-rad+row['ell']-1)//row['ell'] == (size+1+rad)//row['ell']==4,
         "group order not unique in Hasse interval")
 return True
def main():
 require(q==223 and c==3 and w==183 and pow(c,(q-1)//3,q)!=1,
         "changed cubic field")
 r=RNG(1^(q<<20)); candidates=[]
 for tr in range(1,101):
  u=[randk(r),randk(r)];u1=[frob(z) for z in u];u2=[frob(z) for z in u1]
  disc=sub(mul(u[1],u[1]),scl(u[0],4))
  if disc==O or not (resnz(u,u1) and resnz(u,u2) and resnz(u1,u2)):continue
  mrows=[[u[0],u[1],I],[u1[0],u1[1],I],[u2[0],u2[1],I]]
  if det(mrows)==O:continue
  qa=add(u[1],u2[1]);qb=add(add(u[0],u2[0]),mul(u[1],u2[1]))
  qc=add(mul(u[1],u2[0]),mul(u2[1],u[0]));qd=mul(u[0],u2[0])
  a2=qb;a4=sub(mul(qa,qc),scl(qd,4))
  a6=add(sub(mul(qc,qc),scl(mul(qb,qd),4)),mul(mul(qa,qa),qd))
  ec=Ec(a2,a4,a6)
  n=ec.order_bsgs(r)
  if n is None or n%4:continue
  ell=n//4
  if not prime(ell):continue
  p2=ec.rand(r)
  if ec.times(p2,n) is not None:continue
  g=None
  for _ in range(50):
   g=ec.times(ec.rand(r),4)
   if g is not None:break
  if g is None or ec.times(g,ell) is not None:continue
  row=dict(trial=tr,order=n,ell=ell,u=u,a2=a2,a4=a4,a6=a6,g=g,p2=p2)
  candidates.append(row)
  break  # first qualified source; quartic continuation is verified separately
 require(len(candidates)==1,"seeded source candidate missing")
 row=candidates[0];validated_source(row)
 if '--self-test-negative' in sys.argv:
  controls=[dict(row,ell=104),dict(row,a6=(213,109,150)),
            dict(row,g=((162,197,140),(45,11,208))),dict(row,trial=90)]
  for i,bad in enumerate(controls):
   try: validated_source(bad)
   except ValueError:continue
   raise RuntimeError("mutated source not rejected: "+str(i))
 payload=dict(schema='ct152-seeded-curve/v1',standing='[pcc:unverified]',
              field=[q,c,w],selected_trial=row['trial'],source_order=row['order'],
              subgroup_order=row['ell'],a2=row['a2'],a4=row['a4'],a6=row['a6'],
              generator=row['g'],second_point=row['p2'],
              negative_controls=4 if '--self-test-negative' in sys.argv else 0)
 print(json.dumps(payload,sort_keys=True,separators=(',',':')))
if __name__=='__main__':main()
