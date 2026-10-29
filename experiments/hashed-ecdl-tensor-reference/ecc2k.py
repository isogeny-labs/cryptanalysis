#!/usr/bin/env python3
"""Binary-curve arithmetic and bounded hashed-index-calculus experiments.

Relation backends include meet-in-the-middle and Boolean tensor contraction.
The scalar recursive contraction engine and coordinate encoder are implemented
in tensor_*.py. The paper's default parameters give no practical speedup here.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import time
from typing import Iterator

from sympy import isprime, nextprime


Point = tuple[int, int] | None
ROOT = Path(__file__).resolve().parent
SQUARE_BYTE = tuple(sum(((v >> j) & 1) << (2 * j) for j in range(8)) for v in range(256))


class BudgetExceeded(RuntimeError):
    pass


def number(value: int | str) -> int:
    return int(value, 0) if isinstance(value, str) else value


def carryless(a: int, b: int) -> int:
    result = 0
    while b:
        low = b & -b
        result ^= a << (low.bit_length() - 1)
        b ^= low
    return result


def polynomial_remainder(a: int, b: int) -> int:
    while a and a.bit_length() >= b.bit_length():
        a ^= b << (a.bit_length() - b.bit_length())
    return a


def polynomial_gcd(a: int, b: int) -> int:
    while b:
        a, b = b, polynomial_remainder(a, b)
    return a


@dataclass(frozen=True)
class BinaryField:
    degree: int
    polynomial: int

    def __post_init__(self) -> None:
        if self.degree < 2 or self.polynomial.bit_length() != self.degree + 1 or not self.polynomial & 1:
            raise ValueError("invalid field polynomial")

    @property
    def size(self) -> int:
        return 1 << self.degree

    def reduce(self, value: int) -> int:
        low_poly = self.polynomial ^ self.size
        mask = self.size - 1
        while value >> self.degree:
            value = (value & mask) ^ carryless(value >> self.degree, low_poly)
        return value

    def mul(self, a: int, b: int) -> int:
        return self.reduce(carryless(a, b))

    def square(self, a: int) -> int:
        expanded, shift = 0, 0
        while a:
            expanded |= SQUARE_BYTE[a & 255] << shift
            a >>= 8
            shift += 16
        return self.reduce(expanded)

    def inv(self, a: int) -> int:
        if not a:
            raise ZeroDivisionError("inverse of zero")
        u, v, left, right = a, self.polynomial, 1, 0
        while u != 1:
            if not u:
                raise ValueError("noninvertible element: polynomial is reducible")
            shift = u.bit_length() - v.bit_length()
            if shift < 0:
                u, v, left, right = v, u, right, left
                shift = -shift
            u ^= v << shift
            left ^= right << shift
        return self.reduce(left)

    def div(self, a: int, b: int) -> int:
        return self.mul(a, self.inv(b))

    def sqrt(self, a: int) -> int:
        for _ in range(self.degree - 1):
            a = self.square(a)
        return a

    def quadratic(self, value: int) -> int | None:
        """Solve z^2 + z = value by half trace, for odd extension degree."""
        if self.degree % 2 == 0:
            raise ValueError("half trace requires odd extension degree")
        z = value
        for _ in range((self.degree - 1) // 2):
            z = self.square(self.square(z)) ^ value
        return z if self.square(z) ^ z == value else None

    def irreducible(self) -> bool:
        x, power = 2, 2
        # Rabin's test; checking every i <= degree/2 also avoids factoring degree.
        for i in range(1, self.degree + 1):
            power = self.square(power)
            if i <= self.degree // 2 and polynomial_gcd(power ^ x, self.polynomial) != 1:
                return False
        return power == x


@dataclass(frozen=True)
class BinaryCurve:
    field: BinaryField
    a: int = 0
    b: int = 1

    def __post_init__(self) -> None:
        if not (0 <= self.a < self.field.size and 0 < self.b < self.field.size):
            raise ValueError("curve coefficients must be canonical, with b nonzero")

    def valid(self, point: Point) -> bool:
        if point is None:
            return True
        x, y = point
        if not (0 <= x < self.field.size and 0 <= y < self.field.size):
            return False
        f = self.field
        x2 = f.square(x)
        return f.square(y) ^ f.mul(x, y) == f.mul(x2, x) ^ f.mul(self.a, x2) ^ self.b

    @staticmethod
    def neg(point: Point) -> Point:
        return None if point is None else (point[0], point[0] ^ point[1])

    def add(self, left: Point, right: Point) -> Point:
        if left is None:
            return right
        if right is None:
            return left
        f = self.field
        x1, y1 = left
        x2, y2 = right
        if x1 == x2:
            if y1 != y2 or x1 == 0:
                return None
            slope = x1 ^ f.div(y1, x1)
            x3 = f.square(slope) ^ slope ^ self.a
            return x3, f.square(x1) ^ f.mul(slope ^ 1, x3)
        slope = f.div(y1 ^ y2, x1 ^ x2)
        x3 = f.square(slope) ^ slope ^ x1 ^ x2 ^ self.a
        return x3, f.mul(slope, x1 ^ x3) ^ x3 ^ y1

    def mul(self, scalar: int, point: Point) -> Point:
        if scalar < 0:
            return self.mul(-scalar, self.neg(point))
        result = None
        while scalar:
            if scalar & 1:
                result = self.add(result, point)
            scalar >>= 1
            if scalar:
                point = self.add(point, point)
        return result

    def total(self, points: Iterator[Point]) -> Point:
        result = None
        for point in points:
            result = self.add(result, point)
        return result

    def encode(self, point: Point) -> int:
        """Binary SEC1-style selector: low bit of y/x, NOT low bit of y."""
        if point is None:
            raise ValueError("infinity has no factor-base encoding")
        x, y = point
        return (x << 1) | ((self.field.div(y, x) & 1) if x else 0)

    def decode(self, encoded: int) -> Point:
        if not 0 <= encoded < (self.field.size << 1):
            return None
        x, bit = encoded >> 1, encoded & 1
        f = self.field
        if not x:
            return None if bit else (0, f.sqrt(self.b))
        t = x ^ self.a ^ f.div(self.b, f.square(x))
        z = f.quadratic(t)
        if z is None:
            return None
        if z & 1 != bit:
            z ^= 1
        return x, f.mul(x, z)

    def frobenius(self, point: Point) -> Point:
        if self.a not in (0, 1) or self.b not in (0, 1):
            raise ValueError("Frobenius is only an endomorphism here for curves defined over F2")
        return None if point is None else tuple(map(self.field.square, point))


def koblitz_order(degree: int, a: int = 0) -> int:
    prev, current = 2, (-1 if a == 0 else 1)
    if degree == 1:
        return 3 - current
    mu = current
    for _ in range(2, degree + 1):
        prev, current = current, mu * current - 2 * prev
    return (1 << degree) + 1 - current


@dataclass(frozen=True)
class Instance:
    name: str
    curve: BinaryCurve
    order: int
    cofactor: int
    P: Point
    Q: Point

    def as_dict(self) -> dict:
        return {"name": self.name, "degree": self.curve.field.degree,
                "polynomial": hex(self.curve.field.polynomial), "a": hex(self.curve.a),
                "b": hex(self.curve.b), "order": str(self.order), "cofactor": self.cofactor,
                "P": point_json(self.P), "Q": point_json(self.Q)}

    @classmethod
    def from_dict(cls, d: dict) -> Instance:
        field = BinaryField(d["degree"], number(d["polynomial"]))
        return cls(d["name"], BinaryCurve(field, number(d["a"]), number(d["b"])),
                   number(d["order"]), d["cofactor"], parse_point(d["P"]), parse_point(d["Q"]))

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(json.dumps(self.as_dict(), sort_keys=True).encode()).hexdigest()


def point_json(point: Point) -> list[str] | None:
    return None if point is None else [hex(point[0]), hex(point[1])]


def parse_point(value: list | None) -> Point:
    return None if value is None else (number(value[0]), number(value[1]))


def challenge() -> Instance:
    d = json.loads((ROOT / "challenge.json").read_text())
    field = BinaryField(d["field_degree"], sum(1 << e for e in d["field_polynomial_exponents"]))
    return Instance(d["name"], BinaryCurve(field, number(d["a"]), number(d["b"])),
                    number(d["order"]), d["cofactor"], parse_point(d["P"]), parse_point(d["Q"]))


def toy(degree: int = 19, secret: int = 114415) -> Instance:
    params = {7: (0x83, 29, 4), 13: (0x201B, 2003, 4), 19: (0x80027, 130873, 4)}
    if degree not in params:
        raise ValueError("supported demo degrees: 7, 13, 19")
    polynomial, order, cofactor = params[degree]
    curve = BinaryCurve(BinaryField(degree, polynomial))
    for x in range(1, curve.field.size):
        point = curve.decode(x << 1)
        if point is not None:
            point = curve.mul(cofactor, point)
            if point is not None:
                return Instance(f"DEMO-GF2^{degree}", curve, order, cofactor,
                                point, curve.mul(secret % order, point))
    raise RuntimeError("no generator found")


def validate(instance: Instance) -> dict:
    c, n = instance.curve, instance.order
    checks = {"field_polynomial_irreducible": c.field.irreducible(),
              "subgroup_order_prime": bool(isprime(n)),
              "P_nonidentity": instance.P is not None,
              "P_on_curve": c.valid(instance.P), "Q_on_curve": c.valid(instance.Q)}
    if not all(checks.values()):
        raise ValueError(f"invalid instance: {checks}")
    checks.update({"nP_is_identity": c.mul(n, instance.P) is None,
                   "nQ_is_identity": c.mul(n, instance.Q) is None,
                   "P_encoding_roundtrip": c.decode(c.encode(instance.P)) == instance.P,
                   "Q_encoding_roundtrip": instance.Q is None or c.decode(c.encode(instance.Q)) == instance.Q})
    if c.a in (0, 1) and c.b == 1:
        checks["cofactor_times_order_matches_frobenius_count"] = instance.cofactor * n == koblitz_order(c.field.degree, c.a)
    if not all(checks.values()):
        raise ValueError(f"invalid instance: {checks}")
    return {"status": "valid", "instance": instance.as_dict(), "checks": checks}


def ceil_root(n: int, exponent: int) -> int:
    lo, hi = 0, 1 << ((n.bit_length() + exponent - 1) // exponent)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if mid ** exponent >= n:
            hi = mid
        else:
            lo = mid
    return hi


def parameters(instance: Instance, slots: int) -> dict:
    if slots < 2:
        raise ValueError("at least two factor-base slots are required")
    n = instance.order
    s = int(nextprime(instance.curve.field.size << 1))
    L = max(ceil_root(n, slots), 10 * slots)
    tau = min(s, (s * L + n - 2) // (n - 1))
    expected = min(n - 1, (n - 1) * tau // s)
    split = (slots + 1) // 2
    return {"slots": slots, "hash_prime": str(s), "threshold": tau,
            "expected_points_per_base_floor": expected,
            "enumeration_candidates": slots * tau,
            "estimated_mitm_table_entries": expected ** split,
            "estimated_mitm_query_entries": expected ** (slots - split),
            "generic_rho_log2_expected_group_additions": 0.5 * math.log2(math.pi * n / 2),
            "relation_backend": "meet_in_middle",
            "conditional_tensor_contraction_implemented": False}


@dataclass
class FactorBase:
    prime: int
    alpha: int
    beta: int
    threshold: int
    points: list[Point]

    def contains_encoding(self, z: int) -> bool:
        return (self.alpha * z + self.beta) % self.prime < self.threshold

    @classmethod
    def build(cls, instance: Instance, prime: int, threshold: int, rng: random.Random,
              deadline: float) -> FactorBase:
        alpha, beta = rng.randrange(1, prime), rng.randrange(prime)
        inverse = pow(alpha, -1, prime)
        c, points = instance.curve, []
        for value in range(threshold):
            if time.monotonic() >= deadline:
                raise BudgetExceeded("time budget exhausted during factor-base enumeration")
            z = inverse * (value - beta) % prime
            point = c.decode(z)
            if point is not None and c.mul(instance.order, point) is None:
                points.append(point)
        return cls(prime, alpha, beta, threshold, points)

    def as_dict(self, curve: BinaryCurve) -> dict:
        return {"prime": str(self.prime), "alpha": str(self.alpha), "beta": str(self.beta),
                "threshold": self.threshold, "points": [hex(curve.encode(p)) for p in self.points]}


class MITMRelations:
    """Exact relation search, with exponential lists; no tensor-solver claim."""

    def __init__(self, curve: BinaryCurve, bases: list[FactorBase], max_states: int,
                 deadline: float):
        self.curve, self.bases, self.deadline = curve, bases, deadline
        self.split = (len(bases) + 1) // 2
        sizes = [len(base.points) for base in bases]
        left_count = math.prod(sizes[:self.split])
        right_count = math.prod(sizes[self.split:])
        if left_count + right_count > max_states:
            raise BudgetExceeded(f"actual meet-in-the-middle lists need {left_count + right_count} entries; limit {max_states}")
        self.table = {}
        for point, indices in self.sums(0, self.split):
            self.table.setdefault(point, indices)
        self.right = list(self.sums(self.split, len(bases)))

    def sums(self, start: int, end: int) -> Iterator[tuple[Point, tuple[int, ...]]]:
        ranges = [range(len(b.points)) for b in self.bases[start:end]]
        for indices in itertools.product(*ranges):
            if time.monotonic() >= self.deadline:
                raise BudgetExceeded("time budget exhausted in meet-in-the-middle relation search")
            point = self.curve.total(self.bases[start + i].points[j] for i, j in enumerate(indices))
            yield point, indices

    def find(self, target: Point) -> tuple[int, ...] | None:
        for point, indices in self.right:
            if time.monotonic() >= self.deadline:
                raise BudgetExceeded("time budget exhausted in meet-in-the-middle relation search")
            needed = self.curve.add(target, self.curve.neg(point))
            if needed in self.table:
                return self.table[needed] + indices
        return None


class RelationElimination:
    def __init__(self, columns: int, order: int):
        self.columns, self.order = columns, order
        self.pivots: dict[int, tuple[list[int], dict[int, int]]] = {}

    def add(self, row: list[int], u: int, v: int, index: int) -> tuple[int, int, dict[int, int]] | None:
        n = self.order
        row = [x % n for x in row] + [u % n, v % n]
        weights = {index: 1}
        for column in sorted(self.pivots):
            factor = row[column]
            if not factor:
                continue
            pivot, history = self.pivots[column]
            for j in range(column, len(row)):
                row[j] = (row[j] - factor * pivot[j]) % n
            for j, value in history.items():
                weights[j] = (weights.get(j, 0) - factor * value) % n
        column = next((i for i, v in enumerate(row[:self.columns]) if v), None)
        if column is None:
            return row[-2], row[-1], {i: w for i, w in weights.items() if w}
        inverse = pow(row[column], -1, n)
        row = [(value * inverse) % n for value in row]
        weights = {i: value * inverse % n for i, value in weights.items() if value}
        self.pivots[column] = row, weights
        return None


def solve_hashed(instance: Instance, slots: int = 3, seed: int = 1, max_states: int = 200000,
                 max_candidates: int = 200000, seconds: float = 60, trials: int = 16,
                 backend: str = "meet_in_middle") -> dict:
    started = time.monotonic()
    deadline = started + seconds
    estimate = parameters(instance, slots)
    if estimate["enumeration_candidates"] > max_candidates:
        raise BudgetExceeded(f"estimated factor-base enumeration requires {estimate['enumeration_candidates']} candidates; limit {max_candidates}")
    states = estimate["estimated_mitm_table_entries"] + estimate["estimated_mitm_query_entries"]
    if backend == "meet_in_middle" and states > max_states:
        raise BudgetExceeded(f"estimated meet-in-the-middle lists require {states} entries; limit {max_states}")
    rng, c, n = random.Random(seed), instance.curve, instance.order
    if instance.Q is None:
        return {"status": "solved", "scalar": "0", "verified": c.mul(0, instance.P) == instance.Q,
                "instance": instance.as_dict(), "backend": "identity", "elapsed_seconds": time.monotonic() - started}
    for trial in range(trials):
        bases = [FactorBase.build(instance, number(estimate["hash_prime"]), estimate["threshold"], rng, deadline)
                 for _ in range(slots)]
        if any(not base.points for base in bases):
            continue
        if backend == "meet_in_middle":
            finder = MITMRelations(c, bases, max_states, deadline)
        elif backend == "tensor_indexed":
            from tensor_relations import IndexedTensorRelations
            finder = IndexedTensorRelations(c, bases, max_states * 100, deadline)
        elif backend == "tensor_coordinates":
            from tensor_relations import CoordinateTensorRelations
            finder = CoordinateTensorRelations(instance, bases, max_states * 100, deadline)
        else:
            raise ValueError("unknown relation backend")
        sizes = [len(base.points) for base in bases]
        offsets, total = [], 0
        for size in sizes:
            offsets.append(total)
            total += size
        if total * total > max_states * 16:
            raise BudgetExceeded("dense relation-elimination matrix exceeds configured budget")
        elimination = RelationElimination(total, n)
        relations = []
        for attempt in range(20 * (total + 1)):
            if time.monotonic() >= deadline:
                raise BudgetExceeded("time budget exhausted while collecting relations")
            u, v = rng.randrange(n), rng.randrange(n)
            target = c.add(c.mul(u, instance.P), c.mul(v, instance.Q))
            indices = finder.find(target)
            if indices is None:
                continue
            row = [0] * total
            for i, j in enumerate(indices):
                row[offsets[i] + j] = 1
            index = len(relations)
            relations.append({"u": str(u), "v": str(v), "indices": list(indices)})
            dependency = elimination.add(row, u, v, index)
            if dependency is None or dependency[1] == 0:
                continue
            U, V, weights = dependency
            scalar = -U * pow(V, -1, n) % n
            if c.mul(scalar, instance.P) != instance.Q:
                raise ArithmeticError("relation extraction failed independent scalar verification")
            return {"status": "solved", "scalar": str(scalar), "scalar_hex": hex(scalar),
                    "verified": True, "instance": instance.as_dict(), "backend": backend,
                    "conditional_tensor_contraction_implemented": backend.startswith("tensor_"),
                    "tensor_encoding": backend.removeprefix("tensor_") if backend.startswith("tensor_") else None,
                    "tensor_statistics": finder.engine.stats if backend.startswith("tensor_") else None,
                    "subexponential_runtime_claimed": False, "trial": trial + 1,
                    "target_attempts": attempt + 1, "factor_base_sizes": sizes,
                    "relations_collected": len(relations), "matrix_rank": len(elimination.pivots),
                    "bases": [base.as_dict(c) for base in bases], "relations": relations,
                    "dependency": {str(i): str(w) for i, w in weights.items()},
                    "elapsed_seconds": time.monotonic() - started}
    return {"status": "trial_budget_exhausted", "instance": instance.name,
            "elapsed_seconds": time.monotonic() - started}


def verify_certificate(result: dict) -> dict:
    instance = Instance.from_dict(result["instance"])
    validate(instance)
    c, n = instance.curve, instance.order
    scalar = number(result["scalar"])
    if not 0 <= scalar < n or c.mul(scalar, instance.P) != instance.Q:
        raise ValueError("scalar fails Q = [k]P")
    if result.get("backend") == "identity":
        return {"status": "verified", "scalar": str(scalar), "relations_checked": 0}
    bases = []
    for saved in result["bases"]:
        base = FactorBase(number(saved["prime"]), number(saved["alpha"]), number(saved["beta"]),
                          saved["threshold"], [c.decode(number(z)) for z in saved["points"]])
        if not isprime(base.prime) or base.prime <= c.field.size << 1:
            raise ValueError("invalid factor-base hash modulus")
        if not (1 <= base.alpha < base.prime and 0 <= base.beta < base.prime and 1 <= base.threshold <= base.prime):
            raise ValueError("invalid factor-base seed")
        for encoded, point in zip(saved["points"], base.points):
            if (point is None or not c.valid(point) or c.encode(point) != number(encoded)
                    or not base.contains_encoding(number(encoded)) or c.mul(n, point) is not None):
                raise ValueError("invalid factor-base point")
        if len(set(base.points)) != len(base.points):
            raise ValueError("duplicate factor-base entry")
        bases.append(base)
    offsets, total = [], 0
    for base in bases:
        offsets.append(total)
        total += len(base.points)
    cancellation, U, V = [0] * total, 0, 0
    weights = {int(i): number(w) for i, w in result["dependency"].items()}
    relations = result["relations"]
    if not weights or any(i < 0 or i >= len(relations) for i in weights):
        raise ValueError("invalid dependency indices")
    for index, relation in enumerate(relations):
        u, v, indices = number(relation["u"]), number(relation["v"]), relation["indices"]
        if len(indices) != len(bases) or any(j < 0 or j >= len(base.points) for j, base in zip(indices, bases)):
            raise ValueError("invalid relation indices")
        target = c.add(c.mul(u, instance.P), c.mul(v, instance.Q))
        if c.total(base.points[j] for base, j in zip(bases, indices)) != target:
            raise ValueError("invalid additive relation")
        weight = weights.get(index, 0) % n
        U, V = (U + weight * u) % n, (V + weight * v) % n
        for slot, j in enumerate(indices):
            column = offsets[slot] + j
            cancellation[column] = (cancellation[column] + weight) % n
    if any(cancellation) or not V or -U * pow(V, -1, n) % n != scalar:
        raise ValueError("invalid relation cancellation")
    return {"status": "verified", "scalar": str(scalar), "relations_checked": len(relations),
            "factor_base_points_checked": total, "instance": instance.name}


def bsgs(instance: Instance, bound: int, max_states: int, seconds: float) -> dict:
    if not 1 <= bound <= instance.order:
        raise ValueError("bound must be between 1 and subgroup order")
    width = math.isqrt(bound - 1) + 1
    if width > max_states:
        raise BudgetExceeded(f"baby-step table needs {width} points; limit {max_states}")
    started, c = time.monotonic(), instance.curve
    deadline = started + seconds
    table, current = {}, None
    for j in range(width):
        if time.monotonic() >= deadline:
            raise BudgetExceeded("time budget exhausted building baby-step table")
        table.setdefault(current, j)
        current = c.add(current, instance.P)
    step = c.neg(c.mul(width, instance.P))
    current = instance.Q
    count = (bound + width - 1) // width
    for i in range(count):
        if time.monotonic() >= deadline:
            raise BudgetExceeded("time budget exhausted scanning giant steps")
        if current in table:
            scalar = i * width + table[current]
            if scalar < bound and c.mul(scalar, instance.P) == instance.Q:
                return {"status": "solved", "scalar": str(scalar), "verified": True,
                        "backend": "bounded_bsgs", "elapsed_seconds": time.monotonic() - started}
        current = c.add(current, step)
    return {"status": "not_found_in_interval", "interval": ["0", str(bound)],
            "interval_upper_bound_exclusive": True, "table_entries": width,
            "giant_steps": count, "elapsed_seconds": time.monotonic() - started}


def atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(path)


def rho(instance: Instance, max_steps: int, seconds: float, seed: int,
        checkpoint: Path | None = None) -> dict:
    """Resumable reference r-adding rho; budget counts actual walk additions.

    This implementation does not use the Koblitz automorphism speedups.
    A checkpoint is validated against both the instance and coefficient invariants.
    """
    started, c, n = time.monotonic(), instance.curve, instance.order
    rng = random.Random(seed)
    jumps = []
    for _ in range(16):
        a, b = rng.randrange(n), rng.randrange(n)
        jumps.append((c.add(c.mul(a, instance.P), c.mul(b, instance.Q)), a, b))

    def initial(restart: int) -> tuple[Point, int, int]:
        local = random.Random(f"{seed}:restart:{restart}")
        a, b = local.randrange(n), local.randrange(n)
        return c.add(c.mul(a, instance.P), c.mul(b, instance.Q)), a, b

    def step(state: tuple[Point, int, int]) -> tuple[Point, int, int]:
        point, a, b = state
        # Full coordinates make the partition deterministic for equal points.
        encoded = b"O" if point is None else b"P" + point[0].to_bytes((c.field.degree + 7) // 8, "big") + point[1].to_bytes((c.field.degree + 7) // 8, "big")
        slot = hashlib.blake2s(encoded, digest_size=1).digest()[0] & 15
        jump, da, db = jumps[slot]
        return c.add(point, jump), (a + da) % n, (b + db) % n

    restarts, previous_steps = 0, 0
    tortoise = hare = initial(0)
    if checkpoint and checkpoint.exists():
        saved = json.loads(checkpoint.read_text())
        if (saved.get("version") != 1 or saved["instance_sha256"] != instance.fingerprint
                or saved["seed"] != seed):
            raise ValueError("checkpoint belongs to a different instance, seed, or format")
        restarts, previous_steps = saved["restarts"], saved["walk_additions"]
        states = []
        for key in ("tortoise", "hare"):
            point = parse_point(saved[key]["point"])
            a, b = number(saved[key]["a"]), number(saved[key]["b"])
            if not c.valid(point) or c.add(c.mul(a, instance.P), c.mul(b, instance.Q)) != point:
                raise ValueError("checkpoint coefficient invariant failed")
            states.append((point, a, b))
        tortoise, hare = states
    steps, deadline = 0, started + seconds
    while steps + 3 <= max_steps and time.monotonic() < deadline:
        tortoise, hare = step(tortoise), step(step(hare))
        steps += 3
        if tortoise[0] != hare[0]:
            continue
        numerator = (tortoise[1] - hare[1]) % n
        denominator = (hare[2] - tortoise[2]) % n
        if denominator:
            scalar = numerator * pow(denominator, -1, n) % n
            if c.mul(scalar, instance.P) != instance.Q:
                raise ArithmeticError("rho collision failed scalar verification")
            return {"status": "solved", "scalar": str(scalar), "verified": True,
                    "backend": "r_adding_rho", "walk_additions": previous_steps + steps,
                    "elapsed_seconds": time.monotonic() - started}
        restarts += 1
        tortoise = hare = initial(restarts)
    if checkpoint:
        def pack(state):
            return {"point": point_json(state[0]), "a": str(state[1]), "b": str(state[2])}
        atomic_json(checkpoint, {"version": 1, "instance_sha256": instance.fingerprint,
                               "seed": seed, "restarts": restarts,
                               "walk_additions": previous_steps + steps,
                               "tortoise": pack(tortoise), "hare": pack(hare)})
    return {"status": "budget_exhausted", "backend": "r_adding_rho",
            "instance": instance.name, "walk_additions_this_run": steps,
            "walk_additions_total": previous_steps + steps, "restarts": restarts,
            "elapsed_seconds": time.monotonic() - started,
            "checkpoint": str(checkpoint) if checkpoint else None,
            "challenge_solved": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate", "estimate", "demo", "hashed", "verify", "bsgs", "rho"])
    parser.add_argument("--slots", type=int, default=3)
    parser.add_argument("--backend", choices=["meet_in_middle", "tensor_indexed", "tensor_coordinates"], default="meet_in_middle")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--degree", type=int, choices=[7, 13, 19], default=19)
    parser.add_argument("--secret", type=lambda x: int(x, 0), default=114415,
                        help="demo generation only; never passed to the solver")
    parser.add_argument("--max-states", type=int, default=200000)
    parser.add_argument("--max-candidates", type=int, default=200000)
    parser.add_argument("--seconds", type=float, default=30)
    parser.add_argument("--steps", type=int, default=100000)
    parser.add_argument("--bound", type=lambda x: int(x, 0), default=1 << 24)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--certificate", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if min(args.max_states, args.max_candidates, args.seconds, args.steps) <= 0:
        parser.error("budgets must be positive")
    try:
        instance = toy(args.degree, args.secret) if args.command == "demo" else challenge()
        if args.command == "validate":
            result = validate(instance)
            d = json.loads((ROOT / "challenge.json").read_text())
            result["checks"]["published_P_equals_hU"] = instance.curve.mul(instance.cofactor, parse_point(d["U"])) == instance.P
            result["checks"]["published_Q_equals_hV"] = instance.curve.mul(instance.cofactor, parse_point(d["V"])) == instance.Q
            if not all(result["checks"].values()):
                raise ValueError("published cofactor point checks failed")
        elif args.command == "estimate":
            result = {"instance": instance.name, **parameters(instance, args.slots)}
        elif args.command in ("demo", "hashed"):
            result = solve_hashed(instance, args.slots, args.seed, args.max_states,
                                  args.max_candidates, args.seconds, backend=args.backend)
            if args.command == "demo" and result["status"] == "solved":
                result["demo_only"] = True
                result["demo_expected_scalar"] = str(args.secret % instance.order)
                result["certificate_verification"] = verify_certificate(result)
        elif args.command == "verify":
            if not args.certificate:
                parser.error("verify requires --certificate")
            result = verify_certificate(json.loads(args.certificate.read_text()))
        elif args.command == "bsgs":
            validate(instance)
            result = bsgs(instance, args.bound, args.max_states, args.seconds)
        else:
            validate(instance)
            result = rho(instance, args.steps, args.seconds, args.seed, args.checkpoint)
    except BudgetExceeded as exc:
        result = {"status": "budget_exhausted", "reason": str(exc), "challenge_solved": False}
    if args.output:
        atomic_json(args.output, result)
    summary = {k: v for k, v in result.items() if k not in ("bases", "relations", "dependency")}
    print(json.dumps(summary, indent=2))
    return 0 if result.get("status") in ("solved", "valid", "verified") or args.command == "estimate" else 2


if __name__ == "__main__":
    raise SystemExit(main())
