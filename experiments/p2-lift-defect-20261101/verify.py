#!/usr/bin/env python3
"""Independent standard-library verifier for the H110 result artifact."""

from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import json
import math
from pathlib import Path
import random


EXPECTED_RESULT_SHA256 = "7d6c390d0156a4ed101bddd0969132a85505fa884282ef505dc4621b7852124e"
EXPECTED_SCIENTIFIC_SHA256 = "3397823fe3f55fe008797bb87b31324b7ae33efb5699fe479e8e58f5832db4de"


def load_payload(path: Path) -> bytes:
    raw = path.read_bytes()
    return gzip.decompress(raw) if path.suffix == ".gz" else raw


def scientific_payload_sha256(result: dict) -> str:
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


def seed(*parts: object) -> int:
    payload = "|".join(map(str, parts)).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:16], "big")


def ec_add(left, right, p: int, a: int):
    if left is None:
        return right
    if right is None:
        return left
    x1, y1 = left
    x2, y2 = right
    if x1 == x2 and (y1 + y2) % p == 0:
        return None
    if left == right:
        slope = (3 * x1 * x1 + a) * pow(2 * y1, -1, p) % p
    else:
        slope = (y2 - y1) * pow(x2 - x1, -1, p) % p
    x3 = (slope * slope - x1 - x2) % p
    return x3, (slope * (x1 - x3) - y1) % p


def ec_mul(scalar: int, point, p: int, a: int):
    out = None
    addend = point
    while scalar:
        if scalar & 1:
            out = ec_add(out, addend, p, a)
        scalar >>= 1
        if scalar:
            addend = ec_add(addend, addend, p, a)
    return out


def orbit(generator, p: int, a: int, r: int):
    values = [None]
    current = None
    for _ in range(1, r):
        current = ec_add(current, generator, p, a)
        values.append(current)
    if ec_add(values[-1], generator, p, a) is not None:
        raise AssertionError("orbit order mismatch")
    return values


def hensel(point, u: int, p: int, a: int, b: int):
    x, y = point
    discrepancy = x**3 + a * x + b - y**2
    if discrepancy % p:
        raise AssertionError("bad reduced point")
    c = discrepancy // p % p
    v = (c + (3 * x * x + a) * u) * pow(2 * y, -1, p) % p
    n = p * p
    lifted = ((x + p * u) % n, (y + p * v) % n)
    if (lifted[1]**2 - lifted[0]**3 - a * lifted[0] - b) % n:
        raise AssertionError("bad Hensel lift")
    return lifted


def affine_add(left, right, p: int, a: int, b: int):
    if left is None:
        return right
    if right is None:
        return left
    n = p * p
    x1, y1 = left
    x2, y2 = right
    if left == right:
        denominator = 2 * y1 % n
        numerator = 3 * x1 * x1 + a
    else:
        denominator = (x2 - x1) % n
        numerator = y2 - y1
    if denominator % p == 0:
        raise AssertionError("reference affine path met a nonunit")
    slope = numerator * pow(denominator, -1, n) % n
    x3 = (slope * slope - x1 - x2) % n
    y3 = (slope * (x1 - x3) - y1) % n
    if (y3*y3 - x3*x3*x3 - a*x3 - b) % n:
        raise AssertionError("reference affine addition left curve")
    return x3, y3


def affine_mul(scalar: int, point, p: int, a: int, b: int):
    out = None
    addend = point
    while scalar:
        if scalar & 1:
            out = affine_add(out, addend, p, a, b)
        scalar >>= 1
        if scalar:
            addend = affine_add(addend, addend, p, a, b)
    return out


def tau(point, u: int, split: int, p: int, a: int, b: int, r: int) -> int:
    lifted = hensel(point, u, p, a, b)
    left = affine_mul(split, lifted, p, a, b)
    right = affine_mul(r - split, lifted, p, a, b)
    n = p * p
    x1, y1 = left
    x2, y2 = right
    h = (x2 - x1) % n
    i = (2 * h)**2 % n
    j = h * i % n
    rr = 2 * (y2 - y1) % n
    v = x1 * i % n
    x3 = (rr*rr - j - 2*v) % n
    y3 = (rr*(v-x3) - 2*y1*j) % n
    z3 = 2 * h % n
    if (y3*y3 - x3*x3*x3 - a*x3*pow(z3, 4, n) - b*pow(z3, 6, n)) % n:
        raise AssertionError("reference mixed sum left curve")
    if z3 % p or y3 % p == 0:
        raise AssertionError("reference kernel representation invalid")
    parameter = -x3 * z3 * pow(y3, -1, n) % n
    if parameter % p:
        raise AssertionError("reference formal parameter not divisible by p")
    return parameter // p % p


