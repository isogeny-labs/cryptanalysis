#!/usr/bin/env python3
"""CT30: independent geometric 7-kernel and Frobenius oracle, F_101 only.
No producer code, SymPy or cloud use. Standing [pcc:unverified].
"""
P=101
CASES=(
 ('E109 forward',26,58,(99,94,75,1),109,5),
 ('E109 backtrack',26,58,(58,26,58,1),109,2),
 ('E113 forward',69,50,(53,19,40,1),113,6),
 ('E113 backtrack',69,50,(29,88,45,1),113,4),
)
def poly(v):
 v=list(v)
 while len(v)>1 and v[-1]%P==0:v.pop()
 return tuple(t%P for t in (v or [0]))
def add(a,b):
 return poly([(a[i] if i<len(a) else 0)+(b[i] if i<len(b) else 0) for i in range(max(len(a),len(b)))])
def mul(a,b):
 z=[0]*(len(a)+len(b)-1)
 for i,x in enumerate(a):
  for j,y in enumerate(b):z[i+j]+=x*y
 return poly(z)
def scale(a,v):return poly([v*x for x in a])
def neg(a):return scale(a,-1)
def sub(a,b):return add(a,neg(b))
def power(a,n):
 z=(1,)
 while n:
  if n&1:z=mul(z,a)
  a=mul(a,a);n//=2
 return z
def remainder(a,h):
 a=poly(a);h=poly(h)
 if h==(0,):raise ZeroDivisionError('division by zero polynomial')
 inv=pow(h[-1],-1,P)
 while a!=(0,) and len(a)>=len(h):
  shift=len(a)-len(h); factor=a[-1]*inv%P
  a=sub(a,(0,)*shift+scale(h,factor))
 return a
def evaluate(a,x):
 z=0
 for c in reversed(a):z=(z*x+c)%P
 return z
def count(a,b):
 squares={y*y%P for y in range(P)}
 return 1+sum(1 if (x**3+a*x+b)%P==0 else
              2 if (x**3+a*x+b)%P in squares else 0 for x in range(P))
def psi7(a,b):
 # Standard division-polynomial recurrence on y²=x³+ax+b:
 # psi3=3x⁴+6ax²+12bx-a², psi4=4y B,
 # psi5=psi4*psi2³-psi3³=32 f² B-psi3³,
 # psi7=psi5*psi3³-psi2*psi4³=psi5*psi3³-128 f² B³.
 f=(b,a,0,1);psi3=poly((-a*a,12*b,6*a,0,3))
 B=poly((-8*b*b-a**3,-4*a*b,-5*a*a,20*b,5*a,0,1))
 f2=power(f,2);psi3cube=power(psi3,3)
 return sub(mul(sub(scale(mul(f2,B),32),psi3cube),psi3cube),
            scale(mul(f2,power(B,3)),128))
def norm_cubic(h,f):
 # det_Fp(multiplication by f(alpha) on Fp[alpha]/(h)).
 cols=[]
 for j in range(3):
  r=remainder(mul(f,(0,)*j+(1,)),h)
  cols.append(list(r)+[0]*(3-len(r)))
 A=[[cols[j][i] for j in range(3)] for i in range(3)]
 return (A[0][0]*(A[1][1]*A[2][2]-A[1][2]*A[2][1])
         -A[0][1]*(A[1][0]*A[2][2]-A[1][2]*A[2][0])
         +A[0][2]*(A[1][0]*A[2][1]-A[1][1]*A[2][0]))%P
def check(ok,*why):
 if not ok:raise RuntimeError(str(why))
def main():
 orders=[]
 for name,a,b,h,N,expected in CASES:
  check(count(a,b)==N,name,'point order')
  t=P+1-N;f=(b,a,0,1)
  eigen=[z for z in range(7) if (z*z-t*z+P)%7==0]
  check(len(eigen)==2,name,'Frobenius roots')
  check({pow(z,3,7) for z in eigen}=={1,6},name,'cannot isolate eigenspaces via Frobenius cubing')
  psi=psi7(a,b)
  check(len(psi)==25 and psi[-1]==7,name,'psi7 degree/lead')
  check(remainder(psi,h)==(0,),name,'kernel not dividing psi7')
  check(remainder(psi,((h[0]+1)%P,)+h[1:])!=(0,),name,'wrong-kernel control')
  roots=[r for r in range(P) if evaluate(h,r)==0]
  if not roots:
   # Cubic without Fp root is irreducible.
   norm=norm_cubic(h,f);chi=pow(norm,(P-1)//2,P)
   check(chi in (1,P-1),name,'unexpected 2-torsion')
   pick=[z for z in eigen if pow(z,3,7)==(1 if chi==1 else 6)]
   evidence=f'irreducible h, Norm(f(alpha))={norm}, Legendre={chi}'
  else:
   check(len(roots)==3,name,'unhandled cubic factorization',roots)
   chars=[pow(evaluate(f,r),(P-1)//2,P) for r in roots]
   check(len(set(chars))==1 and chars[0] in (1,P-1),name,'y characters',chars)
   pick=[z for z in eigen if z==(1 if chars[0]==1 else 6)]
   evidence=f'rational x={roots}, Legendre values={chars}'
  check(len(pick)==1 and pick[0]==expected,name,'eigenvalue',pick,evidence)
  deg=next(j for j in range(1,7) if pow(expected,j,7)==1)
  orders.append(deg)
  print(name,f'pointcount={N} t={t} eig={expected} splitting_degree={deg}',
        evidence,'division polynomial and mutated-kernel checks pass [pcc:unverified]')
 check(orders==[6,3,2,3],'unexpected field degrees',orders)
 print('Four geometric kernel checks passed [pcc:unverified]')
if __name__=='__main__':main()
