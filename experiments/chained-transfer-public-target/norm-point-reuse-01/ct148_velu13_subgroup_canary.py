#!/usr/bin/env python3
"""CT148: exact public F229 degree-13 Velu DLP-preservation canary.

Scope: genuine rational isogeny, exhaustive point-map certification, public
small-group DLP outcomes. NOT q223 map certification or original-prime speedup.
[pcc:unverified]
"""
from __future__ import annotations
import json
from math import isqrt

P = 229
A2, A4, A6 = 1, 1, 0
O = None


def require(test, message):
    if not test:
        raise ValueError('CT148 rejected: ' + message)


def inv(x):
    require(x % P != 0, 'zero denominator')
    return pow(x % P, P - 2, P)


def neg(point):
    return O if point is O else (point[0], -point[1] % P)


def add(point, other, a2, a4):
    if point is O:
        return other
    if other is O:
        return point
    x, y = point
    u, v = other
    if x == u and (y + v) % P == 0:
        return O
    if x == u:
        require(y % P, 'zero tangent ordinate')
        slope = (3*x*x + 2*a2*x + a4) * inv(2*y) % P
    else:
        slope = (v - y) * inv(u - x) % P
    xx = (slope*slope - a2 - x - u) % P
    yy = (slope*(x-xx) - y) % P
    return (xx, yy)


def mul(k, pt, a2, a4):
    require(k >= 0, 'negative scalar')
    ret = O
    while k:
        if k & 1:
            ret = add(ret, pt, a2, a4)
        pt = add(pt, pt, a2, a4)
        k >>= 1
    return ret


def oncurve(pt, a2, a4, a6):
    return pt is O or (pt[1]**2 - (pt[0]**3 + a2*pt[0]**2 + a4*pt[0] + a6)) % P == 0


def source_points():
    return [O] + [(x,y) for x in range(P) for y in range(P) if oncurve((x,y), A2,A4,A6)]


def order(pt, bound, a2, a4):
    require(mul(bound, pt, a2, a4) is O, 'order bound failed')
    for k in range(1, bound+1):
        if mul(k, pt, a2, a4) is O:
            return k
    raise ValueError('order not found')


def bsgs(base, target, n, a2, a4):
    m = isqrt(n)
    if m*m < n:
        m += 1
    table = {}
    p = O
    for i in range(m):
        table.setdefault(p, i)
        p = add(p, base, a2, a4)
    step = neg(mul(m, base, a2, a4))
    probe = target
    for j in range(m + 1):
        if probe in table:
            x = j * m + table[probe]
            if x < n and mul(x, base, a2, a4) == target:
                return x
        probe = add(probe, step, a2, a4)
    raise ValueError('no dlog in declared subgroup')


