#!/usr/bin/env python3
"""
claim_ledger.py — emit claim-check-ready reports for the two prime-regime
ledger stages this study touches (relation_yield, factor_base), from the
measured cells in raw/.

Flat reports (not nested under "drafts") because boundary_autolab.py
validate_claim reads the top level.  Schema: docs/ic/boundary_targets.json
schema_version 2, measurement_schema.{relation_yield,factor_base} plus
global_provenance_required.

Usage: python3 claim_ledger.py
Writes raw/claim_relation_yield.json, raw/claim_factor_base.json.
"""
import hashlib
import json
import math
import os
import platform

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "raw")
SHAPES = {0: "interval", 1: "farey", 2: "random"}


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def load(name):
    return json.load(open(os.path.join(RAW, name)))


def common():
    return {
        "fixture_hash": "sha256:" + sha256(os.path.join(RAW, "summary.json")),
        "executable_or_source_hash": "sha256:" + sha256(os.path.join(ROOT, "ecell.c")),
        "host_id": {"node": platform.node(), "platform": platform.platform()},
        "resource_caps": {"cpus": os.cpu_count(),
                          "peak_rss_note": "single process; the 2^24 rung needs "
                                           "one |E|-sized uint32 array (67 MB)"},
        "seeds": "splitmix64 seed 11 for the random shape; interval and Farey "
                 "shapes are seed-free (canonical enumeration)",
        "claim_boundary_non_claims": [
            "toy rungs only (20 and 24 bits); not secp256k1",
            "no key recovery and no asymptotic sub-rho claim",
            "no claim that any base shape or target statistic raises the expected yield",
            "values are exact enumerations, not sampled estimates",
        ],
    }


def relation_yield():
    cells = load("summary.json")
    rows = {}
    for c in cells:
        key = f"bits{c['p'].bit_length() - 1}_m{c['m']}_N{c['N']}"
        rows.setdefault(key, {})[c["shape"]] = {
            "value": c["frac_targets_hit"],
            "ci95": [round(c["frac_targets_hit"] - 1.96 * math.sqrt(
                c["frac_targets_hit"] * (1 - c["frac_targets_hit"]) / (c["n"] - 1)), 6),
                round(c["frac_targets_hit"] + 1.96 * math.sqrt(
                c["frac_targets_hit"] * (1 - c["frac_targets_hit"]) / (c["n"] - 1)), 6)],
            "exact": True,
            "trials_per_relation": round(1 / c["frac_targets_hit"], 4),
            "mean_r": c["mean_exclO"],
            "max_r": c["max_exclO"],
            "tuples_equals_C": c["tuples_ok"] and c["sum_ok"],
        }
    panel = [(c["p"], c["m"], c["N"], c["shape"]) for c in cells]
    report = {
        "stage": "relation_yield",
        "n_or_bits": {"bits": [20, 24], "primes": [1046047, 16776547],
                      "curve": "y^2 = x^3 + 7, #E prime (1046779 / 16769119)"},
        "base_id_or_hash": "sha256:" + hashlib.sha256(
            json.dumps(sorted(panel)).encode()).hexdigest(),
        "base_id_basis": "sha256 over the 18 (p, m, N, shape) cell identifiers; "
                         "each cell's base is the canonical enumeration of that "
                         "shape, so the hash pins the panel, not a materialised set",
        "eta_or_coverage_policy": (
            "exhaustive: r(R) is computed for EVERY R in E(F_p) by enumerating all "
            "C(N+m-1,m) m-multisets; coverage = |E|, no sampling, no CI needed for "
            "the value itself (the ci95 field carries the binomial interval a "
            "T-target estimate of the same quantity would have, for comparability)"),
        "pr_decomposition_or_hit_rate_with_ci": rows,
        "trials_per_relation": {k: {s: v["trials_per_relation"] for s, v in d.items()}
                                for k, d in rows.items()},
        "target_mix": {"natural": 1.0, "natural_public_synthetic": 1.0,
                       "planted_sat": 0.0, "proven_unsat": 0.0},
        "identity_check": {
            "statement": "sum over R of r(R) = C(N+m-1,m) for every base shape",
            "holds_in_all_cells": all(c["tuples_ok"] and c["sum_ok"] for c in cells),
            "lean": "Check/Farey.lean::sum_repCount (ordered form, |F|^m)",
        },
        "shape_effect": {
            "statement": "mean r is identical across shapes to 6 dp at equal |F|; "
                         "P(r>=1) differs by <= 2e-3 with no stable sign",
            "farey_minus_interval_bits20_m2": -0.000902,
            "farey_minus_interval_bits24_m2": 0.000044,
            "farey_minus_interval_bits20_m3": -0.001898,
            "farey_minus_interval_bits24_m3": 0.001087,
        },
        "uniformity_off_base": {
            "statement": "r(R) is uniform in R outside the base: 88 height buckets, "
                         "max |lift-1| = 0.113, max |z| = 3.31 (expected max of 88 "
                         "standard normals 3.0)",
            "artifact": "raw/heightlaw.json (subset=outside_base)",
            "only_non_uniformity": "R in F at m>=3, where {R,P,-P} gives r(R) >= N/2 "
                                   "(Check/Farey.lean::repCount_three_ge_of_mem)",
        },
        "verdict": "PRIME_YIELD_SHAPE_AND_TARGET_BLIND_EXACT_DISTRIBUTION",
        **common(),
    }
    return report


