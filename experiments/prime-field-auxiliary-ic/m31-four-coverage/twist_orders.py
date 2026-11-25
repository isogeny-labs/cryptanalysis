"""Verify the two M31 orders using point witnesses and the Hasse interval."""
from math import gcd, isqrt, prod

P = 2**31 - 1


def prime(n):
    return n >= 2 and all(n % d for d in range(2, isqrt(n) + 1))


def add(a, b):
    if a is None or b is None:
        return b if a is None else a
    x, y = a
    u, v = b
    if x == u:
        if (y + v) % P == 0:
            return None
        slope = (3*x*x + 2) * pow(2*y, -1, P) % P
    else:
        slope = (v-y) * pow(u-x, -1, P) % P
    w = (slope*slope-x-u) % P
    return w, (slope*(x-w)-y) % P


def multiple(point, k):
    total = None
    while k:
        if k & 1:
            total = add(total, point)
        point = add(point, point)
        k >>= 1
    return total


def verify(b, point, factors):
    n = prod(factors)
    x, y = point
    assert (4*2**3 + 27*b*b) % P
    assert (y*y - x**3 - 2*x - b) % P == 0
    assert all(map(prime, factors))
    assert multiple(point, n) is None
    for q in set(factors):
        assert multiple(point, n//q) is not None
    lower, upper = P+1-isqrt(4*P), P+1+isqrt(4*P)
    assert (lower+n-1)//n == upper//n == 1
    return n


if __name__ == "__main__":
    assert prime(P)
    base = verify(14, (1, 1333027745), [2147505293])
    twist = verify(-14, (0, 493947710), [53, 40518151])
    assert base + twist == 2*(P+1)
    print(base, twist, gcd(base, twist))
