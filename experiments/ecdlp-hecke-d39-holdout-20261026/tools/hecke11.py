"""Shared machinery for X_0(11) = 11a1: Hecke images T_l(x^k), T_l(x^k y) and j as explicit rational functions,
from the q-expansion of the modular parametrisation (Sage).  Used by exp10 and exp11."""
import sys, time
from sage.all import EllipticCurve, QQ, GF, PolynomialRing, matrix, vector, j_invariant_qexp

E0 = EllipticCurve('11a1')
AINV = [0, -1, 1, -10, -20]


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def laurent_dict(s):
    return {int(e): QQ(c) for e, c in zip(s.exponents(), s.coefficients())}


def hecke_series(gd, l, prec_out):
    out = {}
    for m, c in gd.items():
        if m * l < prec_out:
            out[m * l] = out.get(m * l, 0) + c
        if m % l == 0 and m // l < prec_out:
            out[m // l] = out.get(m // l, 0) + l * c
    return out


def basis_L(m):
    return [(a, b) for b in (0, 1) for a in range(0, m // 2 + 1) if 2 * a + 3 * b <= m]


def identify(target, m, mono_q, prec_out, surplus=10):
    B = basis_L(m)
    rows = list(range(-m, prec_out))
    assert len(rows) >= len(B) + surplus, f"not enough q-precision for L({m}O): {len(rows)} rows, {len(B)} unknowns"
    M = matrix(QQ, [[mono_q[(a, b)].get(e, 0) for (a, b) in B] for e in rows])
    v = vector(QQ, [target.get(e, 0) for e in rows])
    sol = M.solve_right(v)
    assert M * sol == v
    return {B[i]: sol[i] for i in range(len(B)) if sol[i] != 0}


def poly_from_dict(d, ring):
    return sum(ring(c) * ring.gen(0) ** a * ring.gen(1) ** b for (a, b), c in d.items()) if d else ring(0)


def build(LS, prec=None):
    """returns (funcs, jfun): funcs[(l,'x',k)] / funcs[(l,'xy',k)] coefficient dicts over Q; jfun = (A, x0, cusp)."""
    lmax = max(LS)
    maxpole = 2 * (lmax + 1) * lmax + 12
    if prec is None:
        prec = lmax * (maxpole + 16) + 40
    t0 = time.time()
    X, Y = E0.modular_parametrization().power_series(prec=prec)
    Lq = X.parent()
    mono_q = {}
    Xpow = [Lq(1)]
    for a in range(1, maxpole // 2 + 2):
        Xpow.append(Xpow[-1] * X)
    for a in range(0, maxpole // 2 + 2):
        mono_q[(a, 0)] = laurent_dict(Xpow[a])
        mono_q[(a, 1)] = laurent_dict(Xpow[a] * Y)
    log(f"  q-expansions to O(q^{prec}) ready ({time.time()-t0:.1f}s)")
    funcs = {}
    for l in LS:
        prec_out = (prec - 2 * (l + 1) - 6) // l - 2
        for k in range(1, l + 2):
            funcs[(l, 'x', k)] = identify(hecke_series(laurent_dict(Xpow[k]), l, prec_out), 2 * k * l, mono_q, prec_out)
        for k in range(0, l + 1):
            funcs[(l, 'xy', k)] = identify(hecke_series(laurent_dict(Xpow[k] * Y), l, prec_out), l * (2 * k + 3), mono_q, prec_out)
        log(f"  Hecke functions for l={l} identified ({time.time()-t0:.1f}s)")
    jq = laurent_dict(j_invariant_qexp(min(prec, 400) - 30))
    jfun = None
    for T in E0.torsion_points():
        if T.is_zero():
            continue
        x0 = QQ(T[0])
        den = laurent_dict((X - x0) ** 11)
        tgt = {}
        lim = min(prec, 400) - 60
        for e1, c1 in jq.items():
            for e2, c2 in den.items():
                if e1 + e2 < lim:
                    tgt[e1 + e2] = tgt.get(e1 + e2, 0) + c1 * c2
        try:
            A = identify(tgt, 23, mono_q, lim - 10)
            jfun = (A, x0, T)
            log(f"  cusp 0 is {T}; j = A/(x - {x0})^11")
            break
        except (ValueError, AssertionError):
            continue
    assert jfun is not None
    return funcs, jfun


class Reduced:
    """everything reduced to F_p: evaluation of j, Hecke neighbours, class labels."""

    def __init__(self, p, funcs, jfun, LS):
        self.p, self.LS = p, LS
        self.Fp = GF(p)
        self.E = EllipticCurve(self.Fp, AINV)
        self.R = PolynomialRing(self.Fp, ['x', 'y'])
        self.funcs = {k: poly_from_dict(v, self.R) for k, v in funcs.items()}
        A, x0, _ = jfun
        self.A = poly_from_dict(A, self.R)
        self.x0 = self.Fp(x0)
        self.a_l = {l: int(E0.ap(l)) for l in LS}
        self.PT = PolynomialRing(self.Fp, 'T')

    def j(self, P):
        if P.is_zero() or P[0] == self.x0:
            return None
        return self.A(P[0], P[1]) / (P[0] - self.x0) ** 11

    def points_with_j(self, j0):
        """all points z of E(F_p) with j(z) = j0: A0(x) + A1(x) y = j0 (x - x0)^11 on the curve."""
        Rx = PolynomialRing(self.Fp, 'X')
        Xv = Rx.gen()
        A0 = sum(c * Xv ** a for (a, b), c in self.A.dict().items() if b == 0) if True else 0
        A1 = sum(c * Xv ** a for (a, b), c in self.A.dict().items() if b == 1)
        A0 = Rx(sum((self.Fp(c) * Xv ** int(a)) for (a, b), c in self.A.dict().items() if b == 0))
        A1 = Rx(sum((self.Fp(c) * Xv ** int(a)) for (a, b), c in self.A.dict().items() if b == 1))
        rhs = j0 * (Xv - self.x0) ** 11
        # y = (rhs - A0)/A1 ; curve: y^2 + y = x^3 - x^2 - 10x - 20  ->  (rhs-A0)^2 + (rhs-A0) A1 - A1^2 (x^3 - x^2 - 10x - 20) = 0
        num = (rhs - A0) ** 2 + (rhs - A0) * A1 - A1 ** 2 * (Xv ** 3 - Xv ** 2 - 10 * Xv - 20)
        pts = []
        for r in num.roots(multiplicities=False):
            if A1(r) == 0:
                for P in self.E.lift_x(r, all=True):
                    if self.j(P) == j0:
                        pts.append(P)
            else:
                yv = (rhs(r) - A0(r)) / A1(r)
                try:
                    P = self.E(r, yv)
                except (TypeError, ValueError):
                    continue
                if self.j(P) == j0:
                    pts.append(P)
        return pts

    def neighbour_x(self, l, P):
        """the degree-(l+1) polynomial whose roots are the x-coordinates of the l-isogenous neighbours."""
        s = [None] + [self.funcs[(l, 'x', k)](P[0], P[1]) for k in range(1, l + 2)]
        d = l + 1
        e = [self.Fp(1)] + [self.Fp(0)] * d
        for k in range(1, d + 1):
            acc = self.Fp(0)
            for i in range(1, k + 1):
                acc += (-1) ** (i - 1) * e[k - i] * s[i]
            e[k] = acc / self.Fp(k)
        T = self.PT.gen()
        return sum((-1) ** k * e[k] * T ** (d - k) for k in range(d + 1))

    def neighbours_all(self, l, P):
        """all l+1 neighbours if every one is F_p-rational (distinct x), else None."""
        roots = self.neighbour_x(l, P).roots(multiplicities=False)
        if len(roots) != l + 1:
            return None
        t = [self.funcs[(l, 'xy', k)](P[0], P[1]) for k in range(0, l + 1)]
        V = matrix(self.Fp, [[r ** k for r in roots] for k in range(l + 1)])
        ys = V.solve_right(vector(self.Fp, t))
        pts = []
        for r, yy in zip(roots, ys):
            try:
                pts.append(self.E(r, yy))
            except (TypeError, ValueError):
                return None
        return pts

    def neighbour_candidates(self, l, P):
        """points above the F_p-rational neighbour x-coordinates (both y's), for graph walking."""
        out = []
        for r in self.neighbour_x(l, P).roots(multiplicities=False):
            out.extend(self.E.lift_x(r, all=True))
        return out
