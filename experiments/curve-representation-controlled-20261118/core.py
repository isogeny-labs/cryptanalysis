"""Prime-field arithmetic and exact finite-fixture helpers; no measurement on import."""
from dataclasses import dataclass
from math import isqrt
from itertools import product, combinations_with_replacement
import hashlib
import json


def prime(n):
    return n >= 2 and all(n % q for q in range(2, isqrt(n) + 1))


@dataclass(frozen=True)
class Curve:
    p: int
    a2: int
    a4: int
    a6: int = 0

    def rhs(self, x):
        return (x**3 + self.a2*x*x + self.a4*x + self.a6) % self.p

    def contains(self, P):
        return P is None or P[1]**2 % self.p == self.rhs(P[0])

    def neg(self, P):
        return None if P is None else (P[0], -P[1] % self.p)

    def add(self, P, Q):
        if P is None:
            return Q
        if Q is None:
            return P
        x, y = P
        u, v = Q
        p = self.p
        if x == u and (y + v) % p == 0:
            return None
        slope = ((3*x*x + 2*self.a2*x + self.a4) * pow(2*y, -1, p)
                 if P == Q else (v-y)*pow(u-x, -1, p)) % p
        z = (slope*slope - self.a2-x-u) % p
        return z, (slope*(x-z)-y) % p

    def mul(self, n, P):
        if n < 0:
            return self.mul(-n, self.neg(P))
        R = None
        while n:
            if n & 1:
                R = self.add(R, P)
            P = self.add(P, P)
            n //= 2
        return R

    def points(self):
        roots = {}
        for y in range(self.p):
            roots.setdefault(y*y % self.p, []).append(y)
        return [None] + [(x, y) for x in range(self.p)
                         for y in roots.get(self.rhs(x), [])]

    def data(self, r, G):
        return {'p': self.p, 'a2': self.a2 % self.p,
                'a4': self.a4 % self.p, 'a6': self.a6 % self.p,
                'r': r, 'G': list(G)}


def curve(data):
    return Curve(*(data[k] for k in ['p', 'a2', 'a4', 'a6']))


def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def signed(C, base):
    return [(P, i, s) for i, B in enumerate(base)
            for P, s in [(B, 1), (C.neg(B), -1)]]


def oracle(C, base):
    """Exact validation oracle, never a decomposition backend for timed arms."""
    rows = {}
    for entries in combinations_with_replacement(signed(C, base), 3):
        R = None
        coeff = [0] * len(base)
        for P, i, s in entries:
            R = C.add(R, P)
            coeff[i] += s
        if any(coeff):
            rows.setdefault(R, set()).add(tuple(coeff))
    return rows


def point_lift(C, base, indices, R):
    """Returns exact coefficient rows; all 2^3 sign assignments are checked."""
    answer = set()
    for signs in product([-1, 1], repeat=3):
        total = None
        coeff = [0] * len(base)
        for i, s in zip(indices, signs):
            total = C.add(total, C.mul(s, base[i]))
            coeff[i] += s
        if total == R and any(coeff):
            answer.add(tuple(coeff))
    return answer


def add_row(pivots, row, r, width):
    row = [x % r for x in row]
    for col in sorted(pivots):
        value = row[col]
        if value:
            row = [(a-value*b) % r for a, b in zip(row, pivots[col])]
    pivot = next((i for i in range(width) if row[i]), None)
    if pivot is None:
        if row[-1]:
            raise ValueError('inconsistent relation')
        return False
    inv = pow(row[pivot], -1, r)
    row = [x*inv % r for x in row]
    for col in list(pivots):
        value = pivots[col][pivot]
        if value:
            pivots[col] = [(a-value*b) % r
                           for a, b in zip(pivots[col], row)]
    pivots[pivot] = row
    return True


def rho(C, r, G, Q, seed=8128):
    """Bounded same-point reference. No precomputation shared across targets."""
    import random
    rng = random.Random(seed)
    steps = 0

    def advance(state):
        nonlocal steps
        P, a, b = state
        bucket = 0 if P is None else P[0] % 3
        steps += 1
        if bucket == 0:
            return C.add(P, G), (a+1) % r, b
        if bucket == 1:
            return C.add(P, P), 2*a % r, 2*b % r
        return C.add(P, Q), a, (b+1) % r

    for restart in range(32):
        a, b = rng.randrange(r), rng.randrange(r)
        left = right = (C.add(C.mul(a, G), C.mul(b, Q)), a, b)
        for _ in range(8*isqrt(r)+32):
            left = advance(left)
            right = advance(advance(right))
            if left[0] == right[0]:
                denominator = (right[2]-left[2]) % r
                if denominator:
                    k = (left[1]-right[1])*pow(denominator, -1, r) % r
                    if C.mul(k, G) != Q:
                        raise ValueError('rho scalar equation failed')
                    return {'status': 'self_checked_recovered', 'scalar': k,
                            'walk_addition_calls': steps, 'restarts': restart,
                            'scope': 'walk count excludes initialization scalar multiplications; not calibrated total GAE'}
                break
    return {'status': 'not_recovered_within_reference_limit',
            'walk_addition_calls': steps, 'restarts': 32}
