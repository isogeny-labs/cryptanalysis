#!/usr/bin/env python3
"""CT318: fail-closed composition of CT315 cost and CT317 source-group audit.

The measured wall costs, process executions, source identity, and signatures
remain unverified. Self-tests fabricate all clocks, receipts, and process IDs.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import tempfile

import ct315_complete_cold_panel as cost
import ct317_group_replay as group

SCHEMA = "ct318-joint-source-admission/v1"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def audit(panel_raw, witness_raw, raw_root):
    """Never admit a ratio unless *both* unchanged upstream gates pass."""
    panel = cost.strict_json(panel_raw)
    witness = group.strict(witness_raw)
    costs = cost.audit(panel)
    replay = group.audit(panel, witness, Path(raw_root))
    if costs["cold_processes"] != replay["target_group_equations_replayed"]:
        raise ValueError("CT318: cost/group population disagreement")
    return {
        "schema": SCHEMA,
        "raw_panel_sha256": sha(panel_raw),
        "raw_witness_sha256": sha(witness_raw),
        "complete_cold_cost_source_gate": True,
        "source_group_replay_source_gate": True,
        "runs_bound_by_both_gates": costs["cold_processes"],
        "provisional_best_baseline_over_candidate_exact":
            costs["best_baseline_over_candidate_exact"],
        "descriptive_block_bootstrap_ratio_95":
            costs["descriptive_block_bootstrap_ratio_95"],
        "execution_independently_verified": False,
        "complete_cost_independently_reproduced": False,
        "qualifies_as_signed_speedup": False,
        "actual_native_jacobian_executions_by_this_checker": 0,
        "pcc": "unverified",
    }


def _encoded(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":")).encode() + b"\n"


def _fixture(root, candidate_ns):
    """Entirely synthetic clocks/receipts, genuine independent toy Q=[2]P."""
    witness = {
        "schema": group.SCHEMA, "curve_id": "synthetic-F97",
        "p": 97, "a": 2, "b": 3, "generator": [3, 6],
        "subgroup_prime": 5,
        "targets": [{"target_id": "toy-Q2", "Q": [80, 10]}],
    }
    panel = {"schema": cost.SCHEMA, "memory_cap_kib": 4096, "runs": []}
    walls = (1200, candidate_ns, candidate_ns, 1200, 900, 950, 925)
    for b in range(4):
        for pos, (arm, wall) in enumerate(zip(cost.ARMS, walls)):
            rid = "toy-%d-%d" % (b, pos)
            stdout = _encoded({"schema": "ct317-solver-scalar/v1", "scalar": 2})
            receipt = _encoded({"synthetic": True, "run_id": rid})
            (root / (rid + ".stdout")).write_bytes(stdout)
            (root / (rid + ".receipt.json")).write_bytes(receipt)
            phases = dict.fromkeys(cost.PHASES, 0)
            phases.update(setup=50, recovery=50, verification=50)
            panel["runs"].append({
                "block": b, "position": pos, "run_id": rid, "arm": arm,
                "target_id": "toy-Q2", "curve_id": witness["curve_id"],
                "subgroup_order": 5, "expected_scalar": 2, "result_scalar": 2,
                "host": "synthetic-host", "cpu_affinity": [0],
                "source_sha256": sha(("src-" + arm).encode()),
                "binary_sha256": sha(("bin-" + arm).encode()),
                "argv_sha256": sha(("argv-" + arm).encode()),
                "stdout_sha256": sha(stdout), "receipt_sha256": sha(receipt),
                "phases_ns": phases, "external_wall_ns": wall,
                "peak_rss_kib": 1000, "cold": True, "pcc": "unverified",
            })
    return panel, witness


def self_test():
    refused = 0
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        panel, witness = _fixture(root, 700)
        pos = audit(_encoded(panel), _encoded(witness), root)
        ratio = pos["provisional_best_baseline_over_candidate_exact"]
        if ratio["numerator"] <= ratio["denominator"] or pos["qualifies_as_signed_speedup"]:
            raise AssertionError("CT318: positive synthetic comparison not descriptive")
        neg_panel, neg_witness = _fixture(root, 1700)
        neg = audit(_encoded(neg_panel), _encoded(neg_witness), root)
        nratio = neg["provisional_best_baseline_over_candidate_exact"]
        if nratio["numerator"] >= nratio["denominator"]:
            raise AssertionError("CT318: synthetic negative not preserved")

        # Each attack is known to pass at least one independent upstream gate.
        attacks = (
            lambda p, w: w["targets"][0].update(Q=[3, 6]),
            lambda p, w: p["runs"][0]["phases_ns"].update(verification=0),
            lambda p, w: p["runs"][0].update(stdout_sha256="0" * 64),
            lambda p, w: p["runs"][0].update(expected_scalar=3, result_scalar=3),
            lambda p, w: p["runs"][0].update(peak_rss_kib=None),
            lambda p, w: p["runs"][0].update(target_id="other-Q"),
        )
        for i, attack in enumerate(attacks):
            p, w = copy.deepcopy(panel), copy.deepcopy(witness)
            attack(p, w)
            try:
                audit(_encoded(p), _encoded(w), root)
            except (ValueError, OSError):
                refused += 1
            else:
                raise AssertionError("CT318: accepted corrupt source mock " + str(i))
        rid = panel["runs"][0]["run_id"]
        rp = root / (rid + ".receipt.json")
        original = rp.read_bytes()
        rp.unlink()
        try:
            audit(_encoded(panel), _encoded(witness), root)
        except (ValueError, OSError):
            refused += 1
        else:
            raise AssertionError("CT318: accepted absent raw receipt")
        finally:
            rp.write_bytes(original)
        raw = _encoded(panel)
        # Duplicate top-level key; valid data object must still be rejected.
        duplicated = raw.replace(b'{"memory_cap_kib":', b'{"memory_cap_kib":4096,"memory_cap_kib":', 1)
        if duplicated == raw:
            raise AssertionError("CT318: duplicate-key construction failed")
        try:
            audit(duplicated, _encoded(witness), root)
        except (ValueError, OSError):
            refused += 1
        else:
            raise AssertionError("CT318: accepted duplicate-key raw JSON")
        if refused != 8:
            raise AssertionError("CT318: lost sabotage coverage")
    return {
        "schema": "ct318-source-only-selftest/v1",
        "synthetic_positive_and_negative": 2,
        "independent_cross_gate_attacks_refused": refused,
        "synthetic_source_group_replays": 56,
        "original_native_jacobian_executions": 0,
        "pcc": "unverified",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--panel", type=Path)
    parser.add_argument("--witness", type=Path)
    parser.add_argument("--raw-root", type=Path)
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True))
        return
    if args.witness is None or args.raw_root is None:
        raise ValueError("CT318: --witness and --raw-root required")
    print(json.dumps(audit(args.panel.read_bytes(),
                           args.witness.read_bytes(), args.raw_root), sort_keys=True))


if __name__ == "__main__":
    main()
