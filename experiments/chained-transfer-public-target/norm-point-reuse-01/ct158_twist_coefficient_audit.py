#!/usr/bin/env python3
"""CT158 independent cubic-field coefficient/trace audit; no Rust or C++ imports.

This checks the twist construction and selected field-square controls. The
exhaustive point census is a separate C++ program. [pcc:unverified].
"""
import json
from math import isqrt

P = 223
Z = (0, 0, 0)
ONE = (1, 0, 0)
A2 = (127, 56, 199)
A4 = (152, 35, 36)
A6 = (212, 109, 150)
V = (12, 0, 0)

def require(p, m):
    if not p:
        raise ValueError('CT158 validation rejected: ' + m)

def add(x, y):
    return tuple((a+b) % P for a, b in zip(x, y))

def neg(x):
    return tuple(-a % P for a in x)

def mul(x, y):
    # Independent explicit cubic product formula, z^3 = 3.
    a,b,c=x; d,e,f=y
    return ((a*d+3*(b*f+c*e))%P,
            (a*e+b*d+3*c*f)%P,
            (a*f+b*e+c*d)%P)

def power(x, n):
    require(n >= 0, 'negative exponent')
    out=ONE
    while n:
        if n & 1:
            out=mul(out,x)
        x=mul(x,x)
        n >>= 1
    return out

def times(n,x):
    return tuple((n*a)%P for a in x)

def inv(x):
    require(x != Z, 'inverse of zero')
    return power(x, P**3 - 2)

def rhs(x, a2, a4, a6):
    return add(add(power(x, 3), mul(a2, power(x, 2))), add(mul(a4,x),a6))

def coefficients(source=(A2,A4,A6), v=V):
    a2,a4,a6=source
    third=inv((3,0,0))
    inv27=inv((27,0,0))
    A=add(a4,neg(mul(power(a2,2),third)))
    B=add(add(a6, neg(mul(mul(a2,a4),third))), times(2,mul(power(a2,3),inv27)))
    return A,B,mul(power(v,2),A),mul(power(v,3),B)

def audit():
    require(power((0,1,0),3) == (3,0,0), 'wrong field modulus')
    require(power((0,1,0),P**3) == (0,1,0), 'field Frobenius failure')
    require(power(V,(P**3-1)//2) == (P-1,0,0), 'v must be nonsquare in K')
    require(pow(12,(P-1)//2,P) == P-1, 'v must be Fp nonsquare')
    a,b,at,bt=coefficients()
    require(a == (214,144,205) and b == (137,218,9), 'short coefficients mismatch')
    require(at == (42,220,84) and bt == (133,57,165), 'twist coefficients mismatch')
    # Explicit change of coordinates x_old = x_short - a2/3.
    shift=mul(A2,inv((3,0,0)))
    for i in range(128):
        x=((17*i+3)%P, (29*i+5)%P, (31*i+11)%P)
        lhs=rhs(add(x,neg(shift)),A2,A4,A6)
        right=rhs(x,Z,a,b)
        require(lhs == right, f'coordinate change mismatch at {i}')
        # Isomorphism over K(sqrt(v)): x_twisted=v*x_short, y_twisted=v^(3/2)*y.
        require(rhs(mul(V,x),Z,at,bt) == mul(power(V,3),right),
                f'quadratic twist model mismatch at {i}')
        # Distinct even and odd norm characters must interchange square status.
        if right != Z:
            status=(power(right,(P**3-1)//2) == ONE)
            changed=(power(mul(power(V,3),right),(P**3-1)//2) == ONE)
            require(status != changed, f'nonzero twist Legendre parity at {i}')
    n_original=11_092_292
    n_twist=11_086_844
    size=P**3
    require(n_original + n_twist == 2*(size+1), 'wrong group-order identity')
    require(n_original == 4*2_773_073 and n_twist == 4*2_771_711, 'wrong subgroup order')
    original_trace=size+1-n_original
    twist_trace=size+1-n_twist
    require(original_trace == -2724 and twist_trace == 2724, 'trace mismatch')
    # Hasse admissible integer traces over F_p, all checked for both fixed traces.
    candidate_traces=tuple(t for t in range(-isqrt(4*P),isqrt(4*P)+1) if t*t<=4*P)
    diffs={str(T):min(abs(t*t*t-3*P*t-T) for t in candidate_traces)
           for T in (original_trace,twist_trace)}
    require(len(candidate_traces)==59 and diffs == {'-2724':112,'2724':112},
            'zero-Hom trace gap mismatch')
    # Only tests the numerical trace obstruction; map field-of-definition remains a separate gate.
    return {'schema':'ct158-independent-coefficient-audit/v1',
            'status':'[pcc:unverified]', 'field':[P,3], 'nu':12,
            'short_A':a,'short_B':b,'twist_A':at,'twist_B':bt,
            'coordinate_and_twist_tests':128, 'nonsquare_checked':True,
            'original_order':n_original,'twist_order':n_twist,
            'original_trace':original_trace,'twist_trace':twist_trace,
            'prime_trace_candidates':len(candidate_traces),
            'minimum_base_change_trace_gaps':diffs}

def negative_controls():
    variants = [((A2,A4,(213,109,150)),V),
                ((A2,A4,A6),(1,0,0)),
                ((A2,A4,A6),(0,0,0))]
    rejected=0
    canonical=coefficients()
    for i,(source,nu) in enumerate(variants):
        try:
            test=coefficients(source,nu)
            require(test==canonical, f'mutant {i} changed expected coefficients')
        except ValueError:
            rejected+=1
    require(rejected==3,'coefficient negative control not rejected')
    return rejected

if __name__=='__main__':
    out=audit();out['coefficient_mutations_rejected']=negative_controls()
    print(json.dumps(out,sort_keys=True,separators=(',',':')))
