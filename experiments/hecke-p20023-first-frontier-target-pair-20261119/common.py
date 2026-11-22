"""Integer group law for X0(11) over F_20023."""

from hashlib import sha256

P = 20023
N = 4021


def add(a, b):
    if a is None:
        return b
    if b is None:
        return a
    x, y = a
    u, v = b
    if x == u and (y + v + 1) % P == 0:
        return None
    if x == u:
        slope = ((3*x*x - 2*x - 10) * pow(2*y + 1, -1, P)) % P
    else:
        slope = ((v - y) * pow(u - x, -1, P)) % P
    intercept = (y - slope*x) % P
    xx = (slope*slope + 1 - x - u) % P
    return xx, (-slope*xx - intercept - 1) % P


def mul(k, point):
    out = None
    while k:
        if k & 1:
            out = add(out, point)
        point = add(point, point)
        k >>= 1
    return out


G = mul(5, (1, 8630))
assert mul(N, G) is None and G is not None


def valid(a):
    if a is None:
        return True
    x, y = a
    return (y*y + y - x**3 + x*x + 10*x + 20) % P == 0


def digest_scalar(seed, counter):
    return int.from_bytes(sha256(f"{seed}:{counter}".encode()).digest(), "big") % N
