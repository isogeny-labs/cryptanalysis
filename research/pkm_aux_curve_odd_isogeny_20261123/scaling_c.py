#!/usr/bin/env python3
"""Branch C scaling: enumeration vs univariate elimination at m = 2 and 3,
far beyond the |V| any Groebner solver reached.

Neither method reads V's structure (an isogeny coset, a Kummer coset or a
random set cost the same), so V here is a random |V|-subset of F_p and the
target is x(R) of a random point; the m = 3 pair sets are checked equal
between the two methods on every instance.

m = 3 univariate: B(u) = prod_v S3(u, v, x_R) has the abscissae of R -/+ P3
as roots; for each root u in F_p, the m = 2 univariate solve with target u.
m = 3 enumeration: for v1 <= v2 in V, the two u with S3(v1, v2, u) = 0, then
the quadratic S3(u, X, x_R), membership by hash set.
"""
import json
import random
import sys
import time

import flint

from solvers_c import prod_tree, s3_quadratic, solve_enum, solve_univ, tonelli


def quad_roots(c0, c1, c2, p):
    if c2 == 0:
        return [(-c0) * pow(c1, p - 2, p) % p] if c1 else []
    s = tonelli((c1 * c1 - 4 * c2 * c0) % p, p)
    if s is None:
        return []
    inv = pow(2 * c2, p - 2, p)
    return list({(-c1 + s) * inv % p, (-c1 - s) * inv % p})


def enum3(V, r, a, b, p):
    vs, out = set(V), set()
    for i, v1 in enumerate(V):
        for v2 in V[i:]:
            for u in quad_roots(*s3_quadratic(v1, v2, a, b, p), p):  # S3 is symmetric
                for x3 in quad_roots(*s3_quadratic(u, r, a, b, p), p):
                    if x3 in vs:
                        out.add(tuple(sorted((v1, v2, x3))))
    return out


def univ3(V, r, a, b, p):
    B = prod_tree((flint.nmod_poly(list(s3_quadratic(v, r, a, b, p)), p) for v in V), p)
    out = set()
    vs = set(V)
    for u, _ in B.roots():
        u = int(u)
        for x1, x2 in solve_univ(V, u, a, b, p):
            # the third summand: x3 in V with S3(u, x3, r) = 0
            for x3 in quad_roots(*s3_quadratic(u, r, a, b, p), p):
                if x3 in vs:
                    out.add(tuple(sorted((x1, x2, x3))))
    return out


def main():
    p = int(sys.argv[1])
    m = int(sys.argv[2])
    sizes = [int(s) for s in sys.argv[3].split(",")]
    reps = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    rng = random.Random(20261123 + m)
    for n in sizes:
        for rep in range(reps):
            a, b = rng.randrange(p), rng.randrange(1, p)
            V = rng.sample(range(p), n)
            while True:
                xr = rng.randrange(p)
                if pow((xr ** 3 + a * xr + b) % p, (p - 1) // 2, p) == 1:
                    break
            rec = {"p": p, "m": m, "V_size": n, "rep": rep}
            if m == 2:
                t0 = time.perf_counter(); e = solve_enum(V, xr, a, b, p); rec["enum_s"] = time.perf_counter() - t0
                t0 = time.perf_counter(); u = solve_univ(V, xr, a, b, p); rec["univ_s"] = time.perf_counter() - t0
            else:
                t0 = time.perf_counter(); u = univ3(V, xr, a, b, p); rec["univ_s"] = time.perf_counter() - t0
                if n <= 1024:
                    t0 = time.perf_counter(); e = enum3(V, xr, a, b, p); rec["enum_s"] = time.perf_counter() - t0
                else:
                    e = None
            rec["solutions"] = len(u)
            rec["agree"] = None if e is None else (e == u)
            print(json.dumps(rec), flush=True)


if __name__ == "__main__":
    main()
