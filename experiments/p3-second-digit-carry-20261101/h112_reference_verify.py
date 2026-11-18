#!/usr/bin/env python3
"""Independent replay verifier for H112's p^3 carry artifact.

This file intentionally imports no canonical H112 code.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
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

    def on_curve(self, q: Point) -> bool:
        if q is None:
            return True
        x, y = q
        return (y * y - x**3 - self.a * x - self.b) % self.p == 0

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
        out = (x3, (slope * (x1 - x3) - y1) % self.p)
        if not self.on_curve(out):
            raise AssertionError("base addition left curve")
        return out

    def mul(self, scalar: int, point: Point) -> Point:
        out: Point = None
        addend = point
        while scalar:
            if scalar & 1:
                out = self.add(out, addend)
            addend = self.add(addend, addend)
            scalar >>= 1
        return out


CURVES = {c.name: c for c in (
    Curve(101, 6, 9, 83, "E101"), Curve(127, 1, 7, 109, "E127"),
    Curve(149, 2, 8, 139, "E149"), Curve(211, 1, 1, 223, "E211"),
    Curve(283, 2, 7, 281, "E283"), Curve(503, 3, 8, 499, "E503"),
    Curve(907, 1, 1, 947, "E907"),
)}


def seed(*parts: object) -> int:
    return int.from_bytes(hashlib.sha256("|".join(map(str, parts)).encode()).digest()[:16], "big")


def orbit(curve: Curve, generator: tuple[int, int]) -> list[Point]:
    out: list[Point] = [None]
    q: Point = None
    for _ in range(1, curve.r):
        q = curve.add(q, generator)
        out.append(q)
    if curve.add(out[-1], generator) is not None or len(set(out)) != curve.r:
        raise AssertionError("orbit certificate failed")
    return out


def lift(curve: Curve, q: tuple[int, int], u1: int, u2: int) -> tuple[int, int]:
    p, n = curve.p, curve.p**3
    x, y = q
    xx = (x + p * (u1 % p) + p * p * (u2 % p)) % n
    rhs = (xx**3 + curve.a * xx + curve.b) % n
    yy, modulus = y, p
    for _ in range(2):
        d = rhs - yy * yy
        if d % modulus:
            raise AssertionError("Hensel divisibility failed")
        yy = (yy + modulus * ((d // modulus) * pow(2 * yy, -1, p) % p)) % (modulus * p)
        modulus *= p
    out = xx, yy % n
    if (out[1] ** 2 - out[0] ** 3 - curve.a * out[0] - curve.b) % n:
        raise AssertionError("Hensel lift missed curve")
    return out


def add_lifted(curve: Curve, left: Point, right: Point) -> Point:
    if left is None:
        return right
    if right is None:
        return left
    n, p = curve.p**3, curve.p
    x1, y1 = left
    x2, y2 = right
    if left == right:
        numerator, denominator = (3 * x1 * x1 + curve.a) % n, 2 * y1 % n
    else:
        numerator, denominator = (y2 - y1) % n, (x2 - x1) % n
    if denominator % p == 0:
        raise ZeroDivisionError("nonunit lifted denominator")
    slope = numerator * pow(denominator, -1, n) % n
    x3 = (slope * slope - x1 - x2) % n
    out = x3, (slope * (x1 - x3) - y1) % n
    if (out[1] ** 2 - out[0] ** 3 - curve.a * out[0] - curve.b) % n:
        raise AssertionError("lifted addition left curve")
    return out


def mul_lifted(curve: Curve, scalar: int, point: tuple[int, int]) -> Point:
    out: Point = None
    addend: Point = point
    while scalar:
        if scalar & 1:
            out = add_lifted(curve, out, addend)
        scalar >>= 1
        if scalar:
            addend = add_lifted(curve, addend, addend)
    return out


def formal_sum(curve: Curve, left: tuple[int, int], right: tuple[int, int]) -> int:
    n, p = curve.p**3, curve.p
    x1, y1 = left
    x2, y2 = right
    h = (x2 - x1) % n
    two_h = 2 * h % n
    i = two_h * two_h % n
    j = h * i % n
    rr = 2 * (y2 - y1) % n
    v = x1 * i % n
    x3 = (rr * rr - j - 2 * v) % n
    y3 = (rr * (v - x3) - 2 * y1 * j) % n
    if two_h % p or y3 % p == 0:
        raise AssertionError("kernel chart failed")
    t = -x3 * two_h * pow(y3, -1, n) % n
    if t % p:
        raise AssertionError("formal divisibility failed")
    return t // p % (p * p)


def carry(curve: Curve, half: tuple[int, int], target: tuple[int, int], hu=(0, 0), tu=(0, 0)) -> tuple[int, int]:
    lh = lift(curve, half, *hu)
    doubled = add_lifted(curve, lh, lh)
    if doubled is None or (doubled[0] % curve.p, doubled[1] % curve.p) != target:
        raise AssertionError("double reduction failed")
    lt = lift(curve, target, *tu)
    word = formal_sum(curve, doubled, (lt[0], -lt[1] % (curve.p**3)))
    return word % curve.p, word // curve.p


def torsion_word(curve: Curve, point: tuple[int, int], correction: tuple[int, int]) -> int:
    lifted = lift(curve, point, *correction)
    split = (curve.r - 1) // 2
    left = mul_lifted(curve, split, lifted)
    right = mul_lifted(curve, curve.r - split, lifted)
    if left is None or right is None:
        raise AssertionError("torsion split failed")
    return formal_sum(curve, left, right)


def base_bit(value: int, p: int, kind: str) -> int:
    z = value % p
    if kind == "zero": return int(z == 0)
    if kind == "integer_lsb": return z & 1
    if kind == "centered": return int(z > (p - 1) // 2)
    if kind == "legendre": return int(z != 0 and pow(z, (p - 1) // 2, p) == p - 1)
    raise ValueError(kind)


def predicates() -> list[dict]:
    kinds = ("zero", "integer_lsb", "centered", "legendre")
    depth = [{"id": f"depth:{ch}:offset_{o:+d}:{k}:complement_{c}", "family": "depth", "channel": ch, "offset": o, "kind": k, "complement": c} for ch in ("high", "sum", "difference") for o in (-1, 0, 1) for k in kinds for c in (0, 1)]
    cross = [{"id": f"cross:low_{lo:+d}:high_{hi:+d}:{k}:complement_{c}", "family": "cross", "low_offset": lo, "high_offset": hi, "kind": k, "complement": c} for lo in (-1, 0, 1) for hi in (-1, 0, 1) for k in kinds for c in (0, 1)]
    return depth + cross


PREDICATES = predicates()


def predicate_bit(word: tuple[int, int], p: int, spec: dict) -> int:
    low, high = word
    if spec["family"] == "depth":
        value = {"high": high, "sum": low + high, "difference": high - low}[spec["channel"]]
        bit = base_bit(value + spec["offset"], p, spec["kind"])
    else:
        bit = base_bit(low + spec["low_offset"], p, spec["kind"])
        bit ^= base_bit(high + spec["high_offset"], p, spec["kind"])
    return bit ^ spec["complement"]


def score(words: Sequence[tuple[int, int]], labels: Sequence[int], p: int) -> dict:
    scores = []
    for spec in PREDICATES:
        matches = sum(predicate_bit(w, p, spec) == b for w, b in zip(words, labels))
        scores.append({**spec, "matches": matches, "targets": len(labels), "accuracy": matches / len(labels), "exact": matches == len(labels)})
    best = max(x["matches"] for x in scores)
    return {"predicate_count": len(scores), "scores": scores, "best_matches": best, "best_accuracy": best / len(labels), "best_predicate_ids": [x["id"] for x in scores if x["matches"] == best], "exact_predicate_ids": [x["id"] for x in scores if x["exact"]]}


def matched_labels(curve: Curve, replicate: int) -> list[int]:
    labels: list[Optional[int]] = [None] * curve.r
    labels[0] = 0
    rng = random.Random(seed("H112", curve.name, "matched-labels", replicate))
    for scalar in range(1, curve.r):
        partner = curve.r - scalar
        if labels[scalar] is None:
            bit = rng.randrange(2)
            labels[scalar], labels[partner] = bit, 1 - bit
    return [int(x) for x in labels[1:]]


def stable_digest(result: dict) -> str:
    def scrub(value):
        if isinstance(value, dict):
            return {k: scrub(v) for k, v in value.items() if not k.endswith("elapsed_ns") and k not in {"scientific_payload_sha256", "environment"}}
        if isinstance(value, list): return [scrub(x) for x in value]
        return value
    return hashlib.sha256(json.dumps(scrub(result), sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def eq(actual, expected, context: str) -> None:
    if actual != expected:
        raise AssertionError(f"{context}: {actual!r} != {expected!r}")


def verify(path: Path) -> dict:
    result = json.loads(path.read_text())
    eq(result["protocol"]["predicate_family"], PREDICATES, "predicate family")
    eq(result["protocol"]["low_digit_only_predicates"], 0, "low-only exclusion")
    rows = targets = exact = 0
    best = []
    canonical_words = {}
    checked_torsion = set()
    for curve_result in result["curves"]:
        curve = CURVES[curve_result["curve"]]
        base = tuple(curve_result["canonical_generator"])
        for row in curve_result["generators"]:
            generator = tuple(row["generator"])
            eq(generator, curve.mul(row["generator_multiplier"], base), "generator")
            points = orbit(curve, generator)
            words = []
            for scalar, (point, rec) in enumerate(zip(points[1:], row["target_records"]), 1):
                if point is None: raise AssertionError
                half = curve.mul((curve.r + 1) // 2, point)
                if half is None: raise AssertionError
                digits = carry(curve, half, point)
                eq(rec["scalar"], scalar, "scalar")
                eq(rec["digits"], list(digits), "digits")
                hc, tc = tuple(rec["torsion_half_correction"]), tuple(rec["torsion_target_correction"])
                eq(carry(curve, half, point, hc, tc), (0, 0), "torsion carry")
                for q, correction in ((half, hc), (point, tc)):
                    key = curve.name, q, correction
                    if key not in checked_torsion:
                        eq(torsion_word(curve, q, correction), 0, "torsion word")
                        checked_torsion.add(key)
                words.append(digits)
            eq(row["word"], [list(x) for x in words], "word")
            eq(row["word_sha256"], hashlib.sha256(json.dumps(words, separators=(",", ":")).encode()).hexdigest(), "word digest")
            expected = score(words, [k & 1 for k in range(1, curve.r)], curve.p)
            eq(row["predicate_scoring"], expected, "scores")
            if row["generator_multiplier"] == 1: canonical_words[curve.name] = words
            rows += 1; targets += curve.r - 1; best.append(expected["best_accuracy"]); exact += bool(expected["exact_predicate_ids"])

    for curve_name, panel in result["matched_controls"].items():
        curve = CURVES[curve_name]
        cresult = next(x for x in result["curves"] if x["curve"] == curve_name)
        generator = tuple(cresult["canonical_generator"])
        points = orbit(curve, generator)
        parity = [k & 1 for k in range(1, curve.r)]
        for item in panel["random_sections"]:
            rep, words = item["replicate"], []
            for scalar, point in enumerate(points[1:], 1):
                if point is None: raise AssertionError
                half = curve.mul((curve.r + 1) // 2, point)
                if half is None: raise AssertionError
                hu = tuple(seed("H112", curve.name, "half", rep, d, scalar, *half) % curve.p for d in (1, 2))
                tu = tuple(seed("H112", curve.name, "target", rep, d, scalar, *point) % curve.p for d in (1, 2))
                words.append(carry(curve, half, point, hu, tu))
            eq(item["word_sha256"], hashlib.sha256(json.dumps(words, separators=(",", ":")).encode()).hexdigest(), "control digest")
            eq(item["predicate_scoring"], score(words, parity, curve.p), "control scores")
        for item in panel["matched_parity_labels"]:
            labels = matched_labels(curve, item["replicate"])
            eq(item["predicate_scoring"], score(canonical_words[curve_name], labels, curve.p), "label scores")

    for curve_name, item in result["coordinate_isomorphism_controls"].items():
        source = CURVES[curve_name]; lam = item["lambda"]
        curve = Curve(source.p, source.a * pow(lam, 4, source.p) % source.p, source.b * pow(lam, 6, source.p) % source.p, source.r, f"{curve_name}-iso-{lam}")
        base = tuple(next(x for x in result["curves"] if x["curve"] == curve_name)["canonical_generator"])
        generator = (base[0] * pow(lam, 2, source.p) % source.p, base[1] * pow(lam, 3, source.p) % source.p)
        words = []
        for point in orbit(curve, generator)[1:]:
            if point is None: raise AssertionError
            half = curve.mul((curve.r + 1) // 2, point)
            if half is None: raise AssertionError
            words.append(carry(curve, half, point))
        eq(item["word_sha256"], hashlib.sha256(json.dumps(words, separators=(",", ":")).encode()).hexdigest(), "iso digest")
        eq(item["predicate_scoring"], score(words, [k & 1 for k in range(1, curve.r)], curve.p), "iso scores")

    summary = result["summary"]
    for key, value in {"curve_rows": rows, "targets": targets, "predicate_count": 144, "best_accuracy_minimum": min(best), "best_accuracy_median": statistics.median(best), "best_accuracy_maximum": max(best), "rows_with_exact_predicate": exact, "all_structural_checks_passed": True, "all_torsion_carries_zero": True}.items():
        eq(summary[key], value, f"summary {key}")
    eq(result["scientific_payload_sha256"], stable_digest(result), "scientific digest")
    return {"verified": True, "curve_rows": rows, "targets": targets, "rows_with_exact_predicate": exact, "scientific_payload_sha256": result["scientific_payload_sha256"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
