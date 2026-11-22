"""Independent integer arithmetic for the X011 p1009 group."""

from hashlib import sha256

P = 1009
N = 1020
G = (2, 155)


def neg(a):
    return None if a is None else (a[0], (-a[1] - 1) % P)


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
        slope = ((3 * x * x - 2 * x - 10) * pow(2 * y + 1, -1, P)) % P
    else:
        slope = ((v - y) * pow(u - x, -1, P)) % P
    intercept = (y - slope * x) % P
    xx = (slope * slope + 1 - x - u) % P
    return (xx, (-slope * xx - intercept - 1) % P)


def mul(k, a=G):
    out = None
    while k:
        if k & 1:
            out = add(out, a)
        a = add(a, a)
        k >>= 1
    return out


def valid(a):
    if a is None:
        return True
    x, y = a
    return (y * y + y - x**3 + x*x + 10*x + 20) % P == 0


def digest_scalar(seed, counter):
    return int.from_bytes(sha256(f"{seed}:{counter}".encode()).digest(), "big") % N