def main():
    source = source_points()
    N = len(source)
    require(N == 208, 'source census')
    torsion = next(pt for pt in source if order(pt, N, A2, A4) == 13)
    kernel = {mul(k, torsion, A2, A4) for k in range(13)}
    require(len(kernel) == 13 and O in kernel, 'kernel census')
    kernel_nz = sorted((pt for pt in kernel if pt is not O))

    def phi(pt):
        if pt in kernel:
            return O
        x, y = pt
        for t in kernel_nz:
            pt_t = add(pt, t, A2, A4)
            require(pt_t is not O, 'kernel pole not caught')
            x = (x + pt_t[0] - t[0]) % P
            y = (y + pt_t[1] - t[1]) % P
        return (x, y)

    mapped = {pt: phi(pt) for pt in source}
    # Rational Velu keeps a2 fixed; infer a4'/a6' from two independent images,
    # then prove all 208 images lie on the one curve instead of assuming it.
    images = sorted({q for q in mapped.values() if q is not O})
    r, s = next((r,s) for r in images for s in images if r[0] != s[0])
    def residual(q):
        x,y = q
        return (y*y-x*x*x-A2*x*x) % P
    b = (residual(r)-residual(s))*inv(r[0]-s[0])%P
    c = (residual(r)-b*r[0])%P
    discriminant = (A2*A2*b*b - 4*b*b*b - 4*A2*A2*A2*c
                    - 27*c*c + 18*A2*b*c) % P
    require(discriminant != 0, 'singular target curve')
    require(all(oncurve(q,A2,b,c) for q in mapped.values()),'image not on one target curve')
    target = [O] + [(x,y) for x in range(P) for y in range(P) if oncurve((x,y),A2,b,c)]
    require(len(target)==N,'isogeny target cardinality')
    require({pt for pt in source if mapped[pt] is O}==kernel,'map kernel differs')
    require(len(set(mapped.values())) == N//13, 'image cardinality')
    # Exhaustive all-pair addition is independent of the chosen subgroup.
    additions = 0
    for p in source:
        for q in source:
            require(mapped[add(p,q,A2,A4)] == add(mapped[p],mapped[q],A2,b),
                    'Velu homomorphism')
            additions += 1

    group_orders = {pt: order(pt,N,A2,A4) for pt in source}
    n_good = max(o for o in group_orders.values() if o % 13)
    good = next(pt for pt in source if group_orders[pt] == n_good)
    n_bad = max(o for o in group_orders.values() if o % 13 == 0)
    bad = next(pt for pt in source if group_orders[pt] == n_bad)
    require(n_good > 1 and n_bad % 13 == 0, 'missing good/bad subgroup')
    mg, mb = mapped[good], mapped[bad]
    good_image_order = order(mg,N,A2,b)
    bad_image_order = order(mb,N,A2,b)
    require(good_image_order == n_good, 'good subgroup collapsed')
    require(bad_image_order < n_bad and n_bad % bad_image_order == 0,
            'bad subgroup not collapsed')
    safe_tests = 0
    for x in range(n_good):
        q=mul(x,good,A2,A4)
        y=bsgs(mg,mapped[q],good_image_order,A2,b)
        require(y==x and mul(y,good,A2,A4)==q,'good DLP recovery')
        safe_tests += 1
    bad_source_rejections=0
    mapped_classes={}
    for x in range(n_bad):
        q=mul(x,bad,A2,A4)
        y=bsgs(mb,mapped[q],bad_image_order,A2,b)
        require(y==x%bad_image_order,'bad DLP residue mismatch')
        require(mapped[mul(y,bad,A2,A4)] == mapped[q], 'target verifier failure')
        if mul(y,bad,A2,A4) != q:
            bad_source_rejections += 1
        mapped_classes.setdefault(mapped[q], []).append(x)
    require(bad_source_rejections == n_bad-bad_image_order,
            'unexpected collision rejection count')
    require(len(mapped_classes)==bad_image_order, 'wrong image quotient classes')
    require(all(len(v)==n_bad//bad_image_order for v in mapped_classes.values()),
            'unequal image fibers')
    # A target-only algorithm cannot recover which member of the fiber was input.
    witness=next(v for v in mapped_classes.values() if len(v)>1)
    require(witness[0]!=witness[1] and
            mapped[mul(witness[0],bad,A2,A4)]==mapped[mul(witness[1],bad,A2,A4)],
            'missing indistinguishable source DLPs')
    return {'field':'F_229','source_curve':'y^2=x^3+x^2+x',
            'target_curve':f'y^2=x^3+x^2+{b}x+{c}',
            'source_cardinality':N,'target_cardinality':len(target),
            'source_13_kernel_generator':torsion, 'target_discriminant':discriminant,
            'kernel_size':len(kernel),'image_size':len(set(mapped.values())),
            'all_group_homomorphism_pairs':additions,
            'safe_subgroup_order':n_good,'safe_generator':good,
            'safe_image_order':good_image_order,
            'safe_verified_public_dlps':safe_tests,
            'unsafe_subgroup_order':n_bad,'unsafe_generator':bad,
            'unsafe_image_order':bad_image_order,
            'unsafe_distinct_source_candidates_per_target':n_bad//bad_image_order,
            'unsafe_full_source_rejections':bad_source_rejections,
            'unsafe_indistinguishable_scalar_witness':witness[:2],
            'standing':'[pcc:unverified]','scope':'toy degree-13 Velu map, not actual q223'}

if __name__=='__main__':
    print(json.dumps(main(),sort_keys=True))
