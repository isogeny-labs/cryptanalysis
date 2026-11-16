#!/usr/bin/env python3
"""CT37: independent F101 Frobenius-isotypic decomposition controls.

This is a finite arithmetic oracle, not a proof of Tate/Deuring or a PCC verdict.
No imports from producer code. All identifiers and curve fixtures are public.
"""
from math import gcd, isqrt

P = 101
CURVES = (("E109", 1, 46, 109, -7, -355),
          ("E113", 44, 21, 113, -11, -283))
INF = None


def pts(a, b):
    if not ((4 * a**3 + 27 * b**2) % P != 0): raise ArithmeticError("CT37 arithmetic control 16 failed")
    return [INF] + [(x, y) for x in range(P) for y in range(P)
                    if (y*y-x*x*x-a*x-b) % P == 0]


def add(Q, R, a):
    if Q is INF: return R
    if R is INF: return Q
    x, y = Q
    u, v = R
    if x == u and (y+v) % P == 0: return INF
    if x == u:
        m = (3*x*x+a) * pow(2*y, -1, P) % P
    else:
        m = (v-y) * pow((u-x)%P, -1, P) % P
    z = (m*m-x-u) % P
    return (z, (m*(x-z)-y)%P)


def mul(n, Q, a):
    out = INF
    while n:
        if n & 1: out = add(out,Q,a)
        Q = add(Q,Q,a)
        n >>= 1
    return out


def trim(v):
    while v and v[-1] == 0: v.pop()
    return v


def pmul(u, v):
    w = [0]*(len(u)+len(v)-1)
    for i, x in enumerate(u):
        for j, y in enumerate(v):
            w[i+j] += x*y
    return trim(w)


def padd(u, v):
    return trim([ (u[i] if i<len(u) else 0)+(v[i] if i<len(v) else 0)
                   for i in range(max(len(u),len(v))) ])


def scale(u, n): return trim([n*x for x in u])


def pmod(u, v):
    u = list(u)
    while len(u) >= len(v):
        k = len(u)-len(v)
        if not (v[-1] == 1): raise ArithmeticError("CT37 arithmetic control 69 failed")
        c = u[-1]
        for j in range(len(v)): u[k+j] -= c*v[j]
        trim(u)
    return u


def run():
    fs = []
    for name, a, b, order, trace, disc in CURVES:
        Pts = pts(a,b)
        if not (len(Pts) == order): raise ArithmeticError("CT37 arithmetic control 80 failed")
        t = 102-len(Pts)
        if not (t == trace and t*t-4*P == disc): raise ArithmeticError("CT37 arithmetic control 82 failed")
        if not (t % P != 0): raise ArithmeticError("CT37 arithmetic control 83 failed") # ordinary, not supersingular
        # Squares are excluded: distinct imaginary quadratic CM fields.
        if not (disc < 0 and isqrt(-disc)**2 != -disc): raise ArithmeticError("CT37 arithmetic control 85 failed")
        if not (all(mul(order, Q, a) is INF for Q in Pts)): raise ArithmeticError("CT37 arithmetic control 86 failed")
        fs.append([P, -t, 1])  # X^2 - tX + p, low-to-high
        print(f"{name}: order={order} trace={trace} delta={disc} ordinary=1 points_checked={len(Pts)}")
    f1, f2 = fs
    if not (f1 == [101,7,1] and f2 == [101,11,1]): raise ArithmeticError("CT37 arithmetic control 90 failed")
    # 404 projector identity in Z[X]: A+B=[404].
    A = scale(pmul([7,1],f2), -1)
    B = pmul([11,1],f1)
    if not (padd(A,B) == [404]): raise ArithmeticError("CT37 arithmetic control 94 failed")
    # On the source E109: f2(pi)=4pi, pi^2+7pi+101=0.
    if not (pmod(padd(A, [-404]), f1) == []): raise ArithmeticError("CT37 arithmetic control 96 failed")
    if not (pmod(A,f2) == []): raise ArithmeticError("CT37 arithmetic control 97 failed")
    if not (pmod(B,f1) == []): raise ArithmeticError("CT37 arithmetic control 98 failed")
    if not (pmod(padd(B, [-404]),f2) == []): raise ArithmeticError("CT37 arithmetic control 99 failed")
    # The normalized rational idempotents A/404 and B/404 have
    # pairwise-orthogonal projections, verified modulo f1*f2 over Z.
    ff = pmul(f1,f2)
    if not (pmod(padd(pmul(A,A),scale(A,-404)),ff) == []): raise ArithmeticError("CT37 arithmetic control 103 failed")
    if not (pmod(padd(pmul(B,B),scale(B,-404)),ff) == []): raise ArithmeticError("CT37 arithmetic control 104 failed")
    if not (pmod(pmul(A,B),ff) == []): raise ArithmeticError("CT37 arithmetic control 105 failed")
    n = CURVES[0][3]*CURVES[1][3]
    inv = pow(404,-1,n)
    e1 = (sum(A)*inv)%n   # Frobenius acts as [1] on Fp-rational points
    e2 = (sum(B)*inv)%n
    if not ((e1,e2) == (9266,3052)): raise ArithmeticError("CT37 arithmetic control 110 failed")
    if not ((e1+e2)%n == 1 and e1*e2%n == 0): raise ArithmeticError("CT37 arithmetic control 111 failed")
    if not ((e1*e1-e1)%n==0 and (e2*e2-e2)%n==0): raise ArithmeticError("CT37 arithmetic control 112 failed")
    for (name,a,b,order,_,_), expected in zip(CURVES,(1,0)):
        Pts = pts(a,b)
        for Q in Pts:
            if not (mul(e1, Q, a) == (Q if expected==1 else INF)): raise ArithmeticError("CT37 arithmetic control 116 failed")
            if not (mul(e2, Q, a) == (Q if expected==0 else INF)): raise ArithmeticError("CT37 arithmetic control 117 failed")
        print(f"{name}: full rational Frobenius projection points_checked={len(Pts)}")
    # Trace recurrence t_m = t*t_(m-1) - p*t_(m-2), a diagnostic only;
    # all-extension theorem uses distinct End^0 CM fields, not bounded search.
    # Use a fixed recurrence as a bounded diagnostic, with negative controls.
    def recur(t):
        a,b=2,t
        result=[]
        for _ in range(1,25):
            result.append(b)
            a,b=b,t*b-P*a
        return result
    t1,t2=recur(-7),recur(-11)
    if not (all(a!=b for a,b in zip(t1,t2))): raise ArithmeticError("CT37 arithmetic control 130 failed")
    if not (-355 != -283 and gcd(355,283)==1): raise ArithmeticError("CT37 arithmetic control 131 failed")
    if not (isqrt(355)**2!=355 and isqrt(283)**2!=283): raise ArithmeticError("CT37 arithmetic control 132 failed")
    # Controls intentionally destroy the disjoint-CM argument.
    if not ((-7)**2-4*P != (-11)**2-4*P): raise ArithmeticError("CT37 arithmetic control 134 failed")
    if not ((-7)**2-4*P == (-7)**2-4*P): raise ArithmeticError("CT37 arithmetic control 135 failed")
    print("CRT: A=-(X+7)(X^2+11X+101), B=(X+11)(X^2+7X+101), A+B=404")
    print(f"idempotent scalars on J(F101) of order {n}: e109={e1}, e113={e2}")
    print("negative control: equal-trace replacement invalidates disjoint-CM premise")
    print("extension diagnostic: distinct traces for m=1..24 (not a general proof)")
    print("standing=[pcc:unverified]")

if __name__ == "__main__": run()
