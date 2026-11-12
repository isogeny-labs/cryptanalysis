#!/usr/bin/env python3
"""Independent CT50 polynomial-ring proof over Z[u0,v0,u1,v1,u2,v2]."""
N=6
ZERO=(0,)*N
class ZPoly:
 def __init__(self,c=None):self.d={k:v for k,v in (c or {}).items() if v}
 @staticmethod
 def integer(n):return ZPoly({ZERO:n})
 @staticmethod
 def variable(i):
  k=list(ZERO);k[i]=1
  return ZPoly({tuple(k):1})
 def __add__(self,b):
  if isinstance(b,int):b=ZPoly.integer(b)
  d=self.d.copy()
  for k,v in b.d.items():d[k]=d.get(k,0)+v
  return ZPoly(d)
 def __radd__(self,b):return self+b
 def __neg__(self):return ZPoly({k:-v for k,v in self.d.items()})
 def __sub__(self,b):return self+-b
 def __mul__(self,b):
  if isinstance(b,int):b=ZPoly.integer(b)
  d={}
  for a,av in self.d.items():
   for c,cv in b.d.items():
    k=tuple(x+y for x,y in zip(a,c));d[k]=d.get(k,0)+av*cv
  return ZPoly(d)
 def __rmul__(self,b):return self*b
 def __eq__(self,b):return self.d==(ZPoly.integer(b).d if isinstance(b,int) else b.d)
 def __bool__(self):return bool(self.d)
Z=ZPoly.integer(0)
O=ZPoly.integer(1)
def polymul(a,b):
 out=[Z]*(len(a)+len(b)-1)
 for i,x in enumerate(a):
  for j,y in enumerate(b):out[i+j]=out[i+j]+x*y
 return out
def deriv(a):return [i*a[i] for i in range(1,len(a))]
def bracket(a,b):
 u=polymul(deriv(a),b);v=polymul(a,deriv(b))
 return [x-y for x,y in zip(u,v)][:3]
def det3(rows):
 a,b,c=rows
 s=lambda i,j,k:a[i]*b[j]*c[k]
 return s(0,1,2)+s(1,2,0)+s(2,0,1)-s(2,1,0)-s(1,0,2)-s(0,2,1)
def brs(q):return [bracket(q[(i+1)%3],q[(i+2)%3]) for i in range(3)]
q=[[ZPoly.variable(2*i+1),ZPoly.variable(2*i),O] for i in range(3)]
delta=det3(q)
if not delta:raise RuntimeError('trivial determinant')
h=brs(q)
dh=det3(h)
if dh!=-2*delta*delta:raise RuntimeError('universal reverse determinant identity failed')
hh=brs(h)
if any(hh[i]!=[-2*delta*x for x in q[i]] for i in range(3)):
 raise RuntimeError('universal double-bracket identity failed')
if dh==2*delta*delta:raise RuntimeError('wrong sign control accepted')
if any(hh[i]==[2*delta*x for x in q[i]] for i in range(3)):
 raise RuntimeError('wrong double-bracket sign control accepted')
print('PASS over Z[u0,v0,u1,v1,u2,v2]: det(h)=-2 Delta^2; [h,h]=-2 Delta q; sign mutants rejected')