def section_values(point, p: int, a: int, b: int, r: int):
    half = (r - 1) // 2
    third = max(1, r // 3)
    tau0 = tau(point, 0, half, p, a, b, r)
    if tau0 != tau(point, 0, third, p, a, b, r):
        raise AssertionError("split mismatch")
    tau1 = tau(point, 1, half, p, a, b, r)
    slope = (tau1 - tau0) % p
    if slope == 0:
        raise AssertionError("zero section slope")
    torsion_u = -tau0 * pow(slope, -1, p) % p
    torsion_tau = tau(point, torsion_u, half, p, a, b, r)
    if torsion_tau:
        raise AssertionError("torsion correction mismatch")
    return {
        "tau": tau0,
        "tau_u1": tau1,
        "section_slope": slope,
        "torsion_u": torsion_u,
        "torsion_tau": torsion_tau,
    }


def degree_profile(values, prime: int):
    row = [value % prime for value in values]
    first = [row[0]]
    operations = 0
    degree = len(row) - 1
    for order in range(1, len(row)):
        row = [(row[i+1] - row[i]) % prime for i in range(len(row)-1)]
        operations += len(row)
        first.append(row[0])
        if all(value == 0 for value in row):
            degree = order - 1
            break
    return degree, first[:degree+1], operations


def newton(first, scalar: int, prime: int):
    total = 0
    choose = 1
    for index, coefficient in enumerate(first):
        if index:
            choose = choose * (scalar-index) * pow(index, -1, prime) % prime
        total = (total + coefficient * choose) % prime
    return total


def summarize(values, r: int, gate: int):
    degree, first, operations = degree_profile(values, r)
    counts = Counter(values)
    prefix = first[:gate+1]
    return {
        "degree": degree,
        "degree_gate": gate,
        "gate_passed": degree <= gate,
        "interpolation_subtractions": operations,
        "newton_prefix": prefix,
        "prefix_matches": sum(newton(prefix, k, r) == value % r
                              for k, value in enumerate(values, start=1)),
        "targets": len(values),
        "distinct_outputs": len(counts),
        "maximum_collision_bucket": max(counts.values()),
        "word_sha256": hashlib.sha256(json.dumps(list(values), separators=(",", ":")).encode()).hexdigest(),
    }


def verify(path: Path) -> dict:
    payload = load_payload(path)
    raw_sha = hashlib.sha256(payload).hexdigest()
    if raw_sha != EXPECTED_RESULT_SHA256:
        raise AssertionError(f"result SHA mismatch: {raw_sha}")
    result = json.loads(payload)
    science_sha = scientific_payload_sha256(result)
    if science_sha != EXPECTED_SCIENTIFIC_SHA256 or result["scientific_payload_sha256"] != science_sha:
        raise AssertionError(f"scientific SHA mismatch: {science_sha}")

    verified_targets = 0
    degrees = []
    canonical = {}
    for curve in result["curves"]:
        p = curve["parameters"]["p"]
        a = curve["parameters"]["a"]
        b = curve["parameters"]["b"]
        r = curve["parameters"]["r"]
        gate = math.ceil(math.log2(r))**2
        for row in curve["generators"]:
            generator = tuple(row["generator"])
            points = orbit(generator, p, a, r)
            values = []
            for scalar, (point, record) in enumerate(zip(points[1:], row["target_records"]), start=1):
                if record["scalar"] != scalar or record["point"] != list(point):
                    raise AssertionError("target identity mismatch")
                recomputed = section_values(point, p, a, b, r)
                for key, value in recomputed.items():
                    if record[key] != value:
                        raise AssertionError(f"target field mismatch: {key}")
                values.append(recomputed["tau"])
                verified_targets += 1
            if values != row["word"]:
                raise AssertionError("word mismatch")
            summary = summarize(values, r, gate)
            if summary != row["interpolation"]:
                raise AssertionError("interpolation summary mismatch")
            if summary["degree"] != r - 2:
                raise AssertionError("degree is not maximum")
            degrees.append(summary["degree"])
            if row["generator_multiplier"] == 1:
                canonical[curve["curve"]] = (values, points, (p, a, b, r))

    control_count = 0
    for name, controls in result["matched_controls"].items():
        base_values, points, (p, a, b, r) = canonical[name]
        gate = math.ceil(math.log2(r))**2
        for stored in controls["random_sections"]:
            replicate = stored["replicate"]
            word = []
            for scalar, point in enumerate(points[1:], start=1):
                u = seed("H110", name, "section", replicate, scalar, point[0], point[1]) % p
                word.append(tau(point, u, (r-1)//2, p, a, b, r))
            expected = {"replicate": replicate, **summarize(word, r, gate)}
            if expected != stored:
                raise AssertionError("random-section control mismatch")
            control_count += 1
        for stored in controls["matched_permutations"]:
            replicate = stored["replicate"]
            word = list(base_values)
            random.Random(seed("H110", name, "permutation", replicate)).shuffle(word)
            expected = {"replicate": replicate, **summarize(word, r, gate)}
            if expected != stored:
                raise AssertionError("permutation control mismatch")
            control_count += 1

    for name, stored in result["coordinate_isomorphism_controls"].items():
        _, _, (p, a, b, r) = canonical[name]
        lam = stored["lambda"]
        aa = a * pow(lam, 4, p) % p
        bb = b * pow(lam, 6, p) % p
        original_generator = next(tuple(c["canonical_generator"]) for c in result["curves"] if c["curve"] == name)
        generator = (original_generator[0]*pow(lam, 2, p) % p,
                     original_generator[1]*pow(lam, 3, p) % p)
        points = orbit(generator, p, aa, r)
        word = [section_values(point, p, aa, bb, r)["tau"] for point in points[1:]]
        if summarize(word, r, math.ceil(math.log2(r))**2) != stored["interpolation"]:
            raise AssertionError("coordinate-isomorphism control mismatch")

    if verified_targets != 9096 or control_count != 32 or len(degrees) != 28:
        raise AssertionError("frozen workload count mismatch")
    if result["summary"]["rows_passing_degree_gate"] != 0:
        raise AssertionError("decoder gate unexpectedly opened")
    return {
        "result_sha256": raw_sha,
        "scientific_payload_sha256": science_sha,
        "target_rows_verified": verified_targets,
        "candidate_rows_replayed": len(degrees),
        "matched_controls_replayed": control_count,
        "degree_minimum": min(degrees),
        "degree_maximum": max(degrees),
        "rows_passing_degree_gate": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.artifact), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
