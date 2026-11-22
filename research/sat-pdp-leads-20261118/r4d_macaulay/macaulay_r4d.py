#!/usr/bin/env python3
"""Round-4 D measurement: affine Macaulay matrices of the bilinear leaf system.

Field F = GF(2)[z]/(f), n odd; curve y^2 + xy = x^3 + x^2 + B; target abscissa xR.
Unknown bits: T block t (n bits, t = x(R - P1)); Q block x1 (l bits, x1 in V),
s (l bits, s in V), p (2l-1 bits, p in span(1..z^(2l-2))).
Equations (each an F-identity = n F2 equations), with B the curve constant:
  E1 = S3(x1, t, xR) = (x1 t)^2 + (x1 xR)^2 + (t xR)^2 + xR x1 t + B
  E2 = S3(x2, x3, t) with s = x2+x3, p = x2 x3: p^2 + t^2 s^2 + p t + B
Both are F2-bilinear in (T; Q) plus affine terms (squaring is F2-linear).

Macaulay matrix at bidegree (A, B): rows f*m for every equation f and every
multilinear monomial m with t-degree <= A-1 and q-degree <= B-1 (field
equations applied: v^2 = v); columns = multilinear monomials with t-degree <= A,
q-degree <= B. Columns ordered by total degree descending, linear and constant
last, so after elimination the rows living only on degree <= 1 columns are the
linear relations the matrix certifies.

Measured: rank, columns, L = number of independent linear relations obtained,
and L_max = N - dim aff(S), where S is the exact relaxed solution set
(computed independently: for each x1 in V, t ranges over the <= 2 roots of
E1 in t, then E2 is F2-linear in (s, p)). "Solved at (A, B)" iff L == L_max.
A random bilinear system with the same shape is the null control.
"""
import itertools, json, random, sys, time
sys.path.insert(0, '../l3_torsion_count')
import count_t0_relations as m


