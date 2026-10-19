#!/usr/bin/env python3
"""Derive the fixed public KAT workloads for volcano-jobs-native-v1.

This is setup code only. It does no timing and invokes no benchmark binary.
The point-counting case is deliberately tiny; the 33-bit subgroup case uses
the exact order p+1, proved by the x^3 permutation for p == 2 (mod 3).
"""

from __future__ import annotations

import json
import hashlib

MASK = (1 << 64) - 1


def splitmix64(state: list[int]) -> int:
    state[0] = (state[0] + 0x9E3779B97F4A7C15) & MASK
    z = state[0]
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
    return z ^ (z >> 31)


class Rng:
    def __init__(self, seed: int):
        state = [seed & MASK]
        self.s = [splitmix64(state) for _ in range(4)]
        if not any(self.s):
            self.s[0] = 1

    def next(self) -> int:
        s = self.s
        result = (((s[1] * 5) & MASK) << 7 | ((s[1] * 5) & MASK) >> (64 - 7)) & MASK
        result = (result * 9) & MASK
        t = (s[1] << 17) & MASK
        s[2] ^= s[0]
        s[3] ^= s[1]
        s[1] ^= s[2]
        s[0] ^= s[3]
        s[2] ^= t
        s[3] = ((s[3] << 45) | (s[3] >> 19)) & MASK
        return result

    def below(self, n: int) -> int:
        if n == 0:
            return self.next()
        m = self.next() * n
        low = m & MASK
        if low < n:
            threshold = (1 << 64) % n
            while low < threshold:
                m = self.next() * n
                low = m & MASK
        return m >> 64


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    small = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for p in small:
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        s += 1
        d //= 2
    # Deterministic for all unsigned 64-bit integers.
    for a in (2, 325, 9375, 28178, 450775, 9780504, 1795265022):
        if a % n == 0:
            continue
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def sqrt_mod(n: int, p: int) -> int | None:
    n %= p
    if n == 0:
        return 0
    if pow(n, (p - 1) // 2, p) != 1:
        return None
    q, s = p - 1, 0
    while q % 2 == 0:
        s += 1
        q //= 2
    if s == 1:
        y = pow(n, (p + 1) // 4, p)
    else:
        z = 2
        while pow(z, (p - 1) // 2, p) != p - 1:
            z += 1
        c, y, t, m = pow(z, q, p), pow(n, (q + 1) // 2, p), pow(n, q, p), s
        while t != 1:
            i, u = 1, t * t % p
            while i < m and u != 1:
                u = u * u % p
                i += 1
            if i == m:
                return None
            b = pow(c, 1 << (m - i - 1), p)
            y, t, c, m = y * b % p, t * b * b % p, b * b % p, i
    return min(y, p - y)


def add(P: tuple[int, int] | None, Q: tuple[int, int] | None,
        p: int, a: int) -> tuple[int, int] | None:
    if P is None:
        return Q
    if Q is None:
        return P
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2 and (y1 + y2) % p == 0:
        return None
    if P == Q:
        slope = (3 * x1 * x1 + a) * pow(2 * y1, -1, p) % p
    else:
        slope = (y2 - y1) * pow((x2 - x1) % p, -1, p) % p
    x3 = (slope * slope - x1 - x2) % p
    return x3, (slope * (x1 - x3) - y1) % p


def mul(k: int, P: tuple[int, int] | None, p: int, a: int) -> tuple[int, int] | None:
    result = None
    while k:
        if k & 1:
            result = add(result, P, p, a)
        P = add(P, P, p, a)
        k >>= 1
    return result


def random_point(p: int, a: int, b: int, seed: int) -> tuple[int, int]:
    rng = Rng(seed)
    while True:
        x = rng.below(p)
        y = sqrt_mod(x * x % p * x + a * x + b, p)
        if y is None:
            continue
        if rng.next() & 1:
            y = (-y) % p
        return x, y


def count_points(p: int, a: int, b: int) -> int:
    total = p + 1
    for x in range(p):
        rhs = (x * x % p * x + a * x + b) % p
        if rhs:
            total += 1 if pow(rhs, (p - 1) // 2, p) == 1 else -1
    return total


def factor(n: int) -> list[tuple[int, int]]:
    out = []
    d = 2
    while d * d <= n:
        if n % d == 0:
            e = 0
            while n % d == 0:
                n //= d
                e += 1
            out.append((d, e))
        d = 3 if d == 2 else d + 2
    if n > 1:
        out.append((n, 1))
    return out


def kat(name: str, p: int, a: int, b: int, order: int, ell: int,
        seed: int) -> dict:
    factors = factor(order)
    n = factors[-1][0]
    if not is_prime(n):
        raise ValueError(f"largest factor is not prime: {n}")
    cofactor = order // n
    rng = Rng(seed)
    while True:
        R = random_point(p, a, b, rng.next() | 1)
        P = mul(cofactor, R, p, a)
        if P is not None:
            break
    k = 1 + rng.below(n - 1)
    Q = mul(k, P, p, a)
    assert Q is not None and mul(n, P, p, a) is None
    return {
        "id": name, "p": p, "a": a, "b": b, "curve_order": order,
        "subgroup_order": n, "subgroup_order_bits": n.bit_length(),
        "cofactor": cofactor, "ell": ell, "seed": seed,
        "known_scalar": k, "generator": [P[0], P[1]],
        "target": [Q[0], Q[1]], "factorization": [list(x) for x in factors],
    }


def add_workload_id(case: dict) -> None:
    canonical = json.dumps(case, sort_keys=True, separators=(",", ":")).encode()
    case["workload_id"] = hashlib.sha256(canonical).hexdigest()[:12]


def main() -> None:
    # Deterministic 33-bit prime n and p=6n-1. For p == 2 mod 3,
    # x -> x^3 permutes F_p, so y^2=x^3+1 has exactly p+1=6n points.
    n = 4_418_424_173
    p = 6 * n - 1
    assert n.bit_length() == 33 and is_prime(n) and is_prime(p) and p % 3 == 2
    primary = kat("hist-shape-33bit-36solves", p, 0, 1, p + 1, 2, 20261019)

    small_p, small_a, small_b = 1_000_033, 5, 17
    assert is_prime(small_p)
    small_order = count_points(small_p, small_a, small_b)
    assert small_order == 998_368
    # This case is a public regression fixture with the existing 9/14
    # depth-one volcano profile and six measured arms (root + 2 per level + 1 control).
    multi = kat("multiarm-six-arms-36solves", small_p, small_a, small_b,
                small_order, 3, 20261020)
    assert primary["subgroup_order_bits"] == 33
    assert multi["curve_order"] == 998_368
    for case in (primary, multi):
        add_workload_id(case)
    print(json.dumps({"schema": 1, "protocol": "volcano-jobs-native-v1",
                      "cases": [primary, multi]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
