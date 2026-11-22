"""Constant-degree cubic-orbit lifts; labels belong to elliptic traces.

Fix c != 0 and d. The orbit abscissa polynomial is Z^3+h*Z^2+d*Z-c.
The quartic projection below finds all nonexceptional interpolation parameters
and explicitly handles a zero denominator. All actual returned orbits can be
embedded in one fixed F_(p^3); this cost is separately measurable.
"""
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flint import nmod_poly, fq_default_ctx, fq_default_poly_ctx
from core import q_coefficients, sqrt_mod


def field_point_add(E, P, Q):
    if P is None:
        return Q
    if Q is None:
        return P
    x, y = P; xx, yy = Q
    if x == xx:
        if (y+yy).is_zero():
            return None
        slope = (3*x*x+E.a)/(2*y)
    else:
        slope = (yy-y)/(xx-x)
    rx = slope*slope-x-xx
    return rx, slope*(x-rx)-y


def field_point_sum(E, points):
    total = None
    for P in points:
        total = field_point_add(E, total, P)
    return total


def irreducible_cubic(coeff, p):
    q = nmod_poly(coeff, p); z = nmod_poly([0, 1], p)
    return q.gcd(z.pow_mod(p, q)-z).degree() == 0


def lift_parameters(E, T, c=1, d=0):
    """All parameters whose cubic has q0=-c, q1=d and is irreducible.

    A nonidentity point in an odd prime-order full group has Y != 0. Inputs
    with Y=0 are rejected explicitly rather than hiding a costly fallback.
    """
    start = time.process_time()
    p = E.p; X, Y = T; c %= p; d %= p
    assert p > 3 and c
    if Y == 0:
        raise ValueError('Order-two input is outside the odd-prime-group fixture')
    w = nmod_poly([0, 1], p)
    D = 2*(Y*w-X*X)
    N = (2*X*X+E.a)*w*w-4*X*Y*w+2*X**3+X*d-c
    K = X*w*w-2*Y*w+X*X+d
    H = N*N-D*D*K
    if H.is_zero():
        raise RuntimeError('Positive-dimensional quartic projection')
    assert H.degree() <= 4
    roots = H.gcd(w.pow_mod(p, H)-w).roots() if H.degree() > 0 else []
    pairs = set(); denominator_exceptions = 0
    for value, _ in roots:
        value = int(value); dd = 2*(Y*value-X*X) % p
        nn = int(N(value))
        if dd:
            pairs.add((nn*pow(dd, -1, p) % p, value))
        elif nn == 0:
            denominator_exceptions += 1
            root = sqrt_mod(int(K(value)), p)
            if root is not None:
                pairs.update((u, value) for u in {root, -root % p})
    candidates = []; reducible = 0
    for u, value in sorted(pairs):
        coeff = q_coefficients(E, T, u, value)
        if coeff[0] != -c % p or coeff[1] != d:
            continue
        if not irreducible_cubic(coeff, p):
            reducible += 1
            continue
        assert value != 0
        candidates.append({'u': u, 'w': value, 'h': coeff[2], 'q': coeff})
    return {'candidates': candidates, 'quartic_degree': int(H.degree()),
            'projected_roots': len(roots), 'reducible_candidates': reducible,
            'denominator_exceptions': denominator_exceptions,
            'cpu_s': time.process_time()-start}


class CommonCubicField:
    def __init__(self, p):
        tick = time.process_time()
        self.K = fq_default_ctx(p, 3, 'z')
        self.polys = fq_default_poly_ctx(self.K)
        self.p = p
        self.cpu_s = time.process_time()-tick

    def embed(self, E, T, candidate):
        """Extract a root in a common field; do not pretend formal roots agree."""
        tick = time.process_time()
        roots = self.polys(candidate['q']).roots()
        assert len(roots) == 3 and all(mult == 1 for _, mult in roots)
        x = min((root for root, _ in roots), key=lambda z: list(map(int, z.to_list())))
        X, Y = T; u, w = candidate['u'], candidate['w']
        v = (w*Y-X*X-u*X) % self.p
        y = -(x*x+u*x+v)/w
        R = (x, y)
        assert y*y == x*x*x+E.a*x+E.b
        orbit = [R]
        orbit.append(tuple(z.frobenius() for z in orbit[-1]))
        orbit.append(tuple(z.frobenius() for z in orbit[-1]))
        assert tuple(z.frobenius() for z in orbit[-1]) == R
        assert field_point_sum(E, orbit) == (self.K(T[0]), self.K(T[1]))
        return {'point': R, 'orbit': orbit,
                'cpu_s': time.process_time()-tick,
                'coordinates': [list(map(int, x.to_list())), list(map(int, y.to_list()))]}
