#!/usr/bin/env python3
"""CT48: independent exact 2-primary Smith valuations of a Frobenius intertwiner.
Public synthetic curves; producer-authored checks, [pcc:unverified].
"""
from itertools import combinations, product

P = 101

def demand(ok, reason):
    if not ok:
        raise ArithmeticError(reason)

def v2(n):
    if not n:
        raise ArithmeticError('zero valuation undefined')
    return (abs(n) & -abs(n)).bit_length()-1

def mul(a,b,m):
    return ((a[0]*b[0]+a[1]*b[2])%m,
            (a[0]*b[1]+a[1]*b[3])%m,
            (a[2]*b[0]+a[3]*b[2])%m,
            (a[2]*b[1]+a[3]*b[3])%m)

def power(t,k,m):
    a=(0,-P%m,1,t%m)
    out=(1,0,0,1)
    while k:
        if k & 1:
            out=mul(out,a,m)
        a=mul(a,a,m)
        k >>= 1
    return out

def commutator(k,m,t0=-7,t1=-11):
    a,b=power(t0,k,m),power(t1,k,m)
    columns=[]
    for j in range(4):
        x=[0,0,0,0];x[j]=1
        bx=mul(b,x,m)
        xa=mul(x,a,m)
        columns.append([(bx[i]-xa[i])%m for i in range(4)])
    return [[columns[j][i] for j in range(4)] for i in range(4)]

def determinant(rows):
    n=len(rows)
    if n==1:return rows[0][0]
    return sum((-1)**j*rows[0][j]*determinant([row[:j]+row[j+1:] for row in rows[1:]])
               for j in range(n))

def smith_valuations(k,t0=-7,t1=-11):
    r=v2(k)
    cap=4*r+18
    mod=1<<cap
    l=commutator(k,mod,t0,t1)
    minima=[0]
    for h in range(1,5):
        smallest=cap
        for rs in combinations(range(4),h):
            for cs in combinations(range(4),h):
                det=determinant([[l[i][j] for j in cs] for i in rs]) % mod
                if det:
                    smallest=min(smallest,v2(det))
        demand(smallest<cap,f'bound too small, k={k} h={h}')
        minima.append(smallest)
    return [minima[i]-minima[i-1] for i in range(1,5)]

def expected(k):
    r=v2(k)
    return [0,0,r+2,r+2] if k%3 else [r+2,r+2,r+3,r+3]

def count_hom(k,s):
    return 1<<sum(min(s,a) for a in expected(k))

def brute_hom(k,s):
    mod=1<<s
    l=commutator(k,mod)
    count=0
    for x in product(range(mod),repeat=4):
        if all(sum(row[j]*x[j] for j in range(4))%mod==0 for row in l):
            count+=1
    return count

def main():
    cases=sorted(set(range(1,97))|{2**r for r in range(17)}|{3*2**r for r in range(17)}
                 |{5*2**r for r in range(10)}|{15*2**r for r in range(10)})
    for k in cases:
        observed=smith_valuations(k)
        demand(observed==expected(k),f'k={k} observed={observed} expected={expected(k)}')
    brute=0
    for k in (1,2,3,4,6):
        for s in (1,2,3):
            a,b=brute_hom(k,s),count_hom(k,s)
            demand(a==b,f'brute mismatch k={k} s={s}: {a}!={b}')
            brute+=1
    altered=smith_valuations(1,t1=-15)
    demand(altered!=expected(1),f'trace mutant was not detected: {altered}')
    demand(expected(3)==[2,2,3,3], 'k=3 abnormal')
    demand(count_hom(1,8)==16 and count_hom(3,8)==1024,'fixed Hom counts')
    print('CT48 PASS [pcc:unverified]')
    print(f'smith_cases={len(cases)}; full_brute_hom_cases={brute}; trace_mutant_rejected=1')
    print('k=1: smith_2=[0,0,2,2], hom(E[256],F[256])=16')
    print('k=3: smith_2=[2,2,3,3], hom(E[256],F[256])=1024')
    print('all k: k%3 !=0 => [0,0,r+2,r+2]; k%3 ==0 => [r+2,r+2,r+3,r+3]')

if __name__=='__main__':
    main()
