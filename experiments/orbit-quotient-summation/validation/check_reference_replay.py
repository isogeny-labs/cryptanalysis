#!/usr/bin/env python3
"""Compare a full run.py replay with the compact, frozen reference summary."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def compact_case(case: dict) -> dict:
    model, m3 = case["model"], case["m3"]
    anf = m3["first_target_full_cube_anf"]
    out = {
        "valid_orbit_keys": model["valid_orbit_keys"],
        "subgroup_order": model["subgroup_order"],
        "frobenius_eigenvalue": model["frobenius_eigenvalue"],
        "m3_fixed_positive": [x["positive_key_tuples"] for x in m3["fixed_phase"]],
        "m3_orbit_positive": [x["positive_key_tuples"] for x in m3["phase_free"]],
        "m3_domain": m3["fixed_phase"][0]["domain_key_tuples"],
        "m3_first_target_anf": {
            "fixed": {k: anf["fixed_phase"][k] for k in ("degree", "monomials")},
            "orbit": {k: anf["phase_free"][k] for k in ("degree", "monomials")},
        },
    }
    for degree in m3["valid_domain_degree_tests"]:
        n = degree["degree"]
        out[f"degree{n}"] = {
            "rank": degree["evaluation_rank"],
            "domain": degree["domain_size"],
            "fixed_consistent": degree["consistent"][:8],
            "orbit_consistent": degree["consistent"][8:],
        }
    if "m4" in case:
        m4 = case["m4"]
        out.update({
            "m4_fixed_positive": [x["positive_key_tuples"] for x in m4["fixed_phase"]],
            "m4_orbit_positive": [x["positive_key_tuples"] for x in m4["phase_free"]],
            "m4_domain": m4["fixed_phase"][0]["domain_key_tuples"],
            "m4_orbit_witness_median": [x["witness_median"] for x in m4["phase_free"]],
        })
    return out


def compare(expected, actual, path="reference") -> list[str]:
    if isinstance(expected, dict) and isinstance(actual, dict):
        failures = []
        if expected.keys() != actual.keys():
            failures.append(f"{path}: keys differ: expected {sorted(expected)}, got {sorted(actual)}")
        for key in expected.keys() & actual.keys():
            failures += compare(expected[key], actual[key], f"{path}.{key}")
        return failures
    if isinstance(expected, list) and isinstance(actual, list):
        failures = []
        if len(expected) != len(actual):
            failures.append(f"{path}: lengths differ: expected {len(expected)}, got {len(actual)}")
        for i, (a, b) in enumerate(zip(expected, actual)):
            failures += compare(a, b, f"{path}[{i}]")
        return failures
    if (isinstance(expected, (float, int)) and not isinstance(expected, bool)
            and isinstance(actual, (float, int)) and not isinstance(actual, bool)):
        if expected == actual:
            return []
        if isinstance(expected, float) and isinstance(actual, float) and math.isclose(
            expected, actual, rel_tol=1e-13, abs_tol=1e-13
        ):
            return []
    elif type(expected) is type(actual) and expected == actual:
        return []
    return [f"{path}: expected {expected!r}, got {actual!r}"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("replay", type=Path)
    args = parser.parse_args()
    frozen = json.loads((HERE / "results/reference.json").read_text())
    replay = json.loads(args.replay.read_text())
    expected_models = ((13, 4, 5475), (19, 6, 112679))
    actual_models = tuple(
        (case["model"]["n"], case["model"]["s"], case["model"]["normal_generator"])
        for case in replay["cases"]
    )
    if actual_models != expected_models:
        print(f"model identities differ: expected {expected_models}, got {actual_models}")
        return 1
    actual = {
        "schema": replay["schema"],
        "seed": replay["seed"],
        "n13_s4_beta5475": compact_case(replay["cases"][0]),
        "n19_s6_beta112679": compact_case(replay["cases"][1]),
        "degree131_projection": {
            k: replay["degree131_projection"][k]
            for k in frozen["degree131_projection"]
        },
    }
    expected = {k: v for k, v in frozen.items() if k != "runtime"}
    failures = compare(expected, actual)
    for failure in failures:
        print(failure)
    if failures:
        return 1
    fields = len(actual["n13_s4_beta5475"]) + len(actual["n19_s6_beta112679"])
    print(f"PASS: frozen n=13/n=19 summary ({fields} named case fields), seed, schema, and degree-131 projection match")
    print("Numeric comparison: integers exact; equal int/float values accepted; float/float tolerance 1e-13. Other fields exact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
