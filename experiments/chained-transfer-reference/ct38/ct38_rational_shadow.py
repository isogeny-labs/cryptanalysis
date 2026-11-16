#!/usr/bin/env python3
"""CT38: rational-point and tangent indistinguishability of different isogenies.

Standalone finite-field arithmetic; no producer imports. This checks finite
examples, NOT an independent PCC signature or a geometric isogeny proof.
"""
import json
from math import gcd

Q = 101
CURVES = (("E109", 1, 46, 109), ("E113", 44, 21, 113))
N = 109 * 113
K = Q * N
# M1 changes nonzero 7-torsion by [-1]; M0 kills it entirely.
M1, M0 = 1 + K, 1 + 4*K
BAD = 1 + Q

def check(b, msg):
    if not b: raise RuntimeError(msg)

def add(P, R, a):
    if P is None: return R
    if R is None: return P
    x, y = P
    u, v = R
    if x == u and (y + v) % Q == 0: return None
    s = ((3*x*x + a) * pow(2*y, -1, Q)) % Q if x == u else ((v-y) * pow((u-x) % Q, -1, Q)) % Q
    z = (s*s - x - u) % Q
    return (z, (s*(x-z)-y) % Q)

def mul(n, P, a):
    if n < 0:
        return mul(-n, None if P is None else (P[0], (-P[1])%Q), a)
    R = None
    while n:
        if n&1: R = add(R, P, a)
        P = add(P, P, a)
        n //= 2
    return R

def points(a,b):
    xs = {}
    for y in range(Q):
        ys = y*y%Q
        xs.setdefault(ys, []).append(y)
    return [None] + [(x,y) for x in range(Q) for y in xs.get((x*x*x+a*x+b)%Q,())]

def frob_roots_mod7(t):
    return [r for r in range(7) if (r*r-t*r+Q)%7==0]

def run():
    check((N,K,M1,M0,BAD)==(12317,1244017,1244018,4976069,102), "fixture mismatch")
    check(K%Q==0 and K%N==0 and gcd(K, 7)==1, "CRT kernel premise")
    check(M1%7==6 and M0%7==0 and M1%Q==M0%Q==1, "torsion/tangent premise")
    check(M1%N==M0%N==1 and gcd(M1,Q)==gcd(M0,Q)==1, "rational/separable premise")
    out=[]
    for name,a,b,order in CURVES:
        check((4*a*a*a+27*b*b)%Q!=0, "singular curve")
        pts=points(a,b)
        check(len(pts)==order,"point count")
        t=Q+1-order
        roots=frob_roots_mod7(t)
        check(len(roots)==2 and roots[0]!=roots[1],"Frobenius roots distinct")
        check(all(mul(order,P,a) is None for P in pts),"non-torsion rational point")
        for P in pts:
            check(mul(M1,P,a)==P, "M1 rational mismatch")
            check(mul(M0,P,a)==P, "M0 rational mismatch")
        negatives=sum(mul(BAD,P,a)!=P for P in pts)
        check(negatives==order-1,"negative control not sensitive")
        out.append(dict(name=name,points=len(pts),trace=t,roots_mod7=roots,
                        m1_rational_fixed=len(pts),m0_rational_fixed=len(pts),
                        bad_changed=negatives))
    check(out[0]['points']*out[1]['points']==N, "product cardinality")
    check((M1-1)%Q==(M0-1)%Q==0, "differential equality")
    print(json.dumps(dict(project="CT38",field=Q,group_order=N,
        multipliers={"m1":M1,"m0":M0,"bad":BAD},
        residues_mod7={"m1":M1%7,"m0":M0%7},
        rational_product_pairs=N,product_differential="identity",
        product_geometric_7_torsion_order=7**4,
        product_geometric_m0_7_torsion_image_order=1,
        curve_results=out,standing="pcc:unverified"),sort_keys=True))
if __name__ == '__main__':
    run()
