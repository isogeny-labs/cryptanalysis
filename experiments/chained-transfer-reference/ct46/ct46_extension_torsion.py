#!/usr/bin/env python3
"""CT46 independent F_101 extension-field torsion calculations (unsigned)."""
from itertools import product
from math import gcd

P = 101
TRACES = (-7, -11)
I = (1, 0, 0, 1)


def verify(condition, message="CT46 invariant failed"):
    if not condition:
        raise AssertionError(message)


def matrix(t, n):
    return (0, (-P) % n, 1, t % n)


def mul(a, b, n):
    return ((a[0]*b[0]+a[1]*b[2]) % n,
            (a[0]*b[1]+a[1]*b[3]) % n,
            (a[2]*b[0]+a[3]*b[2]) % n,
            (a[2]*b[1]+a[3]*b[3]) % n)


def power(a, k, n):
    out = I
    while k:
        if k & 1:
            out = mul(out, a, n)
        a = mul(a, a, n)
        k //= 2
    return out


def det(a, n):
    return (a[0]*a[3]-a[1]*a[2]) % n


def inverse(a, n):
    d = det(a, n)
    verify(gcd(d, n) == 1)
    v = pow(d, -1, n)
    return (a[3]*v % n, -a[1]*v % n, -a[2]*v % n, a[0]*v % n)


def trace_power(t, k):
    if k == 0:
        return 2
    if k == 1:
        return t
    prev, current = 2, t
    for _ in range(2, k+1):
        prev, current = current, t*current-P*prev
    return current


def v2(z):
    verify(z)
    return (abs(z) & -abs(z)).bit_length()-1


def count_intertwiners(n, k):
    a = power(matrix(TRACES[0], n), k, n)
    b = power(matrix(TRACES[1], n), k, n)
    total = invertible = anti = 0
    for x in product(range(n), repeat=4):
        if mul(x, a, n) != mul(b, x, n):
            continue
        total += 1
        d = det(x, n)
        if d & 1:
            invertible += 1
        if d == n-1:
            anti += 1
    return total, invertible, anti


def cyclic_conjugator(n, k):
    a = power(matrix(TRACES[0], n), k, n)
    b = power(matrix(TRACES[1], n), k, n)
    verify(trace_power(TRACES[0], k) % n == trace_power(TRACES[1], k) % n)
    # The companion vectors (v, F^k v) are cyclic because k is a power of two.
    sa = (1, a[0], 0, a[2])
    sb = (1, b[0], 0, b[2])
    verify(det(sa, n) % 2 == det(sb, n) % 2 == 1)
    x = mul(sb, inverse(sa, n), n)
    verify(mul(x, a, n) == mul(b, x, n))
    # Adjustment by units in the unramified centralizer changes determinant.
    # This is a finite certificate; no geometric pairing orientation is assumed.
    for aa, bb in product(range(n), repeat=2):
        c = tuple((aa*I[j] + bb*b[j]) % n for j in range(4))
        y = mul(c, x, n)
        if det(y, n) == n-1:
            verify(mul(y, a, n) == mul(b, y, n))
            return y
    raise AssertionError('unable to find anti-determinant conjugator')


def main():
    verify(count_intertwiners(8, 1) == (16, 0, 0))
    verify(count_intertwiners(8, 2) == (64, 48, 12))
    verify(count_intertwiners(16, 1) == (16, 0, 0))
    verify(count_intertwiners(16, 2) == (64, 0, 0))
    verify(count_intertwiners(16, 3) == (1024, 0, 0))
    verify(count_intertwiners(16, 4) == (256, 192, 24))
    print('brute 8/16: 8-torsion first isomorphism at k=2; 16-torsion at k=4 [pcc:unverified]')
    for n in (8, 16, 32, 64):
        k = n // 4
        d = trace_power(TRACES[0], k)-trace_power(TRACES[1], k)
        verify(v2(d) == 2 + (k.bit_length()-1))
        verify((trace_power(TRACES[0],k)-trace_power(TRACES[1],k)) % n == 0)
        # One step shorter along the 2-power tower has a differing trace.
        verify((trace_power(TRACES[0],k//2)-trace_power(TRACES[1],k//2)) % n != 0)
        u = cyclic_conjugator(n, k)
        print(f'mod={n} extension={k} anti-det conjugator={u}; det={det(u,n)} [pcc:unverified]')
    # A deliberately wrong base-degree conjecture must fail at level 8.
    verify(count_intertwiners(8, 1)[1] == 0)
    print('CT46 Python PASS: extension-only finite torsion lifts; no curve isogeny claim [pcc:unverified]')

if __name__ == '__main__':
    main()
