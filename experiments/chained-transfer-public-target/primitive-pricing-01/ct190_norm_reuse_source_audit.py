#!/usr/bin/env python3
"""CT190: fail-closed source provenance audit of the *optimized* CT175/CT189 route.

Static repository contract only. Does not authenticate a compiled executable,
measure native arithmetic, or certify a complete ECDLP speedup. [pcc:unverified]
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
BASE = "experiments/chained-transfer-public-target/"
PRICE = BASE + "primitive-pricing-01/"
FILES = {
    "old": BASE + "fixed-jacobian-chain-evaluator-01/src/lib.rs",
    "reuse": BASE + "fixed-jacobian-chain-evaluator-02/derived/lib.rs",
    "cargo": PRICE + "ct172-replay/Cargo.toml",
    "rust": PRICE + "ct172-replay/src/main.rs",
    "collector": PRICE + "ct176_cold_process_collector.py",
    "reader": PRICE + "ct179_panel_adjudicator.py",
    "crossover": PRICE + "ct189_native_physical_crossover_panel.py",
    "fixture": BASE + "evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json",
}
PINNED_BLOBS = {
    "old": "8016634385d76207b23a3eb3a4dae9b0366ac68d",
    "reuse": "b80eb91a39ae1e87f0fcde95e52ea3d3634558bc",
    "fixture": "9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3",
}
ARMS = ("direct_composite", "strongest_retained_lift_chain",
        "literal_sequential_Jacobian_maps")
COUNTS = {
    "direct_composite": (1, 0, 1),
    "strongest_retained_lift_chain": (0, 2, 1),
    "literal_sequential_Jacobian_maps": (0, 2, 2),
}


def require(condition, message):
    if not condition:
        raise ValueError("CT190 source refusal: " + message)


def git_blob(contents):
    return hashlib.sha1(b"blob " + str(len(contents)).encode("ascii") +
                        b"\x00" + contents).hexdigest()


def load_sources(root=ROOT):
    return {name: (root / path).read_bytes() for name, path in FILES.items()}


def fields(code):
    match = re.search(r"pub struct Calls\s*\{([^}]*)\}", code)
    require(match is not None, "missing Rust Calls struct")
    names = re.findall(r"pub ([a-z0-9_]+): u64,", match.group(1))
    require(len(names) == len(set(names)), "duplicate Rust counter")
    return set(names)


def audit(sources, *, enforce_pins=True):
    require(set(sources) == set(FILES), "missing/unexpected input file")
    if enforce_pins:
        for key, digest in PINNED_BLOBS.items():
            require(git_blob(sources[key]) == digest, key + " Git blob changed")
    # The original (not optimized) runtime has TWENTY counters; the optimized
    # derivative has TWENTY-ONE including transported_norm_doubling.
    old = sources["old"].decode("utf-8")
    reuse = sources["reuse"].decode("utf-8")
    orig_fields, new_fields = fields(old), fields(reuse)
    require(len(orig_fields) == 20, "original counter count is not 20")
    require(len(new_fields) == 21, "optimized counter count is not 21")
    require(new_fields - orig_fields == {"transported_norm_doubling"} and
            orig_fields <= new_fields, "not exactly one optimized doubling counter")

    point_start = reuse.find("    fn norm_point(")
    transfer_start = reuse.find("    pub fn transfer_entry(", point_start)
    require(point_start >= 0 and transfer_start > point_start,
            "actual norm-point helper is missing")
    norm = reuse[point_start:transfer_start]
    require("self.bump(|c| c.transported_norm_doubling += 1);" in norm,
            "real norm call must bump true doubling counter")
    require("descend_point(curve::pmul(&target.f, &target.curve, &point, 2))" in norm,
            "real norm path must use pmul(2) AND descend_point")
    require("let target = &self.geometry.models[to].quadratic;" in norm,
            "real norm must use target quadratic curve")
    require(reuse.count("let norm = self.norm_point(to, point);") == 2,
            "direct and retained routes must call optimized norm point")
    require("self.transfer_entry(&self.transfer_entry(input, 1)?, to)" in reuse,
            "literal sequential must execute two optimized transfers")
    require("if ep(n.norm(&entry.class)?) != entry.norm {" in reuse,
            "independent final actual-Jacobian norm check removed")

    cargo = sources["cargo"].decode("utf-8")
    rust = sources["rust"].decode("utf-8")
    collector = sources["collector"].decode("utf-8")
    reader = sources["reader"].decode("utf-8")
    crossover = sources["crossover"].decode("utf-8")
    require('chained-n4-fixed-jacobian-chain-norm-reuse = {' in cargo and
            'path = "../../fixed-jacobian-chain-evaluator-02"' in cargo,
            "CT172 Cargo dependency is not norm-reuse evaluator")
    require("use chained_n4_fixed_jacobian_chain_norm_reuse::Runtime;" in rust,
            "CT172 Rust imports a different runtime")
    require('args[0] == "--cold-route"' in rust and
            'let native_sample = sample_route(&runtime, &packet, from, to, arm, row)?;' in rust and
            'actual_calls == row[arm]' in rust,
            "CT175 source does not cold-execute and validate selected optimized route")
    require('FIXTURE_GIT_BLOB = "' + PINNED_BLOBS["fixture"] + '"' in collector,
            "collector changed 48-record optimized fixture identity")
    require("counter_object(record.get(\"native_calls\"), row[arm], \"native_calls\")" in collector,
            "collector no longer checks full native counters")
    require("len(counts) == 21" in reader and "expected_calls = row[arm]" in reader,
            "reader no longer checks 21 optimized counters")
    require("sample = native.run_sample(binary, packet, physical_arm, rows[packet], allowance)" in crossover and
            "elapsed, rss = audit.valid_sample(sample, rows[packet], packet, physical_arm)" in crossover,
            "CT189 does not delegate real physical route and strict reader")

    # Frozen public fixture is the derivative, NOT the original 20-counter run.
    def strict_pairs(pairs):
        out = {}
        for k, v in pairs:
            require(k not in out, "duplicate fixture key " + k)
            out[k] = v
        return out
    fixture = json.loads(sources["fixture"], object_pairs_hook=strict_pairs)
    require(type(fixture) is dict and set(fixture) == {"all48", "scope"},
            "fixture top-level fields")
    rows = fixture["all48"]
    require(type(rows) is list and len(rows) == 48, "fixture must contain 48 rows")
    seen = set()
    for i, row in enumerate(rows):
        require(type(row) is dict and
                set(row) == {"from", "to", "sector", "scalar_OUTSIDE_runtime",
                             "input", "whole_outputs_equal", *ARMS},
                "wrong row keys at " + str(i))
        key = (row["from"], row["to"], row["sector"], row["scalar_OUTSIDE_runtime"])
        require(all(type(v) is int for v in key) and key not in seen,
                "duplicate or invalid cohort " + str(i))
        seen.add(key)
        require(type(row["input"]) is list and len(row["input"]) == 19 and
                type(row["whole_outputs_equal"]) is list and
                len(row["whole_outputs_equal"]) == 19,
                "noncanonical public packet at " + str(i))
        for arm in ARMS:
            calls = row[arm]
            require(type(calls) is dict and set(calls) == new_fields,
                    "counter names differ from optimized Rust at " + str(i))
            require(all(type(v) is int and v >= 0 for v in calls.values()),
                    "negative/noninteger counter at " + str(i))
            c169, c13, n2 = COUNTS[arm]
            require((calls["degree169_elliptic_evaluation"],
                     calls["degree13_elliptic_evaluation"],
                     calls["transported_norm_doubling"]) == (c169, c13, n2),
                    "wrong actual norm/map counts on packet " + str(i) + " arm " + arm)
    require(len(seen) == 48, "duplicate cohorts")

    return {
        "schema": "ct190-source-norm-reuse-provenance/v1",
        "standing": "[pcc:unverified]",
        "old_git_blob": git_blob(sources["old"]),
        "optimized_git_blob": git_blob(sources["reuse"]),
        "frozen_fixture_git_blob": git_blob(sources["fixture"]),
        "counter_fields_original": 20, "counter_fields_norm_reuse": 21,
        "transported_norm_doubling": "counts actual pmul(point,2)+descend_point calls",
        "observed_frozen_packets": 48,
        "verified_source_contract": True,
        "native_executable_source_attested": False,
        "native_compilation_or_timing_performed": False,
        "measured_n2_actual_or_d_padd": False,
        "complete_single_target_ecdlp_advantage_established": False,
        "scope": "static source and frozen-fixture audit, NOT physical runtime or signed PCC",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(audit(load_sources(args.root)), sort_keys=True))


if __name__ == "__main__":
    main()
