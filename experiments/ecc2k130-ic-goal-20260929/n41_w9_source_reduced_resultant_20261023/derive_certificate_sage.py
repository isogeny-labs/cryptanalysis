"""Ask Sage for an explicit two-generator certificate of redundancy."""
from sage.all import GF, PolynomialRing

S = PolynomialRing(GF(2), names=("z", "u", "v", "w", "t"), order="degrevlex")
z, u, v, w, t = S.gens()
def s3(a, b, c):
    return (1 + (a*b)**2)*c**2 + a*b*c + (a+b)**2
f = s3(z,u,w)
g = s3(w,v,t)
A,B,C = 1+(u*v)**2,u*v,(u+v)**2
D,E,G = 1+(z*t)**2,z*t,(z+t)**2
R = (A*G+C*D)**2+(A*E+B*D)*(B*G+C*E)
I=S.ideal([f,g])
print("in ideal",R in I)
try:
    c=I.lift(R)
    print("lift",c)
    print("verified",c[0]*f+c[1]*g==R)
except Exception as e:
    print("lift error",type(e).__name__,str(e))
print("ideal methods",[n for n in dir(I) if any(k in n for k in ("lift","reduce","syzy","groebner"))])
print("polynomial methods",[n for n in dir(R) if any(k in n for k in ("lift","reduce"))])
try:
    c=R.lift(I)
    print("poly lift",c)
    print("verified",sum(ci*gi for ci,gi in zip(c,(f,g)))==R)
except Exception as e:
    print("poly lift error",type(e).__name__,str(e))
