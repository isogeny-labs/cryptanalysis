#!/usr/bin/env python3
"""L4 counting check. Leaf of the lin21 2+1 decision with u kept free:
    p^2 + u p + u^2 s^2 + b = 0,  s in V = span(1..z^(d-1)), p in span(1..z^(2d-2)),
F2-linear in the 3d-1 bits of (s, p) with coefficients depending on u.
For u uniform in F_{2^n}^* (the MinRank relaxation: no link u = x(R - P3)),
count the fraction of u for which the leaf system is consistent, and compare
with the fraction for u in the true image {x(R - P3) : x(P3) in V} on random
targets. Prediction: relaxation fraction ~ 2^-(n - 3d + 1) (constant at
n ~ 3d), so a rank condition alone cannot isolate the 2^d true u values.
"""
import json, random, sys
sys.path.insert(0, '../l3_torsion_count')
import count_t0_relations as m

def consistent(F, n, d, u, b):
    cols = []
    u2 = F.sq(u)
    for i in range(d):            # s = z^i  ->  u^2 s^2
        cols.append(F.mul(u2, F.sq(1 << i)))
    for j in range(2 * d - 1):    # p = z^j  ->  p^2 + u p
        pj = 1 << j
        cols.append(F.sq(pj) ^ F.mul(u, pj))
    basis = {}                    # Gaussian elimination over F2^n vectors (ints)
    for c in cols:
        for hb, v in sorted(basis.items(), reverse=True):
            if c >> hb & 1:
                c ^= v
        if c:
            basis[c.bit_length() - 1] = c
    t = b
    for hb, v in sorted(basis.items(), reverse=True):
        if t >> hb & 1:
            t ^= v
    return t == 0, len(basis)

out = []
for n in (13, 15, 17, 19, 21):
    d = n // 3
    F = m.Field(n); rng = random.Random(f"l4-{n}")
    a = 1
    b = rng.randrange(1, 1 << n); E = m.Curve(F, a, b)
    trials = 4000
    relax = sum(consistent(F, n, d, rng.randrange(1, 1 << n), b)[0] for _ in range(trials)) / trials
    # true image for random targets R
    pts = [P for x in range(1, 1 << d) for P in E.lift(x)]
    img_hits = img_tot = 0
    for _ in range(20):
        while True:
            x = rng.randrange(1 << d, 1 << n); L = E.lift(x)
            if L: R = rng.choice(L); break
        for P in pts:
            Q = E.add(R, E.neg(P))
            if Q is None or Q[0] == 0: continue
            img_tot += 1; img_hits += consistent(F, n, d, Q[0], b)[0]
    row = {"n": n, "d": d, "unknown_bits": 3 * d - 1, "relaxed_fraction": relax,
           "predicted": 2.0 ** -(n - 3 * d + 1), "true_image_fraction": img_hits / img_tot,
           "true_image_u_per_target": len(pts)}
    out.append(row); print(json.dumps(row), flush=True)
json.dump(out, open("rank_fraction.json", "w"), indent=1)
