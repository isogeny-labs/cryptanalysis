#!/usr/bin/env python3
"""
claim_draft.py — emit a schema-complete relation_yield draft for the prime
regime of docs/ic/boundary_targets.json (schema_version 2), from the cells
already measured here.

This file does NOT touch the `crypto` ledger: it writes a draft that can be
filed by whoever holds that scope.  Required fields per
`measurement_schema.relation_yield`:

    n_or_bits, base_id_or_hash, eta_or_coverage_policy,
    pr_decomposition_or_hit_rate_with_ci, trials_per_relation, target_mix
plus global provenance: fixture_hash, executable_or_source_hash, host_id,
resource_caps, seeds, claim_boundary_non_claims.
"""
import hashlib
import json
import os
import platform

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "raw")


def sha256_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    cells = json.load(open(os.path.join(RAW, "cells.json")))
    src = sha256_file(os.path.join(ROOT, "ecell.c"))
    fixture = sha256_file(os.path.join(RAW, "cells.json"))
    drafts = []
    for c in cells:
        n = c["n"]
        f = c["nz_exclO"] / (n - 1)
        ci = 1.96 * (f * (1 - f) / (n - 1)) ** 0.5
        shape = {0: "interval", 1: "farey", 2: "random"}[c["shape"]]
        basis = (f"p={c['p']};E=y^2=x^3+7;n={n};shape={shape};m={c['m']};"
                 f"N={c['N']};enum=canonical(cell order);points=both y signs")
        drafts.append({
            "regime": "prime",
            "stage": "relation_yield",
            "n_or_bits": {"bits": c["p"].bit_length(), "p": c["p"]},
            "base_id_or_hash": "sha256:" + hashlib.sha256(basis.encode()).hexdigest(),
            "base_id_basis": "recipe string (p, curve, shape, m, N, enumeration "
                             "rule); NOT a hash of the materialised dlog list",
            "factor_base_size_F": c["N"],
            "m_summands": c["m"],
            "eta_or_coverage_policy": (
                "exhaustive: every m-multiset of the base enumerated, r(R) "
                "accumulated over the whole group; coverage = |E| (no sampling)"),
            "pr_decomposition_or_hit_rate_with_ci": {
                "value": round(f, 6),
                "ci95": [round(f - ci, 6), round(f + ci, 6)],
                "definition": "#{R != O : r(R) >= 1} / (|E| - 1)",
                "note": "the value is exact for this base; the interval is the "
                        "binomial error a T-target estimate of the same quantity "
                        "would carry, reported so the field is comparable",
            },
            "trials_per_relation": round(1 / f, 4) if f else None,
            "target_mix": {"natural": 1.0, "planted_sat": 0.0, "proven_unsat": 0.0},
            "total_relations": c["sum_r_exclO"],
            "mean_r_exclO": round(c["sum_r_exclO"] / (n - 1), 6),
            "max_r_exclO": c["max_r_exclO"],
            "identity_check": {
                "sum_r_equals_C_N_plus_m_minus_1_m": c["sum_r"] == c["tuples"],
                "tuples": c["tuples"],
            },
        })
    out = {
        "fixture_hash": "sha256:" + fixture,
        "executable_or_source_hash": "sha256:" + src,
        "host_id": platform.node(),
        "resource_caps": {"cpus": os.cpu_count(), "memory_note": "single process, <2 GiB"},
        "seeds": "splitmix64 seed 11 for the random shape; structured shapes are "
                 "seed-free (canonical enumeration)",
        "claim_boundary_non_claims": [
            "toy rungs (20 and 24 bits), not secp256k1",
            "no key recovery, no asymptotic sub-rho claim",
            "no claim that any base shape raises the expected yield: the "
            "counting identity proves the opposite",
            "hit-rate is exact for one base per cell, not a sample mean",
        ],
        "drafts": drafts,
    }
    path = os.path.join(RAW, "claim_draft_relation_yield.json")
    json.dump(out, open(path, "w"), indent=1)
    print(f"wrote {path} ({len(drafts)} drafts)")
    for d in drafts:
        print(f"  p={d['n_or_bits']['p']} m={d['m_summands']} N={d['factor_base_size_F']:<5} "
              f"{d['base_id_or_hash'][:19]}  P(hit)={d['pr_decomposition_or_hit_rate_with_ci']['value']}")


if __name__ == "__main__":
    main()
