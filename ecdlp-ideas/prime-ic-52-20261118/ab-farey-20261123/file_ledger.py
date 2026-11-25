#!/usr/bin/env python3
"""
file_ledger.py — write the two prime-regime ledger rows for the a/b study into
docs/ic/boundary_targets.json.

Updates (does not append) the existing `current` block of
regimes.prime.records.{relation_yield,factor_base}, pushes the displaced block
into `history`, and leaves everything else byte-identical.  Idempotent: run it
twice and the second run is a no-op.

Usage: python3 file_ledger.py /path/to/docs/ic/boundary_targets.json
"""
import json
import sys

PR = "isogeny-labs/cryptanalysis#1972"
BASE = "ecdlp-ideas/prime-ic-52-20261118/ab-farey-20261123"
RECORDED = "2026-11-24"

RELATION_YIELD = {
    "summary": (
        "Exact prime-regime yield curves at 20/24 bits with three equal-sized base "
        "shapes (interval, small-rational-height/Farey, random): r(R) is computed for "
        "every R in E(F_p) by enumerating all m-multisets, not sampled. The mean is "
        "C(N+m-1,m)/|E| in every cell to 6 dp (counting identity, Lean-proved), so base "
        "shape does not change expected yield; P(r>=1) differs by <= 2e-3 with no stable "
        "sign (a/b last in two of four rungs). Off the base, r(R) is uniform in the "
        "target: 88 rational-height buckets, max |z| 3.31 against an expected max of 3.0 "
        "for 88 normals. The only non-uniformity is R in F at m>=3, where {R,P,-P} forces "
        "r(R) >= N/2."),
    "metrics": {
        "n_or_bits": [20, 24],
        "m_summands": [2, 3],
        "primes": [1046047, 16776547],
        "curve": "y^2 = x^3 + 7, #E prime (1046779 / 16769119)",
        "base_shapes": ["interval", "small_rational_height_farey", "random_splitmix64_seed11"],
        "factor_base_sizes_F": [184, 464, 1448, 5792],
        "coverage": "exhaustive over |E|; exact, not a T-target estimate",
        "mean_r_by_cell": {
            "bits20_m2_N1448": 1.001504, "bits20_m3_N184": 1.008084,
            "bits24_m2_N5792": 1.000269, "bits24_m3_N464": 0.999299,
        },
        "mean_identical_across_shapes_to_6dp": True,
        "identity_sum_r_equals_C": True,
        "pr_hit_by_cell": {
            "bits20_m2": {"interval": 0.634175, "farey": 0.633273, "random": 0.633617},
            "bits20_m3": {"interval": 0.62872, "farey": 0.626822, "random": 0.627199},
            "bits24_m2": {"interval": 0.63241, "farey": 0.632454, "random": 0.632386},
            "bits24_m3": {"interval": 0.628659, "farey": 0.629746, "random": 0.629788},
        },
        "trials_per_relation_range": [1.5739, 1.5942],
        "farey_minus_interval_delta_pr": {"bits20_m2": -0.000902, "bits24_m2": 0.000044,
                                          "bits20_m3": -0.001898, "bits24_m3": 0.001087},
        "uniformity_off_base": {"height_buckets": 88, "max_abs_lift_minus_1": 0.113,
                                "max_abs_z": 3.31, "expected_max_z_88_normals": 3.0},
        "in_base_spike": {"condition": "R in F", "m": 3, "lower_bound": "|F| ordered",
                          "lean": "repCount_three_ge_of_mem"},
        "target_mix": {"natural_public_synthetic": 18, "planted_sat": 0, "proven_unsat": 0},
    },
    "verdict": "PRIME_YIELD_SHAPE_AND_TARGET_BLIND_EXACT_DISTRIBUTION",
}

RELATION_YIELD_NEXT = {
    "summary": (
        "A yield claim that survives the counting identity has to be a solver-cost "
        "claim, not a base or target-selection claim. Measure a sub-MITM decomposition "
        "oracle's cost per success at m=4 (the PKM margin), reported as a slope over "
        "p, and pair it with the per-attempt cost slope. No base redesign and no target "
        "statistic can move the expected yield."),
    "acceptance_gates": [
        "cost per relation measured as a slope over >= 3 rungs, not as a ratio",
        "the change declared as a solver change, not a base or target change",
        "target mix labelled",
        "no claim whose only content is re-selecting targets or resizing the base",
        "exact enumeration or an explicit CI; state which",
    ],
}

