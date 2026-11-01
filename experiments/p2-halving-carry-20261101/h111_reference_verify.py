#!/usr/bin/env python3
"""Independent arithmetic replay and verifier for H111's JSON artifact.

This file intentionally does not import the canonical H111 runner or its
elliptic-curve arithmetic.  It recomputes every canonical and control carry,
the frozen predicates, the structural torsion carry, and the stable digest.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
import random
import statistics
from pathlib import Path
from typing import Optional, Sequence


Point = Optional[tuple[int, int]]


@dataclass(frozen=True)
class Curve:
    p: int
    a: int
    b: int
    r: int
    name: str

    def on_curve(self, point: Point) -> bool:
        if point is None:
            return True
        x, y = point
        return (y * y - x * x * x - self.a * x - self.b) % self.p == 0

    def add(self, left: Point, right: Point) -> Point:
        if left is None:
            return right
        if right is None:
            return left
        x1, y1 = left
        x2, y2 = right
        if x1 == x2 and (y1 + y2) % self.p == 0:
            return None
        if left == right:
            slope = (3 * x1 * x1 + self.a) * pow(2 * y1, -1, self.p) % self.p
        else:
            slope = (y2 - y1) * pow(x2 - x1, -1, self.p) % self.p
        x3 = (slope * slope - x1 - x2) % self.p
        y3 = (slope * (x1 - x3) - y1) % self.p
        out = (x3, y3)
        if not self.on_curve(out):
            raise AssertionError("independent base addition left curve")
        return out

    def neg(self, point: Point) -> Point:
        return None if point is None else (point[0], -point[1] % self.p)

    def mul(self, scalar: int, point: Point) -> Point:
        out: Point = None
        addend = point
        while scalar:
            if scalar & 1:
                out = self.add(out, addend)
            addend = self.add(addend, addend)
            scalar >>= 1
        return out


CURVES = {
    item.name: item
    for item in (
        Curve(101, 6, 9, 83, "E101"),
        Curve(127, 1, 7, 109, "E127"),
        Curve(149, 2, 8, 139, "E149"),
        Curve(211, 1, 1, 223, "E211"),
        Curve(283, 2, 7, 281, "E283"),
        Curve(503, 3, 8, 499, "E503"),
        Curve(907, 1, 1, 947, "E907"),
    )
}


def deterministic_seed(*parts: object) -> int:
    payload = "|".join(map(str, parts)).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:16], "big")


def orbit(curve: Curve, generator: tuple[int, int]) -> list[Point]:
    out: list[Point] = [None]
    current: Point = None
    for _ in range(1, curve.r):
        current = curve.add(current, generator)
        out.append(current)
    if curve.add(out[-1], generator) is not None or len(set(out)) != curve.r:
        raise AssertionError("independent orbit certificate failed")
    return out


def lift(curve: Curve, point: tuple[int, int], u: int) -> tuple[int, int]:
    p = curve.p
    x, y = point
    discrepancy = x**3 + curve.a * x + curve.b - y**2
    if discrepancy % p:
        raise AssertionError("independent lift got off-curve point")
    c = discrepancy // p % p
    tangent = (3 * x * x + curve.a) % p
    v = (c + tangent * (u % p)) * pow(2 * y, -1, p) % p
    lifted = ((x + p * (u % p)) % (p * p), (y + p * v) % (p * p))
    n = p * p
    if (lifted[1] ** 2 - lifted[0] ** 3 - curve.a * lifted[0] - curve.b) % n:
        raise AssertionError("independent Hensel lift missed lifted curve")
    return lifted


def double_lifted(curve: Curve, point: tuple[int, int]) -> tuple[int, int]:
    n = curve.p * curve.p
    x, y = point
    slope = (3 * x * x + curve.a) * pow(2 * y % n, -1, n) % n
    x3 = (slope * slope - 2 * x) % n
    y3 = (slope * (x - x3) - y) % n
    if (y3 * y3 - x3**3 - curve.a * x3 - curve.b) % n:
        raise AssertionError("independent lifted doubling left curve")
    return x3, y3


def carry(curve: Curve, half: tuple[int, int], target: tuple[int, int], half_u: int, target_u: int) -> int:
    n, p = curve.p * curve.p, curve.p
    x1, y1 = double_lifted(curve, lift(curve, half, half_u))
    x2, target_y = lift(curve, target, target_u)
    y2 = -target_y % n
    if (x1 % p, y1 % p) != target:
        raise AssertionError("independent lifted double reduced incorrectly")
    h = (x2 - x1) % n
    two_h = 2 * h % n
    i = two_h * two_h % n
    j = h * i % n
    rr = 2 * (y2 - y1) % n
    v = x1 * i % n
    x3 = (rr * rr - j - 2 * v) % n
    y3 = (rr * (v - x3) - 2 * y1 * j) % n
    z3 = two_h
    if z3 % p:
        raise AssertionError("independent carry missed kernel")
    if y3 % p == 0:
        raise AssertionError("independent kernel Y is not a unit")
    t = -x3 * z3 * pow(y3, -1, n) % n
    if t % p:
        raise AssertionError("independent formal coordinate not divisible by p")
    return t // p % p


def predicates() -> list[dict]:
    return [
        {
            "id": f"offset_{offset:+d}:{kind}:complement_{complement}",
            "offset": offset,
            "kind": kind,
            "complement": complement,
        }
        for offset in (-1, 0, 1)
        for kind in ("zero", "integer_lsb", "centered", "legendre")
        for complement in (0, 1)
    ]


PREDICATES = predicates()


def predicate_bit(value: int, prime: int, spec: dict) -> int:
    z = (value + spec["offset"]) % prime
    if spec["kind"] == "zero":
        bit = int(z == 0)
    elif spec["kind"] == "integer_lsb":
        bit = z & 1
    elif spec["kind"] == "centered":
        bit = int(z > (prime - 1) // 2)
    elif spec["kind"] == "legendre":
        bit = int(z != 0 and pow(z, (prime - 1) // 2, prime) == prime - 1)
    else:
        raise AssertionError("unknown frozen predicate")
    return bit ^ spec["complement"]


def score(values: Sequence[int], labels: Sequence[int], prime: int) -> dict:
    scores = []
    for spec in PREDICATES:
        matches = sum(predicate_bit(v, prime, spec) == b for v, b in zip(values, labels))
        scores.append({
            **spec,
            "matches": matches,
            "targets": len(labels),
            "accuracy": matches / len(labels),
            "exact": matches == len(labels),
        })
    best = max(item["matches"] for item in scores)
    return {
        "predicate_count": len(scores),
        "scores": scores,
        "best_matches": best,
        "best_accuracy": best / len(labels),
        "best_predicate_ids": [item["id"] for item in scores if item["matches"] == best],
        "exact_predicate_ids": [item["id"] for item in scores if item["exact"]],
    }


def matched_labels(curve: Curve, replicate: int) -> list[int]:
    labels: list[Optional[int]] = [None] * curve.r
    labels[0] = 0
    rng = random.Random(deterministic_seed("H111", curve.name, "matched-labels", replicate))
    for scalar in range(1, curve.r):
        partner = curve.r - scalar
        if labels[scalar] is None:
            bit = rng.randrange(2)
            labels[scalar] = bit
            labels[partner] = 1 - bit
    return [int(value) for value in labels[1:]]


def stable_digest(result: dict) -> str:
    def scrub(value):
        if isinstance(value, dict):
            return {
                key: scrub(item)
                for key, item in value.items()
                if not key.endswith("elapsed_ns")
                and key not in {"scientific_payload_sha256", "environment"}
            }
        if isinstance(value, list):
            return [scrub(item) for item in value]
        return value
    payload = json.dumps(scrub(result), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def check_equal(actual, expected, context: str) -> None:
    if actual != expected:
        raise AssertionError(f"{context}: {actual!r} != {expected!r}")


def recompute_row(curve: Curve, generator: tuple[int, int], row: dict) -> list[int]:
    points = orbit(curve, generator)
    values = []
    check_equal(len(row["target_records"]), curve.r - 1, f"{curve.name} record count")
    for scalar, (point, record) in enumerate(zip(points[1:], row["target_records"]), start=1):
        if point is None:
            raise AssertionError
        check_equal(record["scalar"], scalar, "record scalar")
        check_equal(record["point"], list(point), "record point")
        half = curve.mul((curve.r + 1) // 2, point)
        if half is None or curve.add(half, half) != point:
            raise AssertionError("independent public half failed")
        check_equal(record["half"], list(half), "record half")
        value = carry(curve, half, point, 0, 0)
        check_equal(record["kappa"], value, "canonical carry")
        torsion = carry(curve, half, point, record["torsion_half_u"], record["torsion_target_u"])
        check_equal(torsion, 0, "torsion carry")
        check_equal(record["torsion_carry"], 0, "recorded torsion carry")
        values.append(value)
    check_equal(row["word"], values, "canonical word")
    word_sha = hashlib.sha256(json.dumps(values, separators=(",", ":")).encode()).hexdigest()
    check_equal(row["word_sha256"], word_sha, "canonical word digest")
    expected_score = score(values, [k & 1 for k in range(1, curve.r)], curve.p)
    check_equal(row["predicate_scoring"], expected_score, "canonical predicate scores")
    return values


def verify(path: Path) -> dict:
    result = json.loads(path.read_text())
    check_equal(result["protocol"]["predicate_family"], PREDICATES, "frozen predicate family")
    row_count = 0
    target_count = 0
    best_accuracies = []
    exact_rows = 0
    canonical_words = {}
    for curve_result in result["curves"]:
        curve = CURVES[curve_result["curve"]]
        check_equal(curve_result["parameters"], {"p": curve.p, "a": curve.a, "b": curve.b, "r": curve.r}, "curve parameters")
        base = tuple(curve_result["canonical_generator"])
        if not curve.on_curve(base) or curve.mul(curve.r, base) is not None:
            raise AssertionError("canonical generator certificate failed")
        for row in curve_result["generators"]:
            generator = tuple(row["generator"])
            check_equal(generator, curve.mul(row["generator_multiplier"], base), "generator relabeling")
            word = recompute_row(curve, generator, row)
            if row["generator_multiplier"] == 1:
                canonical_words[curve.name] = word
            row_count += 1
            target_count += curve.r - 1
            best_accuracies.append(row["predicate_scoring"]["best_accuracy"])
            exact_rows += bool(row["predicate_scoring"]["exact_predicate_ids"])
            if row["decoder"] is not None:
                for formula in row["decoder"]["formulas"]:
                    for record in formula["records"]:
                        check_equal(
                            curve.mul(record["recovered_scalar"], generator),
                            curve.mul(record["target_scalar"], generator),
                            "decoded EC verification",
                        )

    for curve_name, panel in result["matched_controls"].items():
        curve = CURVES[curve_name]
        generator = tuple(next(x for x in result["curves"] if x["curve"] == curve_name)["canonical_generator"])
        points = orbit(curve, generator)
        parity = [k & 1 for k in range(1, curve.r)]
        for item in panel["random_sections"]:
            replicate = item["replicate"]
            word = []
            for scalar, point in enumerate(points[1:], start=1):
                if point is None:
                    raise AssertionError
                half = curve.mul((curve.r + 1) // 2, point)
                if half is None:
                    raise AssertionError
                half_u = deterministic_seed("H111", curve.name, "half-section", replicate, scalar, *half) % curve.p
                target_u = deterministic_seed("H111", curve.name, "target-section", replicate, scalar, *point) % curve.p
                word.append(carry(curve, half, point, half_u, target_u))
            digest = hashlib.sha256(json.dumps(word, separators=(",", ":")).encode()).hexdigest()
            check_equal(item["word_sha256"], digest, "random-section word digest")
            check_equal(item["predicate_scoring"], score(word, parity, curve.p), "random-section scores")
        for item in panel["matched_parity_labels"]:
            labels = matched_labels(curve, item["replicate"])
            digest = hashlib.sha256(json.dumps(labels, separators=(",", ":")).encode()).hexdigest()
            check_equal(item["labels_sha256"], digest, "matched-label digest")
            check_equal(item["negation_complementary"], True, "matched-label symmetry")
            check_equal(item["predicate_scoring"], score(canonical_words[curve_name], labels, curve.p), "matched-label scores")

    for curve_name, item in result["coordinate_isomorphism_controls"].items():
        source = CURVES[curve_name]
        lam = item["lambda"]
        transformed = Curve(
            source.p,
            source.a * pow(lam, 4, source.p) % source.p,
            source.b * pow(lam, 6, source.p) % source.p,
            source.r,
            f"{curve_name}-iso-{lam}",
        )
        base = tuple(next(x for x in result["curves"] if x["curve"] == curve_name)["canonical_generator"])
        generator = (base[0] * pow(lam, 2, source.p) % source.p, base[1] * pow(lam, 3, source.p) % source.p)
        values = []
        for point in orbit(transformed, generator)[1:]:
            if point is None:
                raise AssertionError
            half = transformed.mul((transformed.r + 1) // 2, point)
            if half is None:
                raise AssertionError
            values.append(carry(transformed, half, point, 0, 0))
        digest = hashlib.sha256(json.dumps(values, separators=(",", ":")).encode()).hexdigest()
        check_equal(item["word_sha256"], digest, "isomorphic word digest")
        check_equal(item["predicate_scoring"], score(values, [k & 1 for k in range(1, transformed.r)], transformed.p), "isomorphic scores")
        check_equal(item["torsion_zero_for_all_targets"], True, "isomorphic torsion control")

    expected_summary = {
        "curve_rows": row_count,
        "targets": target_count,
        "predicate_count": 24,
        "best_accuracy_minimum": min(best_accuracies),
        "best_accuracy_median": statistics.median(best_accuracies),
        "best_accuracy_maximum": max(best_accuracies),
        "rows_with_exact_predicate": exact_rows,
        "rows_decoded": exact_rows,
        "decoded_targets": result["summary"]["decoded_targets"],
        "all_structural_checks_passed": True,
        "all_torsion_carries_zero": True,
    }
    if exact_rows == 0:
        expected_summary["decoded_targets"] = 0
    check_equal(result["summary"], expected_summary, "summary")
    check_equal(result["scientific_payload_sha256"], stable_digest(result), "scientific digest")
    return {
        "verified": True,
        "curve_rows": row_count,
        "targets": target_count,
        "rows_with_exact_predicate": exact_rows,
        "scientific_payload_sha256": result["scientific_payload_sha256"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
