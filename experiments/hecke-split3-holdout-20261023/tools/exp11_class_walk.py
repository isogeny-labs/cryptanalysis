"""Exp 11: walk one isogeny class of X_0(11) over F_p with a smooth conductor and measure the Hecke relation rank.

Run:  sage -python tools/exp11_class_walk.py     (env: PFS_WALK_DK=-7  PFS_WALK_F=210  PFS_WALK_L=2,3,5,7  PFS_WALK_PMIN)

Choose D_K and f, then a prime p with 4p = u^2 + f^2 |D_K|, so the CM curve with discriminant D_K (j = -3375 for
D_K = -7) has trace +-u over F_p and the isogeny class of trace u is the full volcano of conductors f' | f.
Start from the rational points of X_0(11) above that j, walk the class by l-isogenies for l in L using the
explicit Hecke functions (rational neighbour x-coordinates), keep every point whose curve has trace +-u, and
record a relation  sum(neighbours) = a_l z  at every point whose l+1 neighbours are all rational (verified in
the group).  Then: rank of the relation system over the largest prime factor of #E(F_p), deficiency, and the
per-l distribution of the number of rational neighbours (floor vertices have one).  Optionally add the
Atkin-Lehner relation w_11 z = eps z + t (found by testing Phi_11(j(z), j(eps z + t)) = 0).
The question: can the within-class rank reach |C| - 1 when several small primes divide f?
Output: data/exp11_class_walk.json
"""
import os, sys, json, math, time, random
from sage.all import (EllipticCurve, GF, ZZ, QQ, PolynomialRing, matrix, factor, is_prime, next_prime,
                      EllipticCurve_from_j, hilbert_class_polynomial, pari)
sys.path.insert(0, os.path.dirname(__file__))
import hecke11 as H

OUT = os.path.join(os.path.dirname(__file__), "..", "data", f"exp11_class_walk_D{abs(int(os.environ.get('PFS_WALK_DK', '-7')))}_f{os.environ.get('PFS_WALK_F', '210')}.json")
DK = int(os.environ.get("PFS_WALK_DK", "-7"))
F = int(os.environ.get("PFS_WALK_F", "210"))
LS = [int(s) for s in os.environ.get("PFS_WALK_L", "2,3,5,7").split(",")]
PMIN = int(os.environ.get("PFS_WALK_PMIN", "0"))
log = H.log


def sparse_rank_mod(rows, q):
    """rank over GF(q) of rows given as dicts col -> int: dense vectorised Gauss-Jordan in int64 (q < 2^31)."""
    import numpy as np
    if not rows:
        return 0
    ncol = 1 + max(c for r in rows for c in r)
    M = np.zeros((len(rows), ncol), dtype=np.int64)
    for i, r in enumerate(rows):
        for c, v in r.items():
            M[i, c] = v % q
    rank, row = 0, 0
    for col in range(ncol):
        if row >= M.shape[0]:
            break
        piv = np.nonzero(M[row:, col])[0]
        if len(piv) == 0:
            continue
        p0 = row + int(piv[0])
        if p0 != row:
            M[[row, p0]] = M[[p0, row]]
        inv = pow(int(M[row, col]), q - 2, q)
        M[row] = (M[row] * inv) % q
        others = np.nonzero(M[:, col])[0]
        others = others[others != row]
        if len(others):
            M[others] = (M[others] - np.outer(M[others, col], M[row])) % q
        row += 1
        rank += 1
    return rank


def choose_prime():
    """p = (u^2 + f^2 |D_K|)/4 prime, u even when needed, not 11 or a Hecke prime, p >= PMIN."""
    c = F * F * (-DK)
    u = 0 if c % 4 == 0 else 1
    while True:
        if (u * u + c) % 4 == 0:
            p = (u * u + c) // 4
            if p >= PMIN and is_prime(p) and p not in (2, 3, 5, 11) and p not in LS:
                return int(p), int(u)
        u += 1


