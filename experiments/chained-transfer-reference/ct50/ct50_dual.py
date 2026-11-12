#!/usr/bin/env python3
"""CT50 independent exact bidual Richelot equations on four F101 sources.
Does not evaluate divisor maps or certify a DLP speedup. [pcc:unverified]
"""
P=101
DATA={
'Cpi1':([3,26,3], [52,0,25,0,77,0,84], [50,51], [[46,8,49,99,4,78,54],[46,93,49,2,4,23,54]]),
'Cpi2':([3,-3,18], [72,0,85,0,14,0,93], [81,20], [[77,81,100,16,0,40,71],[77,20,100,85,0,61,71]]),
'C10':([-38,-16,7], [89,0,93,0,8,0,61], [73,28], [[49,17,85,87,33,9,10],[49,84,85,14,33,92,10]]),
'C20':([3,46,24], [40,0,45,0,75,0,18], [34,67], [[25,98,69,38,52,39,76],[25,3,69,63,52,62,76]])}
def ok(v,s):
 if not v:raise RuntimeError(s)
class Field:
 def __init__(self,c):self.c=c;self.z=(0,0,0);self.o=(1,0,0)
 def n(self,x):return (x%P,0,0)
 def add(self,a,b):return tuple((x+y)%P for x,y in zip(a,b))
 def neg(self,a):return tuple(-x%P for x in a)
 def sub(self,a,b):return self.add(a,self.neg(b))
 def mul(self,a,b):
  z=[0]*5
  for i in range(3):
   for j in range(3):z[i+j]=(z[i+j]+a[i]*b[j])%P
  for i in [4,3]:
   for j in range(3):z[i-3+j]=(z[i-3+j]-z[i]*self.c[j])%P
  return tuple(z[:3])
 def pow(self,a,k):
  z=self.o
  while k:
   if k&1:z=self.mul(z,a)
   a=self.mul(a,a);k>>=1
  return z
 def poly(self,a,b):
  z=[self.z]*(len(a)+len(b)-1)
  for i,x in enumerate(a):
   for j,y in enumerate(b):z[i+j]=self.add(z[i+j],self.mul(x,y))
  return z
 def deriv(self,a):return [self.mul(self.n(i),x) for i,x in enumerate(a)][1:]
 def br(self,a,b):
  v=self.poly(self.deriv(a),b);w=self.poly(a,self.deriv(b))
  return [self.sub(x,y) for x,y in zip(v,w)][:3]
 def det(self,q):
  a,b,c=q;M=self.mul
  v=lambda i,j,k:M(M(a[i],b[j]),c[k])
  return self.sub(self.add(self.add(v(0,1,2),v(1,2,0)),v(2,0,1)),self.add(self.add(v(2,1,0),v(1,0,2)),v(0,2,1)))
 def brackets(self,q):return [self.br(q[(i+1)%3],q[(i+2)%3]) for i in range(3)]
 def product(self,q):
  z=[self.o]
  for row in q:z=self.poly(z,row)
  return z
 def down(self,a):
  ok(all(x[1]==x[2]==0 for x in a),'bad F101 descent')
  return [x[0] for x in a]
def stable_matchings(cycles):
 p=[];j=0
 for n in cycles:p.extend(j+(i+1)%n for i in range(n));j+=n
 def pairs(unused):
  if not unused:yield ()
  else:
   a=unused[0]
   for b in unused[1:]:
    for tail in pairs(tuple(x for x in unused[1:] if x!=b)):yield ((a,b),)+tail
 canon=lambda m:tuple(sorted(tuple(sorted(x)) for x in m))
 allp={canon(t) for t in pairs(tuple(range(6)))}
 return {m for m in allp if canon((p[a],p[b]) for a,b in m)==m}
def main():
 src=stable_matchings((3,3));dst=stable_matchings((6,))
 ok(len(src)==3 and dst=={((0,3),(1,4),(2,5))},'rational kernel count')
 for name,(g,f,ds,targets) in DATA.items():
  F=Field(g);M=F.mul; t=(0,1,0);r=[F.pow(t,P**i) for i in range(3)]
  ok(F.pow(t,P**3)==t and len(set(r))==3,'bad cubic field')
  for s in [0,1,2]:
   q=[]
   for i,a in enumerate(r):
    b=r[(i+s)%3];q.append([F.neg(M(a,b)),F.sub(b,a),F.o])
   d=F.det(q)
   if s==0:ok(d==F.z,'even pairing not degenerate');continue
   ok(d==F.n(ds[s-1]),'unexpected determinant')
   h=F.brackets(q);lc=F.n(f[6]);norm=F.pow(M(lc,F.pow(d,3)),P**3-2)
   first=F.down([M(x,norm) for x in F.product(h)])
   ok(first==targets[s-1],'wrong first codomain')
   dh=F.det(h);ok(dh==M(F.n(-2),M(d,d)),'wrong dual determinant')
   hh=F.brackets(h);mult=M(F.n(-2),d)
   ok(all(hh[i]==[M(mult,x) for x in q[i]] for i in range(3)),'wrong bidual factors')
   back=F.pow(M(norm,F.pow(dh,3)),P**3-2)
   ok(F.down([M(x,back) for x in F.product(hh)])==f,'double dual not exact')
   bad=F.pow(M(norm,F.pow(dh,2)),P**3-2)
   ok(F.down([M(x,bad) for x in F.product(hh)])!=f,'bad exponent escaped')
   print(f'{name} shift{s} delta={d[0]} dual_delta={dh[0]} dual_equation=exact')
 print('PASS 8 exact bidual equations; unique rational target kernel; 8 bad-exponent controls [pcc:unverified]')
if __name__=='__main__':main()