class Sys:
    """Polynomials over F2 as dict-free sets of monomials; monomial = frozenset of var ids.
    Var ids: t_i -> i (0..n-1); q_j -> n + j."""

    def __init__(self, n, l, seed, random_null=False, planted_eqs=0):
        self.n, self.l = n, l
        F = self.F = m.Field(n)
        rng = random.Random(f"r4d-{n}-{l}-{seed}")
        self.B = rng.randrange(1, 1 << n)
        self.xR = rng.randrange(1 << l, 1 << n)
        self.nT = n
        self.ql = [("x1", i, 1 << i) for i in range(l)] + [("s", i, 1 << i) for i in range(l)] + \
                  [("p", i, 1 << i) for i in range(2 * l - 1)]
        self.nQ = len(self.ql)
        self.N = self.nT + self.nQ
        self.planted = None
        if planted_eqs:
            self.planted = rng.getrandbits(self.N)
            self.eqs = self.random_bilinear(rng, planted_eqs)
            for e in self.eqs:                      # fix constant so the planted vector satisfies e
                if self.eval(e, self.planted): e ^= {frozenset()}
        elif random_null:
            self.eqs = self.random_bilinear(rng)
        else:
            self.eqs = self.build()

    # coordinate expansion: an F element linear in some bits -> per output bit, set of vars
    def build(self):
        F, n = self.F, self.n
        T = [1 << i for i in range(n)]
        qx1 = [i for i, (nm, _, _) in enumerate(self.ql) if nm == "x1"]
        qs = [i for i, (nm, _, _) in enumerate(self.ql) if nm == "s"]
        qp = [i for i, (nm, _, _) in enumerate(self.ql) if nm == "p"]
        basisQ = [e for (_, _, e) in self.ql]
        eqs1 = [set() for _ in range(n)]
        eqs2 = [set() for _ in range(n)]

        def addelem(eqs, val, mono):
            for b in range(n):
                if val >> b & 1:
                    eqs[b] ^= {mono}
        xR, B = self.xR, self.B
        # E1 = (x1 t)^2 + xR x1 t + (x1 xR)^2 + (t xR)^2 + B
        for j in qx1:
            for i in range(n):
                prod = F.mul(basisQ[j], T[i])
                addelem(eqs1, F.sq(prod) ^ F.mul(xR, prod), frozenset({i, n + j}))
            addelem(eqs1, F.sq(F.mul(basisQ[j], xR)), frozenset({n + j}))
        for i in range(n):
            addelem(eqs1, F.sq(F.mul(T[i], xR)), frozenset({i}))
        addelem(eqs1, B, frozenset())
        # E2 = p^2 + t^2 s^2 + p t + B
        for j in qp:
            addelem(eqs2, F.sq(basisQ[j]), frozenset({n + j}))
            for i in range(n):
                addelem(eqs2, F.mul(basisQ[j], T[i]), frozenset({i, n + j}))
        for j in qs:
            for i in range(n):
                addelem(eqs2, F.sq(F.mul(basisQ[j], T[i])), frozenset({i, n + j}))
        addelem(eqs2, B, frozenset())
        return [e for e in eqs1 + eqs2 if e]

    def random_bilinear(self, rng, count=None):
        eqs = []
        for _ in range(count or 2 * self.n):
            e = set()
            for i in range(self.nT):
                for j in range(self.nQ):
                    if rng.random() < 0.5: e ^= {frozenset({i, self.nT + j})}
            for v in range(self.N):
                if rng.random() < 0.5: e ^= {frozenset({v})}
            if rng.random() < 0.5: e ^= {frozenset()}
            eqs.append(e)
        return eqs

    def solutions(self):
        """Exact relaxed solution set of the real system (as N-bit ints)."""
        F, n, l, xR = self.F, self.n, self.l, self.xR
        sols = []
        # brute force over x1 (l bits) and t via evaluation of E1 is 2^(l+n): use structure:
        for x1bits in range(1 << l):
            x1 = x1bits  # x1 in V, polynomial basis z^i -> bit i
            # E1 as function of t: (x1 t)^2 + xR x1 t + (x1 xR)^2 + (t xR)^2 + B ; enumerate t (2^n, n<=17 ok)
            cand_t = []
            a2 = F.sq(F.mul(x1, xR)) ^ self.B
            for t in range(1 << n):
                xt = F.mul(x1, t)
                if F.sq(xt) ^ F.mul(xR, xt) ^ F.sq(F.mul(t, xR)) ^ a2 == 0:
                    cand_t.append(t)
            for t in cand_t:
                # E2 linear in (s,p): p^2 + t^2 s^2 + p t + B = 0
                cols = []
                for i in range(l):
                    cols.append(F.sq(F.mul(1 << i, t)))
                for j in range(2 * l - 1):
                    cols.append(F.sq(1 << j) ^ F.mul(1 << j, t))
                # solve sum c_k cols[k] = B over F2^n
                k = len(cols)
                for mask in range(1 << k):  # k = 3l-1 <= 14: fine
                    acc = 0
                    for b in range(k):
                        if mask >> b & 1: acc ^= cols[b]
                    if acc == self.B:
                        svec = mask & ((1 << l) - 1); pvec = mask >> l
                        bits = t | (x1bits << n) | (svec << (n + l)) | (pvec << (n + 2 * l))
                        sols.append(bits)
        return sols

    def eval(self, eq, bits):
        v = 0
        for mono in eq:
            if all(bits >> x & 1 for x in mono): v ^= 1
        return v


def aff_dim(sols, N):
    if not sols: return -1
    base = sols[0]; rows = []
    for s in sols[1:]:
        r = s ^ base
        for b in rows:
            r = min(r, r ^ b)
        if r: rows.append(r); rows.sort(reverse=True)
    return len(rows)


def monos_upto(nT, nQ, A, B):
    out = []
    for a in range(A + 1):
        for b in range(B + 1):
            for ts in itertools.combinations(range(nT), a):
                for qs in itertools.combinations(range(nT, nT + nQ), b):
                    out.append(frozenset(ts + qs))
    return out


