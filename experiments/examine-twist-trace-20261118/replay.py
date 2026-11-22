#!/usr/bin/env python3
"""Exact quadratic-twist trace obstruction audit, toy F_1009; unverified locally."""
import argparse, hashlib, json, math, random
from pathlib import Path
p,a,b,d,r,seed=1009,2,25,11,991,20261118
at,bt=a*d*d%p,b*d**3%p

class Field:
 def __init__(self,ext):self.ext=ext;self.reset()
 def reset(self):self.n=dict(add=0,mul=0,inv=0)
 def val(self,x):return (x%p,0) if self.ext else x%p
 def add(self,x,y):
  if self.ext:
   self.n['add']+=2;return ((x[0]+y[0])%p,(x[1]+y[1])%p)
  self.n['add']+=1;return (x+y)%p
 def neg(self,x):return tuple(-z%p for z in x) if self.ext else -x%p
 def sub(self,x,y):return self.add(x,self.neg(y))
 def mul(self,x,y):
  if self.ext:
   u,v=x;w,z=y
   self.n['mul']+=5;self.n['add']+=2
   return ((u*w+d*v*z)%p,(u*z+v*w)%p)
  self.n['mul']+=1;return x*y%p
 def inv(self,x):
  self.n['inv']+=1
  if not self.ext:
   assert x;return pow(x,p-2,p)
  u,v=x;den=(u*u-d*v*v)%p;assert den
  self.n['mul']+=5;self.n['add']+=1
  q=pow(den,p-2,p);return u*q%p,-v*q%p
 def div(self,x,y):return self.mul(x,self.inv(y))
 def frob(self,x):return (x[0],-x[1]%p) if self.ext else x

class Curve:
 def __init__(self,f,a,b):
  self.f=f;self.a=f.val(a);self.b=f.val(b);self.calls=0
 def neg(self,P):return None if P is None else (P[0],self.f.neg(P[1]))
 def add(self,P,Q):
  self.calls+=1
  if P is None:return Q
  if Q is None:return P
  f=self.f;x,y=P;u,v=Q
  if x==u:
   if v!=y or y==f.val(0):return None
   m=f.div(f.add(f.mul(f.val(3),f.mul(x,x)),self.a),f.mul(f.val(2),y))
  else:m=f.div(f.sub(v,y),f.sub(u,x))
  z=f.sub(f.sub(f.mul(m,m),x),u)
  return z,f.sub(f.mul(m,f.sub(x,z)),y)
 def mul(self,Q,n):
  R=None
  while n:
   if n&1:R=self.add(R,Q)
   n>>=1
   if n:Q=self.add(Q,Q)
  return R
 def on(self,Q):
  if Q is None:return True
  f=self.f;x,y=Q
  return f.mul(y,y)==f.add(f.add(f.mul(f.mul(x,x),x),f.mul(self.a,x)),self.b)
 def reset(self):self.calls=0;self.f.reset()
 def costs(self):return dict(group_calls=self.calls,**self.f.n)

def points(a,b):
 roots={}
 for y in range(p):roots.setdefault(y*y%p,[]).append(y)
 return [None]+[(x,y) for x in range(p) for y in roots.get((x**3+a*x+b)%p,())]

def phi(Q):
 if Q is None:return None
 x,y=Q;return ((d*x%p,0),(0,d*y%p))
def undo(Q):
 if Q is None:return None
 x,y=Q;assert x[1]==0 and y[0]==0
 t=pow(d,p-2,p);return x[0]*t%p,y[1]*t%p
def trace(C,Q):
 return None if Q is None else C.add(Q,(C.f.frob(Q[0]),C.f.frob(Q[1])))
def bsgs(C,G,Q):
 m=math.isqrt(r)+int(math.isqrt(r)**2<r);v=None;tab={}
 for j in range(m):tab.setdefault(v,j);v=C.add(v,G)
 step=C.neg(C.mul(G,m));v=Q
 for i in range(m+1):
  if v in tab:
   k=(i*m+tab[v])%r;assert C.mul(G,k)==Q;return k
  v=C.add(v,step)
 raise AssertionError("DLP failed")
def fac(n):
 f={};k=2
 while k*k<=n:
  while n%k==0:f[k]=f.get(k,0)+1;n//=k
  k+=1
 if n>1:f[n]=f.get(n,0)+1
 return f

