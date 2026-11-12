#!/usr/bin/env python3
"""Independent F101^2 zeta and Frobenius J[2] audit for CT49 (no dependencies)."""
P=101
fixtures={
 'T0':([31,75,74,54,71,55,1],[6]),
 'T1':([95,26,19,27,94,91,1],[6]),
 'T2':([95,93,43,39,92,17,1],[6]),
 'Cpi1':([52,0,25,0,77,0,84],[3,3]),
 'Cpi2':([72,0,85,0,14,0,93],[3,3]),
 'C10':([89,0,93,0,8,0,61],[3,3]),
 'C20':([40,0,45,0,75,0,18],[3,3]),
}
def check(b,msg):
 if not b: raise RuntimeError(msg)
def extmul(u,w):
 a,b=u;c,d=w
 return ((a*c+2*b*d)%P,(a*d+b*c)%P)
def extpow(z,n):
 acc=(1,0)
 while n:
  if n&1:acc=extmul(acc,z)
  z=extmul(z,z);n>>=1
 return acc
def evalf(f,z):
 acc=(0,0)
 for c in reversed(f):
  a,b=extmul(acc,z)
  acc=((a+c)%P,b)
 return acc
def char(z):
 if z==(0,0):return 0
 c=extpow(z,(P*P-1)//2)
 check(c in ((1,0),(P-1,0)),'quadratic character not +/-1')
 return 1 if c==(1,0) else -1
def fpchar(a):
 if a%P==0:return 0
 return 1 if pow(a,(P-1)//2,P)==1 else -1
def pointcounts(f):
 n1=1+fpchar(f[-1])
 for x in range(P):n1+=1+fpchar(evalf(f,(x,0))[0])
 n2=2
 for x in range(P):
  for y in range(P):n2+=1+char(evalf(f,(x,y)))
 a=P+1-n1
 b=(n2-P*P-1+a*a)//2
 check((n2-P*P-1+a*a)%2==0,'nonintegral zeta coefficient')
 return n1,n2,P*P+1+b-(P+1)*a
def fixed_classes(blocks):
 p=[];offset=0
 for n in blocks:
  p.extend(offset+(i+1)%n for i in range(n));offset+=n
 check(offset==6,'bad roots')
 orbit=list(range(6))
 for _ in range(3):orbit=[p[i] for i in orbit]
 fixed=0
 for mask in range(64):
  if mask.bit_count()%2 or mask>(mask^63):continue
  newmask=sum(1<<orbit[i] for i in range(6) if mask>>i&1)
  fixed+=min(newmask,newmask^63)==mask
 return fixed
for name,(f,signature) in fixtures.items():
 check(pointcounts(f)==(120,10436,12317),name+' zeta disagrees')
 check(fixed_classes(signature)==(4 if signature==[6] else 16),name+' J[2] disagrees')
 print(name,pointcounts(f),fixed_classes(signature))
# Positive and negative Galois-module controls
check(fixed_classes([3,3])!=fixed_classes([6]),'failed cubic torsion discriminator')
check(fixed_classes([6])==4 and fixed_classes([3,3])==16,'incorrect fixed group')
print('PASS Python: seven two-field exact counts and cubic-extension 2-torsion controls')
