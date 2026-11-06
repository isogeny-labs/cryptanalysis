#!/usr/bin/env python3
"""Expand Semaev's S_3 and report its monomial support.

S_3(x1, x2, xR) = (x1 - x2)^2 xR^2
                - 2[(x1 + x2)(x1 x2 + a) + 2b] xR
                + (x1 x2 - a)^2 - 4b(x1 + x2)

for y^2 = x^3 + a x + b.  Pure stdlib; used by
problems/ecdlp-semaev-encoding-floor.md.

    python3 tools/semaev/s3_support.py [a] [b]
"""
import sys


def mul(p, q):
    r = {}
    for m1, c1 in p.items():
        for m2, c2 in q.items():
            m = tuple(x + y for x, y in zip(m1, m2))
            r[m] = r.get(m, 0) + c1 * c2
    return {m: c for m, c in r.items() if c}


def add(*ps):
    r = {}
    for p in ps:
        for m, c in p.items():
            r[m] = r.get(m, 0) + c
    return {m: c for m, c in r.items() if c}


def sub(p, q):
    return add(p, {m: -c for m, c in q.items()})


def scalar(p, k):
    return {m: c * k for m, c in p.items()}


def var(i):
    return {(0,) * i + (1,) + (0,) * (2 - i): 1}


def const(k):
    return {(0, 0, 0): k}


def s3(a, b):
    x1, x2, xR = var(0), var(1), var(2)
    d = sub(x1, x2)
    t1 = mul(mul(d, d), mul(xR, xR))
    inner = add(mul(add(x1, x2), add(mul(x1, x2), const(a))), const(2 * b))
    t2 = scalar(mul(inner, xR), -2)
    t3 = sub(mul(sub(mul(x1, x2), const(a)), sub(mul(x1, x2), const(a))),
             scalar(add(x1, x2), 4 * b))
    return add(t1, t2, t3)


def main():
    a = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    b = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    S = s3(a, b)
    print("curve: y^2 = x^3 + %d x + %d" % (a, b))
    print("monomials: %d of the %d in the box [0,2]^3" % (len(S), 27))
    print("degree in x1 / x2 / xR: %s" % [max(m[i] for m in S) for i in range(3)])
    print("total degree: %d" % max(sum(m) for m in S))
    for m, c in sorted(S.items(), key=lambda t: (sum(t[0]), t[0])):
        print("  x1^%d x2^%d xR^%d  %+d" % (m[0], m[1], m[2], c))


if __name__ == "__main__":
    main()
