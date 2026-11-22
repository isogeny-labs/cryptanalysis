#!/usr/bin/env python3
"""CT32 independent finite-module oracle, F_101 7^2 torsion.

No elliptic-map, genus-2, Sage/SymPy or producer arithmetic imports.
The geometric interpretation is conditional on the fixed nondual kernel
identifications in CT29--31; the finite modular checks are exhaustive.
"""
from dataclasses import dataclass
from math import gcd, lcm

P = 101
ELL = 7
MOD = ELL * ELL

@dataclass(frozen=True)
class Case:
    name: str
    cardinality: int
    a: int
    b: int
    selected_mod7: int
    expected_mod49: int
    other_mod49: int
    degree_points: int
    degree_x: int

CASES = (
    Case("E109", 109, 1, 46, 5, 33, 9, 42, 21),
    Case("E113", 113, 44, 21, 6, 27, 11, 14, 7),
)

def count_points_mod_p(a: int, b: int) -> int:
    # Independent affine point enumeration plus the point at infinity.
    squares = {y*y % P for y in range(P)}
    return 1 + sum(1 if (x*x*x+a*x+b) % P == 0 else
                   2 if (x*x*x+a*x+b) % P in squares else 0
                   for x in range(P))

def eigen_roots_mod(m: int, trace: int, q: int = P) -> list[int]:
    return [a for a in range(m) if (a*a - trace*a + q) % m == 0]

def lift_simple_root(trace: int, root: int, q: int = P) -> int:
    if (root*root - trace*root + q) % ELL:
        raise ValueError("not a characteristic root modulo seven")
    slope = (2*root - trace) % ELL
    if gcd(slope, ELL) != 1:
        raise ValueError("not a simple root: no unique Hensel lift")
    defect = ((root*root - trace*root + q) // ELL) % ELL
    digit = (-defect * pow(slope, -1, ELL)) % ELL
    x = root + ELL*digit
    if (x*x - trace*x + q) % MOD:
        raise AssertionError("Hensel identity failed")
    return x

def order_mod(a: int, modulus: int) -> int:
    if gcd(a, modulus) != 1:
        raise ValueError("not a unit")
    for e in range(1, 200):
        if pow(a, e, modulus) == 1:
            return e
    raise AssertionError("unexpected order")

def projective_x_degree(a: int) -> int:
    # x(Frob^d Q)=x(Q) precisely when lambda^d = +/-1 modulo 49.
    return next(d for d in range(1, 200) if pow(a, d, MOD) in (1, MOD-1))

def fixed_kernel_count(a: int, d: int) -> int:
    return gcd(MOD, (pow(a, d, MOD) - 1) % MOD)

def require(cond: bool, message: str):
    if not cond:
        raise AssertionError(message)

def audit(case: Case) -> dict:
    actual = count_points_mod_p(case.a, case.b)
    require(actual == case.cardinality, "independent point count")
    t = P + 1 - actual
    roots7 = eigen_roots_mod(ELL, t)
    roots49 = eigen_roots_mod(MOD, t)
    require(len(roots7) == 2 and len(roots49) == 2, "root count")
    require(roots7[0] != roots7[1], "nonsemisimple mod7 Frobenius")
    lifts = {r: lift_simple_root(t, r) for r in roots7}
    require(sorted(lifts.values()) == roots49, "Hensel vs brute force")
    forward = lifts[case.selected_mod7]
    backward = next(x for x in roots49 if x != forward)
    require((forward, backward) == (case.expected_mod49, case.other_mod49),
            "forward/dual eigenline")
    require((forward*backward - P) % MOD == 0, "determinant")
    require((forward+backward - t) % MOD == 0, "trace")
    n, nx = order_mod(forward, MOD), projective_x_degree(forward)
    require((n, nx) == (case.degree_points, case.degree_x), "degrees")
    require(pow(forward, nx, MOD) == MOD-1, "x descent sign")
    require(fixed_kernel_count(forward, n) == MOD, "full kernel not fixed")
    require(fixed_kernel_count(forward, n//7) == ELL, "premature full kernel")
    require(all(fixed_kernel_count(forward,d)<MOD for d in range(1,n)), "minimal point field")
    require(all(pow(forward,d,MOD) not in (1, MOD-1) for d in range(1,nx)),
            "minimal x field")
    # Two unique primitive Frobenius-stable cyclic order-49 lines:
    # (1,x) for slopes x mod49, and vertical (0,1).
    lines = 1 + sum(1 for x in range(MOD)
                    if (backward*x - forward*x) % MOD == 0)
    require(lines == 2, "extra stable primitive lines")
    return dict(label=case.name, count=actual, trace=t, roots7=roots7,
                roots49=roots49, forward=forward, dual=backward,
                forward_degree=n, x_degree=nx,
                points_fixed_over_6=fixed_kernel_count(forward,6),
                stable_cyclic49_lines=lines)

def negative_controls():
    for c in CASES:
        t = P+1-c.cardinality
        try:
            lift_simple_root(t, 0)
        except ValueError:
            pass
        else:
            raise AssertionError("nonroot accepted")
        require(lift_simple_root(t,c.selected_mod7) != c.other_mod49,
                "wrong eigendirection accepted")
    try:
        lift_simple_root(2, 1, q=1)  # repeated (X-1)^2 mod7
    except ValueError:
        pass
    else:
        raise AssertionError("nonsimple Hensel case accepted")
    require(projective_x_degree(33) != order_mod(33,MOD), "x degree lost")
    require(fixed_kernel_count(33,6) == 7 and fixed_kernel_count(27,6) == 7,
            "fake F101^6 full kernel")

def main():
    results = [audit(c) for c in CASES]
    negative_controls()
    full = lcm(*(x["forward_degree"] for x in results))
    xonly = lcm(*(x["x_degree"] for x in results))
    require((full,xonly) == (42,21) and full == 2*xonly, "product field")
    print("CT32 F101 Frobenius mod49: arithmetic checks passed [pcc:unverified]")
    for d in results:
        print(f'{d["label"]}: #E={d["count"]}, trace={d["trace"]}, '
              f'roots7={d["roots7"]}, roots49={d["roots49"]}; '
              f'forward={d["forward"]}, dual={d["dual"]}; '
              f'point degree={d["forward_degree"]}, x degree={d["x_degree"]}; '
              f'F101^6 fixed={d["points_fixed_over_6"]}/49; '
              f'stable lines={d["stable_cyclic49_lines"]}')
    print(f'Product kernel: full points degree {full}; x-support degree {xonly}')
    print("Negative controls rejected wrong direction/nonroot/repeated root/F101^6 full-kernel")

if __name__ == "__main__":
    main()
