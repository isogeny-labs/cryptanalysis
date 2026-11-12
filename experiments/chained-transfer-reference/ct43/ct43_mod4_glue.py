#!/usr/bin/env python3
"""Independent exhaustive mod-4 Frobenius/Weil pairing graph census."""
from itertools import product
from collections import Counter
from math import gcd
P=101
def F(t,n): return (0,(-P)%n,1,t%n)
def mm(A,B,n):
    return tuple(sum(A[2*i+k]*B[2*k+j] for k in (0,1))%n for i in (0,1) for j in (0,1))
def act(A,v,n): return ((A[0]*v[0]+A[1]*v[1])%n,(A[2]*v[0]+A[3]*v[1])%n)
def determinant(A,n): return (A[0]*A[3]-A[1]*A[2])%n
def intertwine(n,t=-11):
    A,B=F(-7,n),F(t,n)
    return [U for U in product(range(n),repeat=4)
            if gcd(determinant(U,n),n)==1 and mm(U,A,n)==mm(B,U,n)]
def wedge(v,w,n): return (v[0]*w[1]-v[1]*w[0])%n
def graph(U):
    n=4; A,B=F(-7,n),F(-11,n)
    V=list(product(range(n),repeat=2))
    G={(v,act(U,v,n)) for v in V}
    assert len(G)==16
    assert all((act(A,v,n),act(B,w,n)) in G for v,w in G)
    return Counter((wedge(v,v2,n)+wedge(w,w2,n))%n for v,w in G for v2,w2 in G)
def main():
    u2,u4,u8=(intertwine(n) for n in (2,4,8))
    assert len(u2)==3 and len(u4)==12 and len(u8)==0
    d=Counter(determinant(U,4) for U in u4)
    assert d==Counter({1:6,3:6})
    assert F(-7,4)==F(-11,4)==(0,3,1,1)
    I=(1,0,0,1); f=F(-7,4); U0=(1,2,2,3)
    assert U0==tuple((I[i]+2*f[i])%4 for i in range(4))
    power=I; orbit=[]
    for _ in range(6):
        orbit.append(mm(U0,power,4))
        power=mm(power,f,4)
    assert power==I
    anti={U for U in u4 if determinant(U,4)==3}
    assert set(orbit)==anti
    for U in u4:
        sums=graph(U)
        assert (sums==Counter({0:256}))==(U in anti)
    pairs={tuple(sorted((U,tuple(-z%4 for z in U)))) for U in anti}
    assert len(pairs)==3
    assert not intertwine(4,-10)
    assert (-7)%8 != (-11)%8
    print("CT43 Python PASS [pcc:unverified]")
    print("invertible intertwiners 2,4,8:",len(u2),len(u4),len(u8))
    print("mod4 determinants:",dict(sorted(d.items())))
    print("anti-isometries:",len(anti),"mod signs:",len(pairs))
    print("all six graph size/isotropy/Frobenius checks: 16/256 PASS")
    print("anti orbit:",orbit)
    print("negative wrong trace: 0; mod8 trace: 1 vs 5")
if __name__=="__main__": main()
