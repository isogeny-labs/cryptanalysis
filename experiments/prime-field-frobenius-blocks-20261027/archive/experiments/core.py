"""Exact arithmetic and independent relation oracle. Python 3, no dependencies."""
from itertools import combinations, product
from math import isqrt


def is_prime(n):
    if n < 2:
        return False
    for d in range(2, isqrt(n) + 1):
        if n % d == 0:
            return False
    return True


def sqrt_mod(a, p):
    a %= p
    if a == 0:
        return 0
    if pow(a, (p - 1) // 2, p) != 1:
        return None
    if p % 4 == 3:
        return pow(a, (p + 1) // 4, p)
    q, s = p - 1, 0
    while q % 2 == 0:
        q //= 2
        s += 1
    z = 2
    while pow(z, (p - 1) // 2, p) != p - 1:
        z += 1
    c, x, t, m = pow(z, q, p), pow(a, (q + 1) // 2, p), pow(a, q, p), s
    while t != 1:
        i, tt = 0, t
        while tt != 1:
            tt = tt * tt % p
            i += 1
        b = pow(c, 1 << (m - i - 1), p)
        x, t, c, m = x*b % p, t*b*b % p, b*b % p, i
    return x


class Curve:
    def __init__(self, p, a, b):
        self.p, self.a, self.b = p, a % p, b % p
        assert (4*a**3 + 27*b**2) % p != 0

    def lift(self, x):
        y = sqrt_mod(x**3 + self.a*x + self.b, self.p)
        return None if y is None else (x % self.p, y)

    def contains(self, point):
        if point is None:
            return True
        x, y = point
        return (y*y - x**3 - self.a*x - self.b) % self.p == 0

    def neg(self, point):
        return None if point is None else (point[0], -point[1] % self.p)

    def add(self, P, Q):
        if P is None:
            return Q
        if Q is None:
            return P
        p = self.p
        x, y = P
        xx, yy = Q
        if x == xx:
            if (y + yy) % p == 0:
                return None
            slope = (3*x*x + self.a)*pow(2*y, -1, p) % p
        else:
            slope = (yy-y)*pow(xx-x, -1, p) % p
        rx = (slope*slope-x-xx) % p
        return rx, (slope*(x-rx)-y) % p

    def mul(self, n, P):
        if n < 0:
            return self.mul(-n, self.neg(P))
        R = None
        while n:
            if n & 1:
                R = self.add(R, P)
            P = self.add(P, P)
            n >>= 1
        return R

    def sum(self, points):
        R = None
        for P in points:
            R = self.add(R, P)
        return R

    def points(self):
        for x in range(self.p):
            P = self.lift(x)
            if P is not None:
                yield P
                if P[1]:
                    yield self.neg(P)


def prime_order_curve(p):
    """Test-fixture selection, separately charged from input-specific setup."""
    squares = [0]*p
    for y in range(p):
        squares[y*y % p] += 1
    for a in range(1, 12):
        for b in range(1, 80):
            if (4*a**3 + 27*b*b) % p == 0:
                continue
            n = 1 + sum(squares[(x*x*x+a*x+b) % p] for x in range(p))
            if is_prime(n):
                E = Curve(p, a, b)
                return E, n, next(E.points())
    raise ValueError('No test curve found')


def subgroup(p, size, coset=1):
    assert (p-1) % size == 0 and size & (size-1) == 0
    for h in range(2, p):
        g = pow(h, (p-1)//size, p)
        if pow(g, size//2, p) != 1:
            break
    else:
        raise ValueError('No generator')
    xs, x = [], coset
    for _ in range(size):
        xs.append(x)
        x = x*g % p
    assert len(set(xs)) == size and x == coset
    return sorted(xs)


def canonical(points):
    return tuple(sorted(points))


def pair_oracle(E, xs, R):
    """Complete O(s^2) three-sum oracle, distinct abscissae, fixed target."""
    points = {}
    for x in xs:
        P = E.lift(x)
        if P is not None:
            points[x] = [P] if P[1] == 0 else [P, E.neg(P)]
    signed = {P for pair in points.values() for P in pair}
    result = set()
    for x1, x2 in combinations(points, 2):
        for P, Q in product(points[x1], points[x2]):
            T = E.add(R, E.neg(E.add(P, Q)))
            if T in signed and T[0] != x1 and T[0] != x2:
                result.add(canonical([P, Q, T]))
    return result


def q_coefficients(E, R, u, w):
    """Ascending coefficients of the monic cubic in the report."""
    X, Y = R
    p, a = E.p, E.a
    return [(-X**3-2*X*X*u-X*X*w*w+2*X*Y*w-X*u*u+2*Y*u*w-a*w*w) % p,
            (-X*X-X*w*w+2*Y*w+u*u) % p,
            (X+2*u-w*w) % p, 1]


def decode_cubic(E, R, u, w, roots):
    if w % E.p == 0 or len(roots) != 3 or len(set(roots)) != 3:
        return None
    X, Y = R
    v = (w*Y-X*X-u*X) % E.p
    inv = pow(w, -1, E.p)
    Ps = [(x, -(x*x+u*x+v)*inv % E.p) for x in roots]
    if all(E.contains(P) for P in Ps) and E.sum(Ps) == R:
        return canonical(Ps)
    return None


def interpolate_parameters(E, R, points):
    """Recover u,w from a known relation; independent completeness check."""
    p = E.p
    X, Y = R
    for P, Q in combinations(points, 2):
        x, y = P
        xx, yy = Q
        A, B, C = (x-X) % p, (y+Y) % p, (X*X-x*x) % p
        D, F, H = (xx-X) % p, (yy+Y) % p, (X*X-xx*xx) % p
        det = (A*F-B*D) % p
        if det:
            u = (C*F-B*H)*pow(det, -1, p) % p
            w = (A*H-C*D)*pow(det, -1, p) % p
            if decode_cubic(E, R, u, w, [T[0] for T in points]) == canonical(points):
                return u, w
    raise ValueError(('Exceptional relation', R, points))
