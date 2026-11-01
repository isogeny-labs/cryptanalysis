#!/usr/bin/env python3
"""Independent standard-library verifier for the H109 result artifact."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import random


EXPECTED_RESULT_SHA256 = "940123c44c6194b247fab3596a9ed2e331ee7e01b2fb8830fc7e8465e354993a"
EXPECTED_SCIENTIFIC_SHA256 = "3991b25d2a2ddac0ebb1d25370c8b110051a40acca64a6bda3dd3baba4191b69"


def load_payload(path: Path) -> bytes:
    raw = path.read_bytes()
    return gzip.decompress(raw) if path.suffix == ".gz" else raw


def scientific_payload_sha256(result: dict) -> str:
    def scrub(value):
        if isinstance(value, dict):
            return {
                key: scrub(item)
                for key, item in value.items()
                if not key.endswith("_ns")
                and "_ns_" not in key
                and key not in {"scientific_payload_sha256", "environment"}
            }
        if isinstance(value, list):
            return [scrub(item) for item in value]
        return value

    canonical = json.dumps(
        scrub(result), sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(canonical).hexdigest()


def phase_context(row: dict, prime: int) -> tuple[int, int, dict[int, int]]:
    character = row["character"]
    modulus = character["modulus"]
    root = character["phase_root"]
    table = {pow(root, exponent, prime): exponent for exponent in range(modulus)}
    if len(table) != modulus:
        raise AssertionError("invalid phase root order")
    return modulus, character["half_phase"], table


def phase(value: int, prime: int, modulus: int, table: dict[int, int]) -> int:
    if value % prime == 0:
        raise AssertionError("zero phase input")
    return table[pow(value, (prime - 1) // modulus, prime)]


def formula_search(features: list[list[int]], target: list[int], modulus: int) -> dict:
    best_matches = -1
    best = []
    exact = []
    candidates = 0
    for coefficients in itertools.product(range(modulus), repeat=5):
        candidates += 1
        matches = sum(
            sum(a * b for a, b in zip(coefficients, row)) % modulus == expected
            for row, expected in zip(features, target)
        )
        if matches > best_matches:
            best_matches, best = matches, [list(coefficients)]
        elif matches == best_matches:
            best.append(list(coefficients))
        if matches == len(target):
            exact.append(list(coefficients))
    return {
        "formula_candidates": candidates,
        "best_matches": best_matches,
        "best_coefficients": best,
        "exact_coefficients": exact,
        "exact_formula_count": len(exact),
    }


def deterministic_seed(*parts: object) -> int:
    payload = "|".join(map(str, parts)).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:16], "big")


def matched_phase_control(order: int, modulus: int, seed: int) -> list[int]:
    rng = random.Random(seed)
    bits = [0] * (order - 1)
    for scalar in range(1, (order + 1) // 2):
        bit = rng.randrange(2)
        bits[scalar - 1] = bit
        bits[order - scalar - 1] = bit ^ 1
    half = modulus // 2
    return [half * bit for bit in bits]


def verify(path: Path) -> dict:
    payload = load_payload(path)
    result_sha = hashlib.sha256(payload).hexdigest()
    if result_sha != EXPECTED_RESULT_SHA256:
        raise AssertionError(f"result SHA mismatch: {result_sha}")
    result = json.loads(payload)
    scientific_sha = scientific_payload_sha256(result)
    if scientific_sha != EXPECTED_SCIENTIFIC_SHA256:
        raise AssertionError(f"scientific SHA mismatch: {scientific_sha}")
    if result["scientific_payload_sha256"] != scientific_sha:
        raise AssertionError("embedded scientific SHA mismatch")

    feature_rows_by_curve = {}
    target_rows = 0
    formula_candidates = 0
    exact_rows = 0
    best_rates = []
    for curve_row in result["curves"]:
        p = curve_row["parameters"]["p"]
        r = curve_row["parameters"]["r"]
        for generator_row in curve_row["generators"]:
            modulus, half, table = phase_context(generator_row, p)
            features = []
            for record in generator_row["target_records"]:
                scalar, delta, minus, plus, y = record[:5]
                stored_phases = record[5:9]
                residue = record[9]
                if not all(value % p for value in (delta, minus, plus, y)):
                    raise AssertionError("zero oracle input")
                observed_residue = (
                    delta * delta + (r * r % p) * minus * plus
                ) % p
                if residue != 0 or observed_residue != residue:
                    raise AssertionError("local identity mismatch")
                observed_phases = [
                    phase(value, p, modulus, table)
                    for value in (delta, minus, plus, y)
                ]
                if observed_phases != stored_phases:
                    raise AssertionError("stored phase mismatch")
                features.append([1, *observed_phases])
                if scalar != len(features):
                    raise AssertionError("noncanonical scalar order")
            target = [half if scalar & 1 else 0 for scalar in range(1, r)]
            observed = formula_search(features, target, modulus)
            stored = generator_row["search"]
            for key in (
                "formula_candidates",
                "best_matches",
                "best_coefficients",
                "exact_coefficients",
                "exact_formula_count",
            ):
                if observed[key] != stored[key]:
                    raise AssertionError(f"formula search mismatch: {key}")
            if generator_row["generator_multiplier"] == 1:
                feature_rows_by_curve[curve_row["curve"]] = features
            target_rows += len(features)
            formula_candidates += observed["formula_candidates"]
            exact_rows += int(bool(observed["exact_formula_count"]))
            best_rates.append(observed["best_matches"] / len(features))

    control_rows = 0
    for control in result["matched_controls"]:
        curve = next(row for row in result["curves"] if row["curve"] == control["curve"])
        r = curve["parameters"]["r"]
        features = feature_rows_by_curve[control["curve"]]
        modulus = control["character_modulus"]
        for stored in control["rows"]:
            seed = deterministic_seed(
                "H109",
                control["curve"],
                "symmetry-matched-phase-control",
                stored["replicate"],
            )
            if seed != stored["seed"]:
                raise AssertionError("control seed mismatch")
            target = matched_phase_control(r, modulus, seed)
            if hashlib.sha256(bytes(target)).hexdigest() != stored["label_sha256"]:
                raise AssertionError("control label hash mismatch")
            observed = formula_search(features, target, modulus)
            for key in (
                "formula_candidates",
                "best_matches",
                "best_coefficients",
                "exact_formula_count",
            ):
                if observed[key] != stored[key]:
                    raise AssertionError(f"control search mismatch: {key}")
            control_rows += 1

    summary = result["summary"]
    if target_rows != 9096 or summary["targets"] != target_rows:
        raise AssertionError("target count mismatch")
    if formula_candidates != 8832 or summary["formula_candidates_total"] != formula_candidates:
        raise AssertionError("formula count mismatch")
    if exact_rows != 0 or summary["exact_rows"] != 0:
        raise AssertionError("unexpected exact formula")
    if control_rows != 32 or summary["matched_control_replicates"] != control_rows:
        raise AssertionError("control count mismatch")
    if min(best_rates) != 0.5 or max(best_rates) != 0.6111111111111112:
        raise AssertionError("candidate best-rate range mismatch")
    return {
        "result_sha256": result_sha,
        "scientific_payload_sha256": scientific_sha,
        "target_rows_verified": target_rows,
        "formula_candidates_replayed": formula_candidates,
        "exact_rows": exact_rows,
        "matched_controls_replayed": control_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.artifact), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
