"""Chosen-base zero relations via trace coordinates and univariate fibers.

The base consists of actual known-labeled prime-field trace points. Extension
lifts never replace the condition that all three traces belong to this base.
Product trees keep each fiber's polynomial degrees <= 2*B without constructing
a bivariate/global elimination polynomial. This is O~(B^2), not a subquadratic
relation algorithm. The independent batched-pair control is in joint/zero_pairs.
"""
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'joint'))
from flint import nmod_poly
from zero_fiber import canonical_pm


def product_tree_mod_quadratic(xs, q0, q1, p):
    """Product (Z-x) in F_p[m][Z]/(Z^2+q1(m)Z+q0(m))."""
    nodes = [(nmod_poly([-x], p), nmod_poly([1], p)) for x in xs]
    if not nodes:
        return nmod_poly([1], p), nmod_poly([], p)
    while len(nodes) > 1:
        nxt = []
        for i in range(0, len(nodes)-1, 2):
            a0, a1 = nodes[i]; b0, b1 = nodes[i+1]
            c00, c11 = a0*b0, a1*b1
            cross = (a0+a1)*(b0+b1)-c00-c11
            nxt.append((c00-q0*c11, cross-q1*c11))
        if len(nodes) & 1:
            nxt.append(nodes[-1])
        nodes = nxt
    return nodes[0]


def trace_fibers(E, xs):
    start = time.process_time()
    p = E.p; m = nmod_poly([0, 1], p)
    points = [E.lift(x) for x in sorted(set(xs))]
    points = [P for P in points if P is not None]
    xs = [P[0] for P in points]
    relations = set(); max_degree = 0; roots_seen = 0
    compose = roots_cpu = verify = 0.0
    for X, Y in points:
        tick = time.process_time()
        # The line through (X,Y) is y=m*x+Y-m*X. Divide its intersection
        # cubic by x-X, leaving the two other trace abscissae.
        q0 = X*X + X*m*m - 2*Y*m + E.a
        q1 = X-m*m
        r0, r1 = product_tree_mod_quadratic(xs, q0, q1, p)
        max_degree = max(max_degree, int(r0.degree()), int(r1.degree()))
        common = r0.gcd(r1)
        if common.is_zero():
            raise RuntimeError('Positive-dimensional line fiber')
        compose += time.process_time()-tick
        tick = time.process_time()
        if common.degree() > 0:
            common = common.gcd(m.pow_mod(p, common)-m)
        slopes = common.roots() if common.degree() > 0 else []
        roots_seen += len(slopes)
        roots_cpu += time.process_time()-tick
        tick = time.process_time()
        for slope, _ in slopes:
            slope = int(slope)
            q = nmod_poly([X*X+X*slope*slope-2*Y*slope+E.a,
                           X-slope*slope, 1], p)
            rr = q.roots()
            if len(rr) != 2 or any(mult != 1 for _, mult in rr):
                continue
            xx = [int(z) for z, _ in rr]
            if X in xx or any(z not in xs for z in xx):
                continue
            n = (Y-slope*X) % p
            relation = canonical_pm(E, [(X, Y)] +
                                    [(z, (slope*z+n) % p) for z in xx])
            assert E.sum(relation) is None
            assert all(E.contains(P) for P in relation)
            relations.add(relation)
        verify += time.process_time()-tick
    assert max_degree <= 2*len(xs)
    return {'relations': relations, 'cpu_s': time.process_time()-start,
            'compose_gcd_cpu_s': compose, 'root_cpu_s': roots_cpu,
            'verify_cpu_s': verify, 'fibers': len(xs),
            'max_polynomial_degree': max_degree,
            'slope_roots': roots_seen}


def linear_solve(rows, rhs, p):
    """Unique solution of an overdetermined F_p system, or None."""
    if not rows:
        return None
    width = len(rows[0]); matrix = [[x % p for x in r]+[v % p]
                                  for r, v in zip(rows, rhs)]
    pivots = []; rank = 0
    for j in range(width):
        found = next((i for i in range(rank, len(matrix)) if matrix[i][j]), None)
        if found is None:
            continue
        matrix[rank], matrix[found] = matrix[found], matrix[rank]
        inv = pow(matrix[rank][j], -1, p)
        matrix[rank] = [v*inv % p for v in matrix[rank]]
        for i in range(len(matrix)):
            if i == rank:
                continue
            scale = matrix[i][j]
            if scale:
                matrix[i] = [(a-scale*b) % p for a, b in zip(matrix[i], matrix[rank])]
        pivots.append(j); rank += 1
    if any(all(v == 0 for v in r[:width]) and r[-1] for r in matrix):
        return None
    if rank != width:
        return None
    answer = [0]*width
    for i, j in enumerate(pivots):
        answer[j] = matrix[i][-1]
    return answer
