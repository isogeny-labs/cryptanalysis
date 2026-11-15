#!/usr/bin/env python3
"""Independent finite-field canary for replacing quadratic point trace by doubling.

This is not the N4 Jacobian implementation or an original-prime performance run.
All arithmetic is exact in F_5[u]/(u^2-2), with y^2=x^3+1.
"""
from __future__ import annotations
import json

P, D = 5, 2
ZERO, ONE = (0, 0), (1, 0)

def plus(x, y):
    return ((x[0] + y[0]) % P, (x[1] + y[1]) % P)

def neg(x):
    return (-x[0] % P, -x[1] % P)

def minus(x, y):
    return plus(x, neg(y))

def times(x, y):
    a, b = x
    c, d = y
    return ((a*c + D*b*d) % P, (a*d + b*c) % P)

def invert(x):
    a, b = x
    n = (a*a - D*b*b) % P
    if not n:
        raise ZeroDivisionError('zero element')
    z = pow(n, -1, P)
    return ((a*z) % P, (-b*z) % P)

def divide(x, y):
    return times(x, invert(y))

def conjugate(x):
    return (x[0], (-x[1]) % P)

def point_frobenius(pt):
    return None if pt is None else (conjugate(pt[0]), conjugate(pt[1]))

def point_neg(pt):
    return None if pt is None else (pt[0], neg(pt[1]))

def point_add(a, b):
    if a is None:
        return b
    if b is None:
        return a
    x, y = a
    z, w = b
    if x == z and y == neg(w):
        return None
    if x == z:
        if y == ZERO:
            return None
        slope = divide(times((3, 0), times(x, x)), times((2, 0), y))
    else:
        slope = divide(minus(w, y), minus(z, x))
    new_x = minus(minus(times(slope, slope), x), z)
    new_y = minus(times(slope, minus(x, new_x)), y)
    return (new_x, new_y)

def on_curve(pt):
    if pt is None:
        return True
    x, y = pt
    return times(y, y) == plus(times(times(x, x), x), ONE)

def rational(pt):
    return pt is None or all(z[1] == 0 for z in pt)

def require(condition, message):
    if not condition:
        raise ValueError('CT145 REJECTED: ' + message)

def run():
    elems = [(a, b) for a in range(P) for b in range(P)]
    points = [None] + [(x, y) for x in elems for y in elems if on_curve((x, y))]
    witness = ((4, 1), (3, 0))
    doubled = ((0, 0), (1, 0))
    traced = ((2, 0), (2, 0))
    delta = ((4, 0), (0, 0))
    require(witness in points, 'point absent')
    require(point_frobenius(witness) == ((4, 4), (3, 0)), 'Frobenius')
    require(point_add(witness, witness) == doubled, 'doubling')
    require(point_add(witness, point_frobenius(witness)) == traced, 'trace')
    require(point_add(traced, point_neg(doubled)) == delta, 'trace defect')
    require(point_add(delta, delta) is None, 'defect must be 2-torsion')
    require(on_curve(delta) and rational(doubled) and rational(traced), 'rational outputs')
    require(not rational(witness) and traced != doubled, 'must separate trace and doubling')
    bad = 0
    for pt in points:
        tr = point_add(pt, point_frobenius(pt))
        dbl = point_add(pt, pt)
        defect = point_add(tr, point_neg(dbl))
        frob_defect = point_add(point_frobenius(pt), point_neg(pt))
        require(on_curve(tr) and rational(tr), 'group trace must be rational')
        require(defect == frob_defect, 'trace-defect identity')
        if rational(dbl):
            require(point_add(defect, defect) is None, 'rational double implies 2-torsion defect')
            if not rational(pt) and tr != dbl:
                bad += 1
        if rational(pt):
            require(tr == dbl, 'rational points have trace=double')
    require(bad > 0, 'missing counterexample')
    return {'field': 'F5[u]/(u^2-2)', 'curve': 'y^2=x^3+1',
            'all_extension_points_checked': len(points),
            'counterexamples_with_rational_double': bad,
            'point': witness, 'twice': doubled, 'trace': traced,
            'nonzero_two_torsion_defect': delta,
            'scope': 'group trace on E(F25); not original q223 chain',
            'standing': '[pcc:unverified]'}

if __name__ == '__main__':
    print(json.dumps(run(), sort_keys=True))
