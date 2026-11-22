#!/usr/bin/env python3
"""Prime-field companion for the published Certicom ECCp-131 instance.

Reuses hash enumeration, relation collection, tensor contraction and certificate
replay. This is development reference code, not a claim of challenge recovery.
"""

from dataclasses import dataclass
import argparse
import json
import math
from pathlib import Path

from sympy import isprime

from ecc2k import (Instance, Point, ROOT, BudgetExceeded, atomic_json, number,
                   parameters, parse_point, point_json, solve_hashed,
                   verify_certificate)


@dataclass(frozen=True)
class PrimeField:
    modulus: int

    def __post_init__(self):
        if self.modulus <= 3 or not isprime(self.modulus):
            raise ValueError("prime-field modulus must be prime and greater than 3")

    @property
    def size(self):
        return self.modulus

    @property
    def degree(self):
        """Coordinate bit width; not an extension degree."""
        return self.modulus.bit_length()

    def mul(self, a, b):
        return a * b % self.modulus

    def square(self, a):
        return a * a % self.modulus

    def inv(self, a):
        if not a % self.modulus:
            raise ZeroDivisionError("inverse of zero")
        return pow(a, -1, self.modulus)

    def div(self, a, b):
        return self.mul(a, self.inv(b))

    def sqrt(self, value):
        """Tonelli-Shanks, including zero and nonsquare rejection."""
        p, value = self.modulus, value % self.modulus
        if value == 0:
            return 0
        if pow(value, (p - 1) // 2, p) != 1:
            return None
        if p % 4 == 3:
            return pow(value, (p + 1) // 4, p)
        odd, exponent = p - 1, 0
        while not odd & 1:
            odd >>= 1
            exponent += 1
        nonresidue = 2
        while pow(nonresidue, (p - 1) // 2, p) != p - 1:
            nonresidue += 1
        c = pow(nonresidue, odd, p)
        x, t, m = pow(value, (odd + 1) // 2, p), pow(value, odd, p), exponent
        while t != 1:
            i, power = 1, t * t % p
            while power != 1:
                power = power * power % p
                i += 1
            b = pow(c, 1 << (m - i - 1), p)
            x, t, c, m = x * b % p, t * b * b % p, b * b % p, i
        return x


@dataclass(frozen=True)
class PrimeCurve:
    field: PrimeField
    a: int
    b: int

    def __post_init__(self):
        p = self.field.size
        if not (0 <= self.a < p and 0 <= self.b < p):
            raise ValueError("curve coefficients must be canonical")
        if (4 * self.a ** 3 + 27 * self.b ** 2) % p == 0:
            raise ValueError("singular curve")

    def valid(self, point: Point):
        if point is None:
            return True
        x, y = point
        p = self.field.size
        return 0 <= x < p and 0 <= y < p and (y * y - x ** 3 - self.a * x - self.b) % p == 0

    def neg(self, point):
        return None if point is None else (point[0], -point[1] % self.field.size)

    def add(self, left, right):
        if left is None:
            return right
        if right is None:
            return left
        p = self.field.size
        x1, y1 = left
        x2, y2 = right
        if x1 == x2:
            if y1 != y2 or y1 == 0:
                return None
            slope = (3 * x1 * x1 + self.a) * pow(2 * y1, -1, p) % p
        else:
            slope = (y2 - y1) * pow(x2 - x1, -1, p) % p
        x3 = (slope * slope - x1 - x2) % p
        return x3, (slope * (x1 - x3) - y1) % p

    def mul(self, scalar, point):
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

    def total(self, points):
        result = None
        for point in points:
            result = self.add(result, point)
        return result

    def encode(self, point):
        if point is None or not self.valid(point):
            raise ValueError("encoding requires a valid finite point")
        return 2 * point[0] + (point[1] & 1)

    def decode(self, encoded):
        if not 0 <= encoded < 2 * self.field.size:
            return None
        x, bit = encoded >> 1, encoded & 1
        root = self.field.sqrt(x ** 3 + self.a * x + self.b)
        if root is None or (root == 0 and bit):
            return None
        if root & 1 != bit:
            root = -root % self.field.size
        return x, root


@dataclass(frozen=True)
class PrimeInstance(Instance):
    curve: PrimeCurve

    def as_dict(self):
        return {"name": self.name, "field_type": "prime", "prime": hex(self.curve.field.size),
                "a": hex(self.curve.a), "b": hex(self.curve.b), "order": str(self.order),
                "cofactor": self.cofactor, "P": point_json(self.P), "Q": point_json(self.Q)}

    @classmethod
    def from_dict(cls, d):
        curve = PrimeCurve(PrimeField(number(d["prime"])), number(d["a"]), number(d["b"]))
        return cls(d["name"], curve, number(d["order"]), d["cofactor"],
                   parse_point(d["P"]), parse_point(d["Q"]))


def challenge():
    return PrimeInstance.from_dict(json.loads((ROOT / "eccp131.json").read_text()))


def toy(fixture_scalar=7):
    """Public known-answer target for bounded correctness checks."""
    curve, P = PrimeCurve(PrimeField(17), 2, 2), (5, 1)
    return PrimeInstance("DEMO-Fp17-order19", curve, 19, 1, P, curve.mul(fixture_scalar % 19, P))


def validate(instance):
    c, n, h = instance.curve, instance.order, instance.cofactor
    p = c.field.size
    checks = {"field_modulus_prime": bool(isprime(p)), "subgroup_order_prime": bool(isprime(n)),
              "P_nonidentity": instance.P is not None, "P_on_curve": c.valid(instance.P),
              "Q_on_curve": c.valid(instance.Q), "positive_coprime_cofactor": h > 0 and math.gcd(h, n) == 1}
    if not all(checks.values()):
        raise ValueError(f"invalid instance: {checks}")
    checks.update({"nP_is_identity": c.mul(n, instance.P) is None,
                   "nQ_is_identity": c.mul(n, instance.Q) is None,
                   "P_encoding_roundtrip": c.decode(c.encode(instance.P)) == instance.P,
                   "Q_encoding_roundtrip": instance.Q is None or c.decode(c.encode(instance.Q)) == instance.Q})
    radius = math.isqrt(4 * p)
    first, last = (p + 1 - radius + n - 1) // n, (p + 1 + radius) // n
    if first == last:
        method = "unique multiple of certified prime point order in Hasse interval"
        checks["curve_cardinality_matches_cofactor_times_order"] = first == h
    elif p <= 65521:
        count = 1 + sum(1 if (y2 := (x ** 3 + c.a * x + c.b) % p) == 0
                        else 2 if pow(y2, (p - 1) // 2, p) == 1 else 0 for x in range(p))
        method = "exact small-field point count"
        checks["curve_cardinality_matches_cofactor_times_order"] = count == h * n
    else:
        raise ValueError("cofactor not certified: Hasse interval contains multiple order multiples")
    if not all(checks.values()):
        raise ValueError(f"invalid instance: {checks}")
    return {"status": "valid", "instance": instance.as_dict(), "checks": checks,
            "cardinality_check": method}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "estimate", "hashed", "demo", "verify"))
    parser.add_argument("--slots", type=int, default=2)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--fixture-scalar", "--secret", dest="fixture_scalar", type=int, default=7, help="public demo target only")
    parser.add_argument("--backend", choices=("tensor_indexed", "tensor_coordinates", "meet_in_middle"), default="tensor_indexed")
    parser.add_argument("--seconds", type=float, default=60)
    parser.add_argument("--max-states", type=int, default=200000)
    parser.add_argument("--max-candidates", type=int, default=200000)
    parser.add_argument("--certificate", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "verify" and args.certificate is None:
        parser.error("verify requires --certificate")
    instance = toy(args.fixture_scalar) if args.command == "demo" else challenge()
    try:
        if args.command == "validate":
            result = validate(instance)
        elif args.command == "estimate":
            result = parameters(instance, args.slots)
        elif args.command == "verify":
            result = verify_certificate(json.loads(args.certificate.read_text()))
        else:
            validate(instance)
            result = solve_hashed(instance, slots=args.slots, seed=args.seed, max_states=args.max_states,
                                  max_candidates=args.max_candidates, seconds=args.seconds, backend=args.backend)
            if result.get("status") == "solved":
                result["certificate_verification"] = verify_certificate(result)
    except BudgetExceeded as exc:
        result = {"status": "budget_exhausted", "reason": str(exc), "challenge_solved": False}
    if args.output:
        atomic_json(args.output, result)
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") in ("valid", "verified", "solved") or args.command == "estimate" else 2


if __name__ == "__main__":
    raise SystemExit(main())