FACTOR_BASE = {
    "summary": (
        "Small-rational-height (Farey) base added to the prime table. "
        "X(B) = {a/b mod p : gcd(a,b)=1, 1<=|a|,|b|<=B, b!=0} is the Farey sequence of "
        "order B under x -> -x and x -> 1/x, so |X(B)| = 4*Phi(B) - 1 ~ 1.2159 B^2. It is "
        "enumerable by a mediant recurrence with no gcd test and no hash set (4.2-5.5x "
        "fewer operations than the square scan at B<=2^12, O(1) memory) and "
        "index-addressable: rank/unrank gives 58 us random access on a 10^12-element base "
        "at B=2^20 with zero storage. Not materialised at production scale; the toy cells "
        "materialise it only to run the exact yield enumeration."),
    "metrics": {
        "construction_methods": ["small_x", "zeta_orbit", "eisenstein_smooth",
                                 "small_rational_height_farey"],
        "construction_method": "farey_mediant_recurrence + batch_modular_inversion",
        "orbit_count_K": {"equals_F": True, "values": [184, 464, 1448, 5792],
                          "note": "no orbit reduction applies; K = |F| exactly"},
        "dimension_l_or_dim": 1,
        "materialized": True,
        "materialized_note": "toy cells only, to run the enumeration; the construction "
                             "itself is non-materialising",
        "construction_wall_ms": {"B_2^12": 9350.0, "naive_square_scan_B_2^12": 41250.0,
                                 "elements": 20400079, "speedup": 4.41,
                                 "platform": "Python 3.12, one core; the structural "
                                             "saving is 3.3x fewer pair steps "
                                             "(Phi(B) vs B^2) plus no gcd, no set"},
        "retained_bytes": 0,
        "retained_bytes_note": "streaming generator is O(1); the naive equivalent retains "
                               "an |X|-element hash set",
        "size_formula": "4*Phi(B) - 1, asymptotically 12/pi^2 * B^2 = 1.2158542 B^2",
        "size_examples": {"2^16": 5222059703, "2^18": 83553058575, "2^20": 1336846396983},
        "index_addressable": {"unrank_us_at_B_2^20": 58.32,
                              "method": "rank = Phi(b-1) + #{a'<=a : gcd(a',b)=1}; "
                                        "unrank via totient-prefix bisection + "
                                        "inclusion-exclusion k-th-coprime search"},
        "count_checks": {"brute_force_max_B": 96, "identity_asserted_to_B": 4096},
    },
    "verdict": "PRIME_AB_FAREY_BASE_O1_STREAMING_AND_INDEXABLE",
}

FACTOR_BASE_NEXT = {
    "summary": (
        "Use the index-addressable base to shard a relation sweep across hosts without "
        "transferring the base, and measure whether unrank stays sublinear to B=2^24. "
        "Base shape cannot change yield; this line is about setup and sharding only."),
    "acceptance_gates": [
        "unrank cost measured at >= 2 sizes",
        "count identity checked against brute force",
        "no materialisation at the tested size",
        "rank/unrank round-trip verified on the shard boundaries",
    ],
}


def evidence(extra):
    return [
        f"cross-repo: {PR} — {BASE}/{extra}",
        f"cross-repo: {PR} — {BASE}/lean-check/Check/Farey.lean",
        f"cross-repo: {PR} — {BASE}/raw/claim_relation_yield.json",
        f"cross-repo: {PR} — {BASE}/raw/claim_factor_base.json",
    ]


def main():
    path = sys.argv[1]
    doc = json.load(open(path))
    prime = doc["regimes"]["prime"]["records"]

    for stage, cur, nxt, ev_extra in (
        ("relation_yield", RELATION_YIELD, RELATION_YIELD_NEXT, "report.md"),
        ("factor_base", FACTOR_BASE, FACTOR_BASE_NEXT, "report.md"),
    ):
        rec = prime[stage]
        if rec["current"].get("verdict") == cur["verdict"]:
            print(f"{stage}: already filed, no change")
            continue
        rec["history"].append({"summary": rec["current"]["summary"],
                               "metrics": rec["current"].get("metrics", {}),
                               "recorded": "pre-" + RECORDED})
        rec["current"] = cur
        rec["next_target"] = nxt
        rec["status"] = "record"
        for item in evidence(ev_extra):
            if item not in rec["evidence"]:
                rec["evidence"].append(item)
        print(f"{stage}: filed {cur['verdict']}")

    doc["updated"] = RECORDED
    json.dump(doc, open(path, "w"), indent=2)
    print("updated ->", RECORDED)


if __name__ == "__main__":
    main()
