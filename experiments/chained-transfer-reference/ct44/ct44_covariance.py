#!/usr/bin/env python3
"""Independent CT44 finite-ring transport checker; no producer imports."""
from itertools import product

M = 4
F = ((0, 3), (1, 1))
I = ((1, 0), (0, 1))
Z = ((0, 0), (0, 0))


def matmul(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(2)) % M
                       for j in range(2)) for i in range(2))


def det(a):
    return (a[0][0] * a[1][1] - a[0][1] * a[1][0]) % M


def inv(a):
    d = det(a)
    assert d in (1, 3)
    return ((a[1][1] * d % M, -a[0][1] * d % M),
            (-a[1][0] * d % M, a[0][0] * d % M))


def adj(a):
    return ((a[1][1] % M, -a[0][1] % M),
            (-a[1][0] % M, a[0][0] % M))


def vec(a, v):
    return tuple(sum(a[i][j] * v[j] for j in range(2)) % M for i in range(2))


def wedge(v, w):
    return (v[0] * w[1] - v[1] * w[0]) % M


def pair(v, w):
    return pow(10, wedge(v, w), 101)


points = list(product(range(4), repeat=2))
matrices = [((a, b), (c, d)) for a, b, c, d in product(range(4), repeat=4)]
centralizer = [a for a in matrices if matmul(a, F) == matmul(F, a)]
anti = [a for a in centralizer if det(a) == 3]
symp = [a for a in centralizer if det(a) == 1]
assert len(centralizer) == 16 and len(anti) == len(symp) == 6
assert matmul(F, matmul(F, F)) == ((3, 0), (0, 3))
assert matmul(F, F) != I
powers = [I]
for _ in range(5):
    powers.append(matmul(powers[-1], F))
U0 = ((1, 2), (2, 3))
assert set(anti) == {matmul(U0, p) for p in powers}
assert set(symp) == set(powers)

for a in anti:
    dual = adj(a)
    assert dual in anti
    assert matmul(dual, a) == matmul(a, dual) == ((3, 0), (0, 3))
    for p, q in product(points, repeat=2):
        assert pair(vec(a, p), vec(a, q)) == pow(pair(p, q), 7, 101)

transported = set()
for a, b, u in product(anti, repeat=3):
    v = matmul(matmul(b, u), inv(a))
    assert v in anti and det(v) == 3
    transported.add(v)
    for p, q in product(points, repeat=2):
        ap, aq = vec(a, p), vec(a, q)
        bp, bq = vec(b, vec(u, p)), vec(b, vec(u, q))
        assert bp == vec(v, ap) and bq == vec(v, aq)
        assert pair(ap, aq) * pair(bp, bq) % 101 == 1
        assert matmul(a, F) == matmul(F, a)
        assert matmul(b, F) == matmul(F, b)
assert len(transported) == 6

wrong = 0
for a, b, u in product(anti, symp, anti):
    v = matmul(matmul(b, u), inv(a))
    assert v in symp and det(v) == 1
    x, y = (1, 0), (0, 1)
    assert pair(x, y) * pair(vec(v, x), vec(v, y)) % 101 == 100
    assert (wedge(x, y) + wedge(vec(v, x), vec(v, y))) % 2 == 0
    wrong += 1
assert wrong == 216

paths = 0
for a1, a2, b1, b2, u in product(anti, repeat=5):
    ac, bc = matmul(a2, a1), matmul(b2, b1)
    assert ac in symp and bc in symp
    once = matmul(matmul(b1, u), inv(a1))
    twice = matmul(matmul(b2, once), inv(a2))
    assert twice == matmul(matmul(bc, u), inv(ac))
    assert twice in anti and det(twice) == 3
    assert matmul(adj(ac), ac) == I  # degree 49 = 1 (mod 4)
    paths += 1
assert paths == 7776
print('PASS CT44 [pcc:unverified]: 16 Frobenius centralizers; 6 degree-7/anti maps; 6 degree-49/symplectic maps')
print('PASS CT44: 216 one-hop graph transports x 256 Weil pair tests; 7776 two-hop matrix transports')
print('PASS CT44: 6 dual adjugates; 216 mismatched-degree counterexamples invisible mod 2')
print('BOUNDARY: abstract E[4] companion modules only; no native quartic pullback, A[4] or cost claim')