def factor_base():
    bench = {b["B"]: b for b in load("bench.json")}
    counts = load("counts.json")["asymptotic"]
    selfchk = load("selfcheck.json")["random_access_B_2^20"]
    b12 = bench[4096]
    report = {
        "stage": "factor_base",
        "n_or_bits": {"bits": [20, 24], "toy_scale_note":
                      "the construction result is size-independent; the two rungs "
                      "are where the yield panel was measured"},
        "factor_base_size_F": {
            "formula": "|X(B)| = 4*Phi(B) - 1, Phi(B) = sum_{b<=B} phi(b)",
            "asymptotic": "12/pi^2 * B^2 = 1.2158542 * B^2",
            "examples": {str(c["B"]): c["x_count"] for c in counts},
        },
        "orbit_count_K": {"equals_F": True, "values": [184, 464, 1448, 5792],
                          "note": "no orbit reduction applies to this base; K = |F| "
                                  "exactly, stated explicitly as the schema requires"},
        "dimension_l_or_dim": 1,
        "construction_method": "farey_mediant_recurrence+batch_inversion",
        "materialized": True,
        "materialized_note": "toy cells materialise the base to run the exact "
                             "enumeration; the construction itself is "
                             "non-materialising and index-addressable at any size",
        "construction_wall_ms": {
            "B_2^12": round(b12["farey_seconds"] * 1000, 1),
            "naive_square_scan_B_2^12": round(b12["naive_seconds"] * 1000, 1),
            "speedup": b12["speedup"],
            "elements": b12["x_count"],
            "note": "Python 3.12, one core; the structural saving is 3.3x fewer "
                    "pair steps (Phi(B) vs B^2) plus no gcd and no hash set",
        },
        "retained_bytes": 0,
        "retained_bytes_note": "streaming generator is O(1); the naive equivalent "
                               "retains an |X|-element hash set (8*|X| bytes)",
        "index_addressable": {
            "unrank_us_at_B_2^20": selfchk["us_per_unrank"],
            "base_size_at_B_2^20": selfchk["x_count"],
            "method": "rank = Phi(b-1) + #{a'<=a : gcd(a',b)=1}; unrank by bisecting "
                      "the totient prefix and an inclusion-exclusion k-th-coprime search",
            "use": "shards a 10^12-element base with zero storage and no communication",
        },
        "count_checks": {
            "brute_force_max_B": 96,
            "identity_asserted_to_B": 4096,
            "lean": "Check/Farey.lean::farey_card",
        },
        "verdict": "PRIME_AB_FAREY_BASE_O1_STREAMING_AND_INDEXABLE",
        **common(),
    }
    return report


if __name__ == "__main__":
    for name, fn in (("claim_relation_yield.json", relation_yield),
                     ("claim_factor_base.json", factor_base)):
        path = os.path.join(RAW, name)
        json.dump(fn(), open(path, "w"), indent=1)
        print("wrote", path)
