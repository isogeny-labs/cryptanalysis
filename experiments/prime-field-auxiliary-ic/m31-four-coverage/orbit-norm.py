"""Derive the five public quotient maps and check the norm against both panels."""
from pathlib import Path
import subprocess
import sys

p = 2**31 - 1
def shift(f, t):
    a,b,c,d = f
    return tuple(v % p for v in (a,b+3*a*t,c+2*b*t+3*a*t*t,d+c*t+b*t*t+a*t**3))

def norm(f, B):
    a,b,c,d = f
    h = a*d
    j = a*c*B+b*d
    return tuple(v % p for v in (h,j,a*b*B**2+b*c*B+c*d-3*B*h,
                                  a*a*B**3+b*b*B**2+c*c*B+d*d-2*B*j))

def eval_poly(f,x):
    a,b,c,d=f
    return ((a*x+b)*x*x+c*x+d)%p

def quotient(x, t, A, B):
    u=(x-t)%p
    if not u: raise ValueError("point lies in quotient kernel")
    return (u+A+B*pow(u,-1,p))%p

gp = """p=2^31-1; E=ellinit([1,0],p); G=[Mod(3,p),Mod(615668188,p)]; K=ellmul(E,G,2^26);
forstep(j=4,0,-1,print(lift(ellmul(E,K,2^j)[1])))
"""
kernels=list(map(int,subprocess.check_output(['gp','-fq'], input=gp,text=True).split()))
assert len(kernels)==5
f=(1,0,2,14)
a2,a4=0,1
maps=[]
for k in kernels:
    t=k
    for m in maps: t=quotient(t,*m)
    assert (t**3+a2*t*t+a4*t)%p==0
    A,B=(3*t+a2)%p,(3*t*t+2*a2*t+a4)%p
    assert B
    f=shift(norm(shift(f,t),B),-A)
    maps.append((t,A,B))
    a2,a4=-2*A%p,(A*A-4*B)%p
print("maps",maps,"cubic",f)
for panel in sys.argv[1:]:
    vals=[tuple(map(int,l.split())) for l in Path(panel).read_text().splitlines()]
    assert len(vals)==32768
    odd=0
    for off in range(0,len(vals),32):
        row=vals[off:off+32]
        xs=[x for x,_ in row]
        product=1
        for x in xs: product=product*eval_poly((1,0,2,14),x)%p
        for m in maps:
            reduced=[quotient(x,*m) for x in xs]
            half=len(xs)//2
            t,_,B=m
            assert all((xs[i]-t)*(xs[i+half]-t)%p==B for i in range(half))
            assert reduced[:half]==reduced[half:]
            xs=reduced[:half]
        assert len(xs)==1 and product==eval_poly(f,xs[0])
        sign=pow(product,p//2,p)
        assert sign==(p-1 if sum(1-b for _,b in row)%2 else 1)
        odd+=sign==p-1
    print(Path(panel).name,len(vals)//32,odd)
