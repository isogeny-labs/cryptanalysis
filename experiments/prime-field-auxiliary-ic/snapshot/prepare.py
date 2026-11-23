"""Construct Petit's auxiliary-isogeny factor base; no Sage dependency.

Run: python prepare.py
Then compile/run solve.cpp as described in README.md.
"""
import json
from math import isqrt
from pathlib import Path
from sympy import isprime

ROOT = Path(__file__).resolve().parent


class Curve:
    # y^2 = x^3 + a2*x^2 + a4*x + a6, characteristic > 3
    def __init__(self, p, a2=0, a4=0, a6=0):
        self.p = p
        self.a2, self.a4, self.a6 = (a2 % p, a4 % p, a6 % p)

    def contains(self, P):
        if P is None:
            return True
        x, y = P
        return (y*y - x**3 - self.a2*x*x - self.a4*x - self.a6) % self.p == 0

    def neg(self, P):
        return None if P is None else (P[0], -P[1] % self.p)

    def add(self, P, Q):
        if P is None:
            return Q
        if Q is None:
            return P
        p = self.p
        x, y = P
        u, v = Q
        if x == u:
            if (y + v) % p == 0:
                return None
            slope = (3*x*x + 2*self.a2*x + self.a4) * pow(2*y, -1, p) % p
        else:
            slope = (v-y) * pow(u-x, -1, p) % p
        z = (slope*slope - self.a2 - x - u) % p
        return z, (slope*(x-z)-y) % p

    def mul(self, k, P):
        assert k >= 0
        R = None
        while k:
            if k & 1:
                R = self.add(R, P)
            P = self.add(P, P)
            k >>= 1
        return R

    def double_n(self, point, count):
        """Apply exactly count successive doublings, stopping at infinity."""
        for _ in range(count):
            if point is None:
                break
            point = self.add(point, point)
        return point

    def point(self, start=0):
        for x in range(start, self.p):
            rhs = (x**3 + self.a2*x*x + self.a4*x + self.a6) % self.p
            y = pow(rhs, (self.p+1)//4, self.p)
            if y*y % self.p == rhs:
                return x, min(y, -y % self.p)
        raise RuntimeError('No point found')


def _append_reciprocals(xs, p):
    """Append the field inverses of the original entries in the same order."""
    prefixes = []
    product = 1
    for x in xs:
        prefixes.append(product)
        product = product * x % p
    inverse = pow(product, -1, p)
    for i in range(len(xs)-1, -1, -1):
        prefixes[i], inverse = prefixes[i] * inverse % p, xs[i] * inverse % p
    xs.extend(prefixes)


def _check_sibling_fiber(roots, maps, terminal, p):
    """Check each isogeny image once for a full, coset-ordered fiber."""
    layer = roots
    for step in maps:
        half = len(layer) // 2
        if not half or len(layer) != 2 * half:
            return False
        r, a, b = step['r'], step['A'], step['B']
        parents = []
        for i in range(half):
            u, v = layer[i] - r, layer[half + i] - r
            if not b or u * v % p != b:
                return False
            # uv=B makes both shifted images u+A+B/u and v+A+B/v equal.
            parents.append((u + a + v) % p)
        layer = parents
    return layer == [terminal]


def chain(p, s, enumerate_all=False, root_limit=None):
    k = (p+1).bit_length()-1
    assert isprime(p) and p+1 == 2**k and 1 <= s < k-1
    E = Curve(p, a4=1)
    # For p == 3 (mod 4), the character sum cancels under x -> -x,
    # so #E=p+1. Exactly one nonidentity rational 2-torsion point
    # makes this 2-group cyclic.
    for x in range(1, 100):
        T = E.point(x)
        G = E.double_n(T, k-s)
        half = E.double_n(G, s-1)
        if half is not None:
            break
    else:
        raise RuntimeError('No auxiliary generator found')
    # half = [2^(s-1)]G = [2^(k-1)]T. One final doubling checks both orders.
    assert E.add(half, half) is None
    current, H, image = E, G, T
    maps = []
    for j in range(s):
        K = current.double_n(H, s-j-1)
        assert K is not None and K[1] == 0
        r = K[0]
        A = (3*r + current.a2) % p
        B = (3*r*r + 2*current.a2*r + current.a4) % p
        nxt = Curve(p, a2=-2*A, a4=A*A-4*B)

        def phi(P):
            if P is None or P[0] == r:
                return None
            u = (P[0]-r) % p
            inv = pow(u, -1, p)
            return ((u+A+B*inv) % p, P[1]*(1-B*inv*inv) % p)

        newH, newT = phi(H), phi(image)
        assert nxt.contains(newH) and nxt.contains(newT)
        # Check homomorphism on concrete points, independently of formulas.
        assert phi(current.add(image, H)) == nxt.add(newT, newH)
        maps.append(dict(r=r, A=A, B=B))
        current, H, image = nxt, newH, newT
    assert H is None and image is not None and image[1] != 0
    c = image[0]

    def eval_chain(x):
        for step in maps:
            u = (x-step['r']) % p
            if u == 0:
                return None  # pole; never accepted as a root
            x = (u+step['A']+step['B']*pow(u, -1, p)) % p
        return (x-c) % p

    # All x(T+iG) are distinct: 2T is not in G. They are the roots of
    # a degree-2^s rational-map numerator, hence exhaust all roots.
    V, R = [], T
    checked_count=2**s if k==31 or enumerate_all else min(128,2**s)
    if root_limit is not None:
        if root_limit<0:raise ValueError('root_limit must be nonnegative')
        checked_count=min(2**s,root_limit)
    paired = p == 2**31-1 and checked_count == 2**s
    half_walk = paired and s >= 3
    walk_count = checked_count // 2 if half_walk else checked_count
    for i in range(walk_count):
        assert R is not None
        if not paired:
            assert eval_chain(R[0]) == 0
        V.append(R[0])
        R = E.add(R, G)
    if half_walk:
        # On y²=x³+x, translating by (0,0) sends x to its reciprocal.
        # The midpoint is T + half; the second half ends at T.
        assert half == (0, 0) and E.add(R, half) == T
        _append_reciprocals(V, p)
    if paired:
        assert _check_sibling_fiber(V, maps, c, p)
    assert len(set(V)) == len(V)
    if not half_walk and checked_count == 2**s:
        assert R == T
    info = dict(p=p, auxiliary_order=p+1, auxiliary_generator=T,
                kernel_generator=G, kernel_order=2**s, maps=maps,
                terminal_c=c, root_count=2**s, roots_checked=len(V))
    return info, V


def order_in_hasse_interval(E, P):
    # Baby-step/giant-step for [N]P=0 within the Hasse interval.
    # This is used ONLY to certify the target's public order, not for its DLP.
    p = E.p
    radius = isqrt(4*p)
    low, high = p+1-radius, p+1+radius
    width = high-low
    m = isqrt(width)+1
    babies, R = {}, None
    for j in range(m):
        babies[R] = j
        R = E.add(R, P)
    R = E.neg(E.mul(low, P))
    step = E.neg(E.mul(m, P))
    for i in range(m+1):
        if R in babies:
            n = low+i*m+babies[R]
            if low <= n <= high and E.mul(n, P) is None:
                return n
        R = E.add(R, step)
    return None


def main():
    aux, V = chain(2**31-1, 10)
    (ROOT/'auxiliary_31.json').write_text(json.dumps(aux, indent=2)+'\n')
    aux61, _ = chain(2**61-1, 20)
    (ROOT/'auxiliary_61.json').write_text(json.dumps(aux61, indent=2)+'\n')
    p = aux['p']
    for b in range(1, 500):
        if (4*2**3+27*b*b) % p == 0:
            continue
        E = Curve(p, a4=2, a6=b)
        P = E.point(1)
        n = order_in_hasse_interval(E, P)
        if n and isprime(n):
            # Nonzero P with prime order n in Hasse's interval proves #E=n:
            # there is no second multiple of n within that interval.
            break
    else:
        raise RuntimeError('No prime-order target found')
    secret = 123456789
    Q = E.mul(secret, P)
    F = []  # One representative per +/- pair; signs stored in relations.
    for x in V:
        rhs = (x**3+2*x+b) % p
        y = pow(rhs, (p+1)//4, p)
        if y*y % p == rhs:
            assert y != 0  # Target order is odd prime.
            F.append((x, min(y, p-y)))
    public = dict(p=p, a=2, b=b, n=n, P=P, Q=Q,
                  factor_base_x_size=len(V), signed_factor_base_size=2*len(F),
                  factor_base_representatives=F)
    (ROOT/'public.json').write_text(json.dumps(public, indent=2)+'\n')
    # Solver input deliberately excludes the secret.
    with (ROOT/'public.txt').open('w') as out:
        out.write(f'{p} {n} 2 {b}\n{P[0]} {P[1]} {Q[0]} {Q[1]}\n{len(F)}\n')
        out.writelines(f'{x} {y}\n' for x,y in F)
    (ROOT/'expected.json').write_text(json.dumps(dict(secret=secret))+'\n')
    print(json.dumps({k:v for k,v in public.items() if k != 'factor_base_representatives'},indent=2))
    print('Auxiliary 31-bit: order 2^31; 10 degree-2 maps; all 1024 roots checked.')
    print('Auxiliary 61-bit: order 2^61; 20 degree-2 maps; 128 roots sampled.')
    print('Factor-base representatives:', len(F))


if __name__ == '__main__':
    main()