def run():
 assert pow(d,(p-1)//2,p)==p-1 and (4*a**3+27*b*b)%p
 src=points(a,b);tw=points(at,bt)
 assert len(src)==r and len(tw)==1029
 assert fac(r)=={991:1} and fac(len(tw))=={3:1,7:3}
 t=p+1-r;n2=(p+1)**2-t*t;assert n2==r*len(tw)
 E=Curve(Field(False),a,b);W=Curve(Field(True),at,bt)
 G=next(x for x in src if x is not None)
 assert G==(0,5) and E.mul(G,r) is None
 images=set()
 for Q in src:
  V=phi(Q);assert W.on(V) and trace(W,V) is None
  if V is not None:assert (W.f.frob(V[0]),W.f.frob(V[1]))==W.neg(V)
  assert undo(V)==Q;images.add(V)
 assert len(images)==r
 rational={None}|{((x,0),(y,0)) for Q in tw if Q is not None for x,y in [Q]}
 assert images.intersection(rational)=={None}
 H=((3,0),(76,0));Gt=phi(G)
 assert W.mul(H,1029) is None
 assert W.mul(H,343) is not None and W.mul(H,147) is not None
 assert trace(W,H)==W.mul(H,2) and W.mul(Gt,r) is None
 S=W.add(H,Gt);assert W.mul(S,n2) is None
 assert all(W.mul(S,n2//j) is not None for j in (3,7,r))
 for j in range(1029):
  P=W.mul(H,j)
  assert W.mul(trace(W,P),515)==P
 W.reset();v=trace(W,H);tc=W.calls
 W.reset();assert W.mul(v,515)==H;ic=W.calls
 rng=random.Random(seed)
 for _ in range(1024):
  i,j=rng.randrange(r),rng.randrange(r)
  A1,B1=E.mul(G,i),E.mul(G,j)
  assert phi(E.add(A1,B1))==W.add(phi(A1),phi(B1))
 scalars=[0,1,r-1]
 while len(scalars)<64:
  k=rng.randrange(r)
  if k not in scalars:scalars.append(k)
 rows=[]
 for k in scalars:
  Q=E.mul(G,k)
  E.reset();assert bsgs(E,G,Q)==k;dc=E.costs()
  W.reset();assert bsgs(W,Gt,phi(Q))==k;mc=W.costs()
  assert undo(W.mul(Gt,k))==Q
  rows.append(dict(k=k,direct=dc,lifted=mc))
 totals={arm:{key:sum(row[arm][key] for row in rows)
         for key in ('group_calls','add','mul','inv')} for arm in ('direct','lifted')}
 assert totals['direct']['group_calls']==totals['lifted']['group_calls']
 assert totals['lifted']['mul']>totals['direct']['mul']
 assert totals['lifted']['inv']==totals['direct']['inv']
 return dict(schema="examine.quadratic-twist/v1",seed=seed,
  parameters=dict(p=p,a=a,b=b,nonsquare=d,twist_a=at,twist_b=bt,
   source_order=r,twist_order=1029,extension_order=n2,trace=t,
   trace_projection_kernel=r,trace_projection_image=1029,
   source_order_factors=fac(r),twist_order_factors=fac(1029),
   extension_factors=fac(n2),generator=G),
  counts=dict(full_source_points_checked=r,twist_points_counted=1029,
   homomorphism_pairs=1024,inverses_checked=r,distinct_images=len(images),
   intersection_twist_rational=1,rational_twist_full_order_generator=[3,76],
   extension_full_order_generator_certified=True,trace_image_order=1029,
   trace_kernel_order=r,trace_rational_inverse_checks=1029,dlps=len(rows)),
  costs=dict(algorithm="affine BSGS same scalar/loop both arms",
   totals=totals,source_to_twist_map_base_mul_per_point=2,
   twist_to_source_inverse_base_mul_per_point=2,
   mapped_generator_one_time_base_mul=2,mapped_queries_base_mul=128,
   trace_projection_group_calls=tc,trace_rational_inverse_group_calls=ic,
   rho_heuristic_expected_group_ops=math.sqrt(math.pi*r/2)),
  obligations=dict(source_subgroup="PASS",extension_group_order="PASS",
   twist_rational_count="PASS",kernel_image="PASS",
   frob_anti_and_zero_trace="PASS",inverse_on_image="PASS",
   trace_rational_inverse="PASS",trace_global_inverse="FAIL",
   log_recovery="PASS",smooth_target_transfer="FAIL",
   strict_total_cost_improvement="FAIL",independent_signed_pcc="PENDING"),
  samples=rows)

if __name__=="__main__":
 parser=argparse.ArgumentParser()
 parser.add_argument('--out');parser.add_argument('--verify-json')
 args=parser.parse_args()
 result=run();raw=json.dumps(result,sort_keys=True,indent=2)+"\n"
 if args.verify_json:assert Path(args.verify_json).read_text()==raw
 if args.out:Path(args.out).write_text(raw)
 print(json.dumps({k:result[k] for k in ('parameters','counts','costs','obligations')},sort_keys=True))
 print('canonical_sha256',hashlib.sha256(raw.encode()).hexdigest())