def macaulay(S, A, B, time_cap=900, sols=None):
    nT, nQ, N = S.nT, S.nQ, S.N
    cols = monos_upto(nT, nQ, A, B)
    cols.sort(key=lambda mo: (-len(mo), sorted(mo)))
    idx = {mo: i for i, mo in enumerate(cols)}
    ncol = len(cols)
    lin_start = sum(1 for mo in cols if len(mo) >= 2)   # first column of degree <= 1
    mults = monos_upto(nT, nQ, max(A - 1, 0), max(B - 1, 0)) if A >= 1 and B >= 1 else [frozenset()]
    # bit k of row int <-> column (ncol-1-k): make leading = highest column index 0
    pivots = {}
    t0 = time.time(); nrows = 0
    for f in S.eqs:
        for mu in mults:
            r = 0
            for mono in f:
                mm = mono | mu
                # bidegree check (field eqs already applied by set union)
                ta = sum(1 for x in mm if x < nT); qb = len(mm) - ta
                if ta > A or qb > B:
                    r = None; break
                r ^= 1 << (ncol - 1 - idx[mm])
            if r is None or r == 0:
                continue
            nrows += 1
            while r:
                h = r.bit_length() - 1
                if h in pivots:
                    r ^= pivots[h]
                else:
                    pivots[h] = r
                    break
            if time.time() - t0 > time_cap:
                return {"A": A, "B": B, "cols": ncol, "rows": nrows, "rank": len(pivots), "timeout": True}
    rank = len(pivots)
    if sols is not None:   # every certified linear relation must vanish on every true solution
        lin_cut0 = ncol - sum(1 for mo in cols if len(mo) >= 2)
        for h, row in pivots.items():
            if h < lin_cut0:
                for x in sols:
                    v = 0
                    for k in range(lin_cut0):
                        if row >> k & 1:
                            mo = cols[ncol - 1 - k]
                            if all(x >> y & 1 for y in mo): v ^= 1
                    assert v == 0, "certified linear relation fails on a true solution"
    # linear relations: pivot rows whose leading column is a degree<=1 column
    lin_cut = ncol - lin_start   # bits below lin_cut are degree<=1 columns
    L = sum(1 for h in pivots if h < lin_cut and h > 0)  # exclude the constant column (h == 0) -> inconsistency
    inconsistent = 0 in pivots
    return {"A": A, "B": B, "cols": ncol, "rows": nrows, "rank": rank, "L": L,
            "inconsistent": inconsistent, "secs": round(time.time() - t0, 2), "timeout": False}


def run_cell(n, l, seed, kind, bidegs=((1, 1), (1, 2), (2, 1), (2, 2)), cap=900):
    if kind == "real":
        S = Sys(n, l, seed)
        sols = S.solutions()
        assert all(S.eval(e, x) == 0 for x in sols for e in S.eqs), "solution check failed"
        d = aff_dim(sols, S.N); Lmax = S.N - d if d >= 0 else S.N + 1
    elif kind == "planted":
        S = Sys(n, l, seed, planted_eqs=3 * (n + 3 * l - 1 + l))   # 3N equations
        sols = [S.planted]; Lmax = S.N      # solution set {planted} with high probability
    else:
        S = Sys(n, l, seed, random_null=True); sols = None; Lmax = None
    head = {"kind": kind, "n": n, "l": l, "seed": seed, "N": S.N, "eqs": len(S.eqs),
            "solutions": len(sols) if sols is not None else None, "L_max": Lmax}
    out = []
    for (A, B) in bidegs:
        r = macaulay(S, A, B, cap, sols)
        r.update(head); r["solved"] = (Lmax is not None and r.get("L") == Lmax)
        out.append(r); print(json.dumps(r), flush=True)
    return out


if __name__ == "__main__":
    n, l, seed, kind = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    run_cell(n, l, seed, kind)
