#!/usr/bin/env python3
"""Emit a local bit-circuit CNF for an archived s=5 canonical IR.

The first two signed windows are selected by muxes; no pair table is built.
All auxiliary wires have Tseitin equivalence clauses. This is an encoding
construction, not the dynamic CDCL(Fp) clause graph.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

W = 20
TRUE = 19  # Selector variables are exactly 1..18.


def sqrt_canonical(a: int, p: int) -> int:
    if a == 0:
        return 0
    if pow(a, (p - 1) // 2, p) != 1:
        raise ValueError("non-rational window abscissa")
    q, s = p - 1, 0
    while q % 2 == 0:
        q //= 2
        s += 1
    z = 2
    while pow(z, (p - 1) // 2, p) != p - 1:
        z += 1
    m, c = s, pow(z, q, p)
    t, r = pow(a, q, p), pow(a, (q + 1) // 2, p)
    while t != 1:
        i, v = 1, t * t % p
        while v != 1:
            v = v * v % p
            i += 1
        b = pow(c, 1 << (m - i - 1), p)
        r, t, c, m = r * b % p, t * b * b % p, b * b % p, i
    return min(r, p - r)


def parse_ir(data: bytes) -> tuple[int, tuple[int, int], list[list[tuple[int, int]]]]:
    lines = data.decode("ascii").splitlines()
    if not lines or lines[0] != "prime-field-m3-ir/v2":
        raise ValueError("wrong canonical IR version")
    fields = dict(line.split("=", 1) for line in lines[1:])
    if len(fields) != len(lines) - 1 or fields["rung_s"] != "5":
        raise ValueError("duplicate field or wrong rung")
    p, a, b = (int(fields[key]) for key in ("p", "a", "b"))
    if p != 884981 or not (0 <= a < p and 0 <= b < p):
        raise ValueError("this emitter is fixed to the archived p=884981 cohort")
    if (4 * pow(a, 3, p) + 27 * pow(b, 2, p)) % p == 0:
        raise ValueError("singular curve")
    if fields["selector_semantics"] != "compact-binary-radix-index-plus-rational-lift-sign":
        raise ValueError("unexpected selector semantics")
    qx, qy = (int(word) for word in fields["target"].split(","))
    if not (0 <= qx < p and 0 <= qy < p) or qy * qy % p != (qx * qx * qx + a * qx + b) % p:
        raise ValueError("off-curve target")
    windows = []
    seen = set()
    for w in range(3):
        xs = [int(word) for word in fields[f"window{w}"].split(",")]
        if len(xs) != 32 or xs != sorted(set(xs)):
            raise ValueError("window must have 32 distinct sorted abscissae")
        pts = []
        for x in xs:
            if not (0 <= x < p) or x in seen:
                raise ValueError("out-of-field or repeated abscissa")
            seen.add(x)
            y = sqrt_canonical((x * x * x + a * x + b) % p, p)
            if y == 0:
                raise ValueError("one-lift window point")
            pts.extend(((x, y), (x, p - y)))
        windows.append(pts)
    if qx in {x for x, _ in windows[2]}:
        raise ValueError("target and third window must have disjoint abscissae")
    return p, (qx, qy), windows


class Circuit:
    def __init__(self, selector_assignment: int = 0):
        self.next_var = TRUE + 1
        self.clauses: list[list[int]] = [[TRUE]]
        self.values = {TRUE: True}
        for i in range(18):
            self.values[i + 1] = bool((selector_assignment >> i) & 1)

    def val(self, lit: int) -> bool:
        v = self.values[abs(lit)]
        return v if lit > 0 else not v

    def new(self, value: bool) -> int:
        v = self.next_var
        self.next_var += 1
        self.values[v] = value
        return v

    def and_(self, a: int, b: int) -> int:
        if a == -TRUE or b == -TRUE or a == -b:
            return -TRUE
        if a == TRUE or a == b:
            return b
        if b == TRUE:
            return a
        z = self.new(self.val(a) and self.val(b))
        self.clauses.extend(([-a, -b, z], [a, -z], [b, -z]))
        return z

    def or_(self, a: int, b: int) -> int:
        return -self.and_(-a, -b)

    def xor(self, a: int, b: int) -> int:
        if a == -TRUE:
            return b
        if b == -TRUE:
            return a
        if a == TRUE:
            return -b
        if b == TRUE:
            return -a
        if a == b:
            return -TRUE
        if a == -b:
            return TRUE
        z = self.new(self.val(a) != self.val(b))
        self.clauses.extend(([a, b, -z], [-a, -b, -z], [a, -b, z], [-a, b, z]))
        return z

    def mux(self, s: int, a: int, b: int) -> int:
        if a == b:
            return a
        z = self.new(self.val(b) if self.val(s) else self.val(a))
        self.clauses.extend(([s, -a, z], [s, a, -z], [-s, -b, z], [-s, b, -z]))
        return z

    def constant(self, n: int, width: int = W) -> list[int]:
        if not 0 <= n < (1 << width):
            raise ValueError("constant exceeds word width")
        return [TRUE if (n >> i) & 1 else -TRUE for i in range(width)]

    def variable_word(self, n: int, width: int = W) -> list[int]:
        return [self.new(bool((n >> i) & 1)) for i in range(width)]

    def value(self, word: list[int]) -> int:
        return sum(int(self.val(bit)) << i for i, bit in enumerate(word))

    def add_bits(self, a: list[int], b: list[int], width: int) -> list[int]:
        carry = -TRUE
        out = []
        for i in range(width):
            x = a[i] if i < len(a) else -TRUE
            y = b[i] if i < len(b) else -TRUE
            t = self.xor(x, y)
            out.append(self.xor(t, carry))
            carry = self.or_(self.and_(x, y), self.and_(t, carry))
        return out

    def assert_equal(self, a: list[int], b: list[int]) -> None:
        assert len(a) == len(b)
        for x, y in zip(a, b):
            self.clauses.extend(([-x, y], [x, -y]))

    def assert_lt(self, a: list[int], p: int) -> None:
        equal, less = TRUE, -TRUE
        for i in range(W - 1, -1, -1):
            if (p >> i) & 1:
                less = self.or_(less, self.and_(equal, -a[i]))
                equal = self.and_(equal, a[i])
            else:
                equal = self.and_(equal, -a[i])
        self.clauses.append([less])

    def modulus_row(self, carry: int, p: int, width: int) -> list[int]:
        return [carry if (p >> i) & 1 else -TRUE for i in range(width)]

    def mod_add(self, a: list[int], b: list[int], p: int) -> list[int]:
        value = self.value(a) + self.value(b)
        r, c = value % p, value // p
        out, carry = self.variable_word(r), self.new(bool(c))
        lhs = self.add_bits(a, b, W + 1)
        rhs = self.add_bits(out, self.modulus_row(carry, p, W + 1), W + 1)
        self.assert_equal(lhs, rhs)
        self.assert_lt(out, p)
        return out

    def mod_sub(self, a: list[int], b: list[int], p: int) -> list[int]:
        av, bv = self.value(a), self.value(b)
        carry = self.new(av < bv)
        out = self.variable_word((av - bv) % p)
        lhs = self.add_bits(a, self.modulus_row(carry, p, W + 1), W + 1)
        rhs = self.add_bits(b, out, W + 1)
        self.assert_equal(lhs, rhs)
        self.assert_lt(out, p)
        return out

    def product(self, a: list[int], b: list[int]) -> list[int]:
        total = self.constant(0, 41)
        for j, bj in enumerate(b):
            row = [-TRUE] * 41
            for i, ai in enumerate(a):
                row[i + j] = self.and_(ai, bj)
            total = self.add_bits(total, row, 41)
        return total

    def mod_mul(self, a: list[int], b: list[int], p: int) -> list[int]:
        value = self.value(a) * self.value(b)
        out = self.variable_word(value % p)
        quotient = self.variable_word(value // p)
        lhs = self.product(a, b)
        pk = self.constant(0, 41)
        for j in range(W):
            if (p >> j) & 1:
                row = [-TRUE] * j + quotient + [-TRUE] * (41 - j - W)
                pk = self.add_bits(pk, row, 41)
        rhs = self.add_bits(pk, out, 41)
        self.assert_equal(lhs, rhs)
        self.assert_lt(out, p)
        return out

    def select_point(self, table: list[tuple[int, int]], w: int) -> tuple[list[int], list[int]]:
        chosen = []
        for coordinate in range(2):
            row = [self.constant(pt[coordinate]) for pt in table]
            for selector in [6 * w + 6] + [6 * w + i + 1 for i in range(5)]:
                row = [
                    [self.mux(selector, x, y) for x, y in zip(row[i], row[i + 1])]
                    for i in range(0, len(row), 2)
                ]
            chosen.append(row[0])
        return chosen[0], chosen[1]

    def chord(self, u: tuple[list[int], list[int]], v: tuple[list[int], list[int]], p: int):
        x, y = u
        vx, vy = v
        d = self.mod_sub(vx, x, p)
        n = self.mod_sub(vy, y, p)
        d2 = self.mod_mul(d, d, p)
        d3 = self.mod_mul(d2, d, p)
        n2 = self.mod_mul(n, n, p)
        xsum = self.mod_add(x, vx, p)
        a = self.mod_sub(n2, self.mod_mul(xsum, d2, p), p)
        inner = self.mod_sub(self.mod_mul(x, d2, p), a, p)
        b = self.mod_sub(self.mod_mul(n, inner, p), self.mod_mul(y, d3, p), p)
        return a, b, d, d2, d3


def build(data: bytes, selector_assignment: int = 0) -> Circuit:
    p, (qx, qy), windows = parse_ir(data)
    c = Circuit(selector_assignment)
    pts = [c.select_point(table, w) for w, table in enumerate(windows)]
    q = c.constant(qx), c.constant(qy)
    neg_p2 = pts[2][0], c.mod_sub(c.constant(0), pts[2][1], p)
    a, b, d, d2, d3 = c.chord(pts[0], pts[1], p)
    e, f, h, h2, h3 = c.chord(q, neg_p2, p)
    c.assert_equal(c.mod_mul(a, h2, p), c.mod_mul(e, d2, p))
    c.assert_equal(c.mod_mul(b, h3, p), c.mod_mul(f, d3, p))
    return c


def write_dimacs(c: Circuit, data: bytes, path: Path) -> None:
    header = (
        "c m3-compact-two-chord-cnf/v1\n"
        f"c canonical_ir_sha256={hashlib.sha256(data).hexdigest()}\n"
        "c existential gate-equivalence encoding; not dynamic CDCL(Fp)\n"
        f"p cnf {c.next_var - 1} {len(c.clauses)}\n"
    )
    if path.exists():
        raise FileExistsError("refusing to overwrite existing DIMACS")
    with path.open("x", encoding="ascii") as out:
        out.write(header)
        for clause in c.clauses:
            out.write(" ".join(map(str, clause)) + " 0\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: m3_compact_cnf.py INPUT.ir OUTPUT.cnf")
    source = Path(sys.argv[1]).read_bytes()
    circuit = build(source)
    write_dimacs(circuit, source, Path(sys.argv[2]))
    print(f"vars={circuit.next_var - 1} clauses={len(circuit.clauses)}")
