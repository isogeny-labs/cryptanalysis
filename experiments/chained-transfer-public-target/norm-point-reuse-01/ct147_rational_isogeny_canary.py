#!/usr/bin/env python3
"""CT147: exhaustive genuine rational 2-isogeny test over F25, independent of CT146.

A public finite toy canary; NOT the original q223 transfer, native benchmark,
Jacobian identity proof, or a verified ECDLP speedup. [pcc:unverified]
"""
import json

P = 5
IR = 2
O = None


def fadd(a, b):
    return (a % P + b % P) % P + P * ((a // P + b // P) % P)


def fneg(a):
    return (-(a % P)) % P + P * ((-(a // P)) % P)


def fsub(a, b):
    return fadd(a, fneg(b))


def fmul(a, b):
    x, y, z, w = a % P, a // P, b % P, b // P
    return (x * z + IR * y * w) % P + P * ((x * w + y * z) % P)


def fpow(a, n):
    result = 1
    while n:
        if n & 1:
            result = fmul(result, a)
        a = fmul(a, a)
        n //= 2
    return result


def finv(a):
    if not a:
        raise ZeroDivisionError("zero field denominator")
    return fpow(a, 23)


def fdiv(a, b):
    return fmul(a, finv(b))


def require(condition, message):
    if not condition:
        raise ValueError("CT147 rejected: " + message)


def on_curve(point, a, b):
    if point is O:
        return True
    x, y = point
    return fmul(y, y) == fmul(x, fadd(fadd(fmul(x, x), fmul(a, x)), b))


def neg(point):
    return O if point is O else (point[0], fneg(point[1]))


def add(p, q, a, b):
    if p is O:
        return q
    if q is O:
        return p
    x, y = p
    u, v = q
    if x == u and y == fneg(v):
        return O
    if x == u:
        require(y != 0, "invalid double at zero ordinate")
        slope = fdiv(fadd(fadd(fmul(3, fmul(x, x)),
                                fmul(2, fmul(a, x))), b), fmul(2, y))
    else:
        slope = fdiv(fsub(v, y), fsub(u, x))
    xx = fsub(fsub(fsub(fmul(slope, slope), a), x), u)
    yy = fsub(fmul(slope, fsub(x, xx)), y)
    return xx, yy


def times(n, p, a, b):
    result = O
    while n:
        if n & 1:
            result = add(result, p, a, b)
        p = add(p, p, a, b)
        n >>= 1
    return result


def points(a, b):
    return [O] + [(x, y) for x in range(25) for y in range(25)
                  if on_curve((x, y), a, b)]


def phi(p, a, b):
    """Velu 2-isogeny with kernel {O,(0,0)}; handle both poles explicitly."""
    if p is O:
        return O
    x, y = p
    if x == 0:
        require(y == 0, "non-kernel exceptional denominator")
        return O
    xx = fadd(fadd(x, a), fdiv(b, x))
    yy = fmul(y, fsub(1, fdiv(b, fmul(x, x))))
    return xx, yy


def frob(p):
    return O if p is O else (fpow(p[0], 5), fpow(p[1], 5))


def main():
    a = b = 1
    a2 = fneg(fmul(2, a))
    b2 = fsub(fmul(a, a), fmul(4, b))
    source = points(a, b)
    target = points(a2, b2)
    require(len(source) == len(target) == 32, "group sizes not expected")
    require(all(on_curve(phi(p, a, b), a2, b2) for p in source),
            "rational map curve residual")
    require(phi(O, a, b) is O and phi((0, 0), a, b) is O,
            "exceptional kernel")
    image = {phi(p, a, b) for p in source}
    require(len(image) == 16 and len(image) * 2 == len(source),
            "kernel/image cardinality")
    two = [t for t in source if times(2, t, a, b) is O]
    require(len(two) == 4, "full geometric two-torsion")
    for p in source:
        require(phi(frob(p), a, b) == frob(phi(p, a, b)),
                "non-K-defined isogeny")
        for q in source:
            require(phi(add(p, q, a, b), a, b) ==
                    add(phi(p, a, b), phi(q, a, b), a2, b2),
                    "nonhomomorphic rational map")
        for t in two:
            require(times(2, phi(add(p, t, a, b), a, b), a2, b2)
                    == phi(times(2, p, a, b), a, b),
                    "two-torsion correction identity")
    # Explicit dual via another 2-isogeny, followed by the target's
    # scaling (x'',y'')=(4x,8y), independent of original CT146 scalar maps.
    aa = fneg(fmul(2, a2))
    bb = fsub(fmul(a2, a2), fmul(4, b2))
    require(aa == fmul(4, a) and bb == fmul(16 % P, b),
            "dual target curve scaling")
    inverse4, inverse8 = finv(4), finv(8 % P)

    def dual(q):
        r = phi(q, a2, b2)
        return O if r is O else (fmul(r[0], inverse4), fmul(r[1], inverse8))

    require(all(on_curve(dual(q), a, b) for q in target),
            "dual maps outside source")
    require(all(dual(phi(p, a, b)) == times(2, p, a, b) for p in source),
            "dual composite differs from [2]")

    # The sharp necessary-and-sufficient correction condition here is
    # phi([2]T)=O, not [2]T=O. Non-E[2] kernel-preimage corrections exist.
    weak = [t for t in source
            if times(2, t, a, b) is not O and
            phi(times(2, t, a, b), a, b) is O]
    require(len(weak) == 4, "missing kernel-preimage non-E2 corrections")
    for t in weak:
        for p in source:
            require(times(2, phi(add(p, t, a, b), a, b), a2, b2)
                    == phi(times(2, p, a, b), a, b),
                    "kernel-preimage correction did not cancel")

    wrong = next(t for t in source
                 if phi(times(2, t, a, b), a, b) is not O)
    rejected = sum(
        times(2, phi(add(p, wrong, a, b), a, b), a2, b2)
        != phi(times(2, p, a, b), a, b) for p in source)
    require(rejected == len(source), "wrong correction accepted")

    # Translation preserves the target curve but is not a group morphism.
    w = (0, 0)
    require(on_curve(w, a2, b2) and w is not O,
            "invalid translation negative control")

    def shifted(p):
        return add(phi(p, a, b), w, a2, b2)

    require(shifted(O) is not O and
            shifted(add(O, O, a, b)) != add(shifted(O), shifted(O), a2, b2),
            "translated nonhomomorphism accepted")
    result = dict(
        field="F5[u]/(u^2-2)", source_curve="y^2=x^3+x^2+x",
        source_points=len(source), target_points=len(target),
        image_points=len(image), two_torsion=len(two),
        map_addition_checks=len(source)**2,
        corrected_lift_checks=len(source)*len(two),
        frob_checks=len(source), dual_double_checks=len(source),
        non_e2_kernel_corrections=len(weak),
        kernel_correction_checks=len(weak)*len(source),
        wrong_correction_rejections=rejected,
        negative_controls=["wrong_correction_with_nonzero_phi_double",
                           "nonhomomorphic_translation"],
        standing="[pcc:unverified]")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
