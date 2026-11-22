#!/usr/bin/env python3
"""Small finite-field primitives with no O(p) tables or scans."""

from __future__ import annotations

import hashlib


Point = tuple[int, int] | None


class HashStream:
    """Version-independent deterministic hash stream with unbiased randbelow."""

    def __init__(self, seed: str):
        self.seed = seed.encode()
        self.counter = 0

    def block(self) -> bytes:
        block = hashlib.sha256(
            self.seed + b"|" + self.counter.to_bytes(16, "big")
        ).digest()
        self.counter += 1
        return block

    def randbelow(self, limit: int) -> int:
        if limit <= 0:
            raise ValueError("randbelow limit must be positive")
        width = (limit.bit_length() + 7) // 8
        ceiling = 1 << (8 * width)
        cutoff = ceiling - ceiling % limit
        while True:
            material = bytearray()
            while len(material) < width:
                material.extend(self.block())
            value = int.from_bytes(material[:width], "big")
            if value < cutoff:
                return value % limit

    def shuffle(self, values: list[int]) -> None:
        for index in range(len(values) - 1, 0, -1):
            partner = self.randbelow(index + 1)
            values[index], values[partner] = values[partner], values[index]


def legendre(value: int, prime: int) -> int:
    value %= prime
    if value == 0:
        return 0
    symbol = pow(value, (prime - 1) // 2, prime)
    return -1 if symbol == prime - 1 else symbol


def tonelli_shanks(value: int, prime: int) -> int | None:
    """Return a deterministic square root modulo an odd prime, or None."""
    value %= prime
    if value == 0:
        return 0
    if prime == 2:
        return value
    if legendre(value, prime) != 1:
        return None
    if prime % 4 == 3:
        return pow(value, (prime + 1) // 4, prime)
    odd = prime - 1
    shifts = 0
    while odd % 2 == 0:
        shifts += 1
        odd //= 2
    nonresidue = 2
    while legendre(nonresidue, prime) != -1:
        nonresidue += 1
    c = pow(nonresidue, odd, prime)
    root = pow(value, (odd + 1) // 2, prime)
    residue = pow(value, odd, prime)
    exponent = shifts
    while residue != 1:
        index = 1
        square = residue * residue % prime
        while square != 1:
            square = square * square % prime
            index += 1
            if index >= exponent:
                raise ArithmeticError("Tonelli--Shanks invariant failed")
        factor = pow(c, 1 << (exponent - index - 1), prime)
        root = root * factor % prime
        residue = residue * factor * factor % prime
        c = factor * factor % prime
        exponent = index
    return min(root, prime - root)


def discriminant(a: int, b: int, prime: int) -> int:
    return (-16 * (4 * pow(a, 3, prime) + 27 * pow(b, 2, prime))) % prime


def on_curve(point: Point, a: int, b: int, prime: int) -> bool:
    if point is None:
        return True
    x, y = point
    return (y * y - (x * x * x + a * x + b)) % prime == 0


def point_neg(point: Point, prime: int) -> Point:
    return None if point is None else (point[0], (-point[1]) % prime)


def point_add(left: Point, right: Point, a: int, prime: int) -> Point:
    if left is None:
        return right
    if right is None:
        return left
    x1, y1 = left
    x2, y2 = right
    if x1 == x2 and (y1 + y2) % prime == 0:
        return None
    if left == right:
        slope = (3 * x1 * x1 + a) * pow(2 * y1, -1, prime) % prime
    else:
        slope = (y2 - y1) * pow((x2 - x1) % prime, -1, prime) % prime
    x3 = (slope * slope - x1 - x2) % prime
    y3 = (slope * (x1 - x3) - y1) % prime
    return x3, y3


def point_mul(scalar: int, point: Point, a: int, prime: int) -> Point:
    if scalar < 0:
        return point_mul(-scalar, point_neg(point, prime), a, prime)
    result = None
    addend = point
    while scalar:
        if scalar & 1:
            result = point_add(result, addend, a, prime)
        addend = point_add(addend, addend, a, prime)
        scalar >>= 1
    return result


def generate_curve(stream: HashStream, prime: int, family: str):
    for attempt in range(1, 257):
        a = 0 if family == "j0" else stream.randbelow(prime)
        b = stream.randbelow(prime)
        if family not in {"generic", "j0"}:
            raise ValueError(f"unknown curve family {family}")
        if discriminant(a, b, prime):
            return a, b, attempt
    raise RuntimeError("curve generation exhausted its fixed attempt cap")


def sample_point(stream: HashStream, prime: int, a: int, b: int):
    for attempt in range(1, 4097):
        x = stream.randbelow(prime)
        rhs = (x * x * x + a * x + b) % prime
        root = tonelli_shanks(rhs, prime)
        if root is None:
            continue
        y = root if stream.randbelow(2) == 0 else (-root) % prime
        point = (x, y)
        if not on_curve(point, a, b, prime):
            raise ArithmeticError("sampled point failed its curve equation")
        return point, attempt
    raise RuntimeError("point sampling exhausted its fixed attempt cap")
