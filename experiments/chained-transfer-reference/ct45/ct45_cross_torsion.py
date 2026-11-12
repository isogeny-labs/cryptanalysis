#!/usr/bin/env python3
"""CT45: independent finite-ring Frobenius Hom census [pcc:unverified]."""
from itertools import product
from math import gcd

P, T1, T2 = 101, -7, -11

def frobenius(t,n):
    return (0,-P%n,1,t%n)

def mm(a,b,n):
    return tuple(sum(a[2*i+j]*b[2*j+k] for j in (0,1))%n
                 for i in (0,1) for k in (0,1))

def determinant(a,n):
    return (a[0]*a[3]-a[1]*a[2])%n

def closed(n,t2=T2):
    ann=[a for a in range(n) if ((t2-T1)*a)%n==0]
    return {tuple(x%n for x in (a,-P*c,c,a+t2*c))
            for a,c in product(ann,repeat=2)}

def brute(n,t2=T2):
    a,b=frobenius(T1,n),frobenius(t2,n)
    return {u for u in product(range(n),repeat=4) if mm(u,a,n)==mm(b,u,n)}

def check(n):
    actual=brute(n)
    assert actual==closed(n)
    assert len(actual)==min(n,4)**2
    assert all(all(4*x%n==0 for x in u) for u in actual)
    units=[u for u in actual if gcd(determinant(u,n),n)==1]
    assert len(units)==({2:3,4:12}.get(n,0))
    if n==4:
        assert sum(determinant(u,n)==3 for u in units)==6
    if n>=8:
        assert not units
        assert all(all(x%(n//4)==0 for x in u) for u in actual)
    print(f'{n}: {len(actual)} intertwiners; {len(units)} invertible [pcc:unverified]')

def main():
    for n in (2,4,8,16):check(n)
    for n in (32,256):
        u=closed(n)
        assert len(u)==16
        assert all(mm(x,frobenius(T1,n),n)==mm(frobenius(T2,n),x,n) for x in u)
        assert all(all(v%(n//4)==0 for v in x) for x in u)
        print(f'{n}: 16 formula-checked; all singular [pcc:unverified]')
    near=brute(8,-15)
    assert len(near)==64
    assert sum(gcd(determinant(x,8),8)==1 for x in near)==48
    for n in (3,5,7,9,25):
        assert brute(n)=={(0,0,0,0)}
    print('CT45 Python PASS: exhaustive and mutated controls [pcc:unverified]')

if __name__=='__main__':main()