def main():
    t0 = time.time()
    p, u = choose_prime()
    log(f"D_K={DK} f={F} -> p={p} u={u} (|u| < 2 sqrt p = {2*math.sqrt(p):.0f})")
    funcs, jfun = H.build(LS)
    Rd = H.Reduced(p, funcs, jfun, LS)
    E, Fp = Rd.E, Rd.Fp
    n = int(E.order())
    nprime = int(max(q for q, _ in factor(n)))
    log(f"#E(F_p) = {n} = {factor(n)}; largest prime {nprime}")
    # CM j-invariant(s) of discriminant D_K over F_p
    Hpol = hilbert_class_polynomial(DK).change_ring(Fp)
    js = Hpol.roots(multiplicities=False)
    assert js, "no CM j over F_p"
    starts = []
    for j0 in js:
        tr = abs(int(EllipticCurve_from_j(j0).trace_of_frobenius()))
        assert tr == u, (tr, u)
        starts.extend(Rd.points_with_j(j0))
    log(f"{len(js)} CM j-invariant(s), {len(starts)} rational point(s) of X_0(11) above them")
    if not starts:
        # j = 0 or 1728 is ramified on X_0(11) -> X(1) and may carry no rational point; sample a class member instead
        rs = random.Random(p)
        tried = 0
        while not starts and tried < 200000:
            tried += 1
            P = E.random_point()
            jj = Rd.j(P)
            if jj is None or jj in (0, 1728):
                continue
            if abs(int(EllipticCurve_from_j(jj).trace_of_frobenius())) == u:
                starts.append(P)
        log(f"  random start found after {tried} samples")
    # walk
    trace_cache = {}

    def in_class(P):
        j = Rd.j(P)
        if j is None or j == 0 or j == 1728:
            return False
        if j not in trace_cache:
            trace_cache[j] = abs(int(EllipticCurve_from_j(j).trace_of_frobenius()))
        return trace_cache[j] == u

    seen = {P for P in starts}
    frontier = list(starts)
    nrat = {l: {} for l in LS}
    while frontier:
        nxt = []
        for P in frontier:
            for l in LS:
                cands = Rd.neighbour_candidates(l, P)
                k = len(set(Q[0] for Q in cands))
                nrat[l][k] = nrat[l].get(k, 0) + 1
                for Q in cands:
                    if Q not in seen and in_class(Q):
                        seen.add(Q)
                        nxt.append(Q)
        frontier = nxt
        log(f"  class so far {len(seen)} points, frontier {len(frontier)} ({time.time()-t0:.0f}s)")
    C = sorted(seen, key=lambda P: (int(P[0]), int(P[1])))
    idx = {P: i for i, P in enumerate(C)}
    # relations
    rows, per_l, verified = [], {l: 0 for l in LS}, {l: [0, 0] for l in LS}
    for P in C:
        for l in LS:
            nb = Rd.neighbours_all(l, P)
            if nb is None:
                continue
            verified[l][0] += 1
            if sum(nb, E(0)) != Rd.a_l[l] * P:
                continue
            verified[l][1] += 1
            if all(Q in idx for Q in nb):
                r = {}
                for Q in nb:
                    r[idx[Q]] = r.get(idx[Q], 0) + 1
                r[idx[P]] = r.get(idx[P], 0) - Rd.a_l[l]
                rows.append(r)
                per_l[l] += 1
    Fn = GF(nprime)
    BIG = 2147483647                           # rank mod a large prime = rank over Q with overwhelming probability
    rk = sparse_rank_mod(rows, BIG)
    rk_n = sparse_rank_mod(rows, nprime)
    out = dict(DK=DK, f=F, p=p, u=u, n=n, n_factor=str(factor(n)), nprime=nprime, hecke_primes=LS,
               class_size=len(C), distinct_j=len(trace_cache), relations=len(rows), relations_per_l={str(l): v for l, v in per_l.items()},
               verified={str(l): f"{v[1]}/{v[0]}" for l, v in verified.items()},
               rank=int(rk), rank_mod_nprime=int(rk_n), deficiency=len(C) - 1 - int(rk), deficiency_fraction=(len(C) - 1 - int(rk)) / max(1, len(C)),
               relation_density=len(rows) / max(1, len(C)),
               rational_neighbour_counts={str(l): {str(k): v for k, v in sorted(d.items())} for l, d in nrat.items()},
               sqrt_p=math.sqrt(p), class_over_sqrtp=len(C) / math.sqrt(p))
    # Retain the actual matrix for an independent rank and pivot audit.
    out["column_points"] = [str(P) for P in C]
    out["relation_rows"] = [{str(c): int(v) for c, v in row.items()} for row in rows]
    # Atkin-Lehner: find eps, t with Phi_11(j(z), j(eps z + t)) = 0 for sample points
    try:
        Phi11 = pari.polmodular(11)
        Rxy = PolynomialRing(Fp, ['X', 'Y'])
        Phi = Rxy(str(Phi11).replace('x', 'X').replace('y', 'Y'))
        # the rational 5-torsion of 11a1 reduces to (5,5),(5,-6),(16,60),(16,-61)
        tors = [E(0)] + [E(Fp(5), Fp(5)), E(Fp(5), Fp(-6)), E(Fp(16), Fp(60)), E(Fp(16), Fp(-61))]
        sample = random.Random(1).sample(C, min(12, len(C)))
        found = None
        for eps in (1, -1):
            for t in tors:
                ok = 0
                for z in sample:
                    w = eps * z + t
                    jw, jz = Rd.j(w), Rd.j(z)
                    if jw is not None and jz is not None and Phi(jz, jw) == 0:
                        ok += 1
                if ok == len(sample):
                    found = (eps, t)
        if found:
            eps, t = found
            rows_w = []
            for P in C:
                w = eps * P + t
                if w in idx:
                    r = {idx[w]: 1}
                    r[idx[P]] = r.get(idx[P], 0) - eps
                    rows_w.append(r)
            rk2 = sparse_rank_mod(rows + rows_w, BIG)
            out["atkin_lehner_rows"] = [{str(c): int(v) for c, v in row.items()} for row in rows_w]
            out["atkin_lehner"] = dict(eps=eps, t=str(t), relations=len(rows_w), rank_with=int(rk2),
                                       deficiency_with=len(C) - 1 - int(rk2))
        else:
            out["atkin_lehner"] = "not identified among eps z + t"
    except Exception as ex:   # noqa
        out["atkin_lehner"] = f"skipped: {ex}"
    out["seconds"] = time.time() - t0
    json.dump(out, open(OUT, "w"), indent=1, default=str)
    print(json.dumps({k: v for k, v in out.items() if k not in ("rational_neighbour_counts",)}, indent=1, default=str))
    print("rational neighbour counts per l:", out["rational_neighbour_counts"])
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
