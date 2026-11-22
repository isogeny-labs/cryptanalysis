#!/usr/bin/env python3
"""CT320: require independently checked, distinct source-curve Q across cold blocks.

Source-only conditional admission, NOT a native execution, trusted challenge
generator, unbiased sample, or signed speedup proof. [pcc:unverified]
"""
import argparse
import json
import tempfile
from pathlib import Path

import ct315_complete_cold_panel as cold
import ct317_group_replay as group
import ct319_receipt_cost_binding as receipt

SCHEMA = "ct320-distinct-source-target-cold-admission/v1"


def refuse(why):
    raise ValueError("CT320: " + why)


def audit(panel_raw, witness_raw, root, fixture):
    # Critical: no target-diversity assertion can replace receipt and equation checks.
    upstream = receipt.audit(panel_raw, witness_raw, root, fixture)
    panel = cold.strict_json(panel_raw)
    witness = group.strict(witness_raw)
    target_map = {x["target_id"]: tuple(x["Q"]) for x in witness["targets"]}
    blocks = []
    Q_to_id = {}
    target_ids = set()
    scalars = set()
    for b in range(len(panel["runs"]) // 7):
        runs = panel["runs"][7 * b: 7 * b + 7]
        tid = runs[0]["target_id"]
        scalar = runs[0]["result_scalar"]
        Q = target_map[tid]  # CT317 has already validated IDs and Q=[k]P.
        if Q in Q_to_id and Q_to_id[Q] != tid:
            refuse("different target IDs alias one elliptic-curve Q")
        Q_to_id[Q] = tid
        target_ids.add(tid)
        scalars.add(scalar)
        blocks.append({"block": b, "target_id": tid, "Q": list(Q),
                       "verified_scalar": scalar})
    if len(Q_to_id) < 4:
        refuse("fewer than four algebraically distinct matched public Q")
    if len(target_ids) != len(Q_to_id):
        refuse("target identity aliases a group element")
    return {
        **upstream,
        "schema": SCHEMA,
        "distinct_group_element_Q": len(Q_to_id),
        "distinct_recovered_scalars": len(scalars),
        "matched_seven_arm_blocks": len(blocks),
        "source_public_target_blocks": blocks,
        "distinct_source_Q_coverage_gate": True,
        "independent_blind_challenge_generation_verified": False,
        "unmeasured_cross_run_cache_ruled_out": False,
        "actual_native_jacobian_executions_by_this_checker": 0,
        "qualifies_as_signed_speedup": False,
        "pcc": "unverified",
    }


def make_fixture(root, candidate_ns, k_by_block, ids=None):
    """Toy source group arithmetic genuine; cost/receipts remain invented."""
    panel, witness, fixture = receipt._fixture(root, candidate_ns)
    if ids is None:
        ids = ["synthetic-Q" + str(k) for k in k_by_block]
    if len(k_by_block) != 4 or len(ids) != 4:
        raise AssertionError("toy test has four matched blocks")
    witness["targets"] = []
    for b, (k, tid) in enumerate(zip(k_by_block, ids)):
        Q = group.mul(k, (3, 6), 97, 2)
        if Q is None:
            raise AssertionError("zero toy Q is not an affine challenge")
        if not any(x["target_id"] == tid for x in witness["targets"]):
            witness["targets"].append({"target_id": tid, "Q": list(Q)})
        for row in panel["runs"][7*b:7*b+7]:
            row["target_id"] = tid
            row["expected_scalar"] = k
            row["result_scalar"] = k
            stdout = receipt.encoded({"schema":"ct317-solver-scalar/v1",
                                      "scalar": k})
            rid = row["run_id"]
            (root / (rid + ".stdout")).write_bytes(stdout)
            recpath = root / (rid + ".receipt.json")
            record = receipt.receipt_gate.strict_json(recpath.read_bytes())
            record["stdout_sha256"] = receipt.sha(stdout)
            record["stdout_bytes"] = len(stdout)
            newreceipt = receipt.encoded(record)
            recpath.write_bytes(newreceipt)
            row["stdout_sha256"] = receipt.sha(stdout)
            row["receipt_sha256"] = receipt.sha(newreceipt)
    return panel, witness, fixture


def self_test():
    refused = 0
    old_gate_false_admissions = 0
    with tempfile.TemporaryDirectory(prefix="ct320-source-mock-") as td:
        root = Path(td)
        for label, scalars, ids, should_accept in (
            ("distinct-positive", (1,2,3,4), None, True),
            ("single-Q", (2,2,2,2), None, False),
            ("two-Q", (1,2,1,2), None, False),
            ("aliased-Q", (1,2,3,3), ("q1","q2","q3","q4"), False),
        ):
            child = root / label
            child.mkdir()
            panel, witness, fixture = make_fixture(child, 700, scalars, ids)
            p = receipt.encoded(panel)
            w = receipt.encoded(witness)
            # Show the preexisting gate really admitted the degenerate corpus.
            old = receipt.audit(p, w, child, fixture)
            if old["raw_receipts_bound_to_cold_wall_and_peak_rss"] != 28:
                raise AssertionError("upstream did not admit complete mock")
            if should_accept:
                accepted = audit(p, w, child, fixture)
                if (accepted["distinct_group_element_Q"] != 4 or
                        accepted["matched_seven_arm_blocks"] != 4):
                    raise AssertionError("missed four distinct Q")
            else:
                old_gate_false_admissions += 1
                try:
                    audit(p, w, child, fixture)
                except ValueError as exc:
                    if not str(exc).startswith("CT320:"):
                        raise
                    refused += 1
                else:
                    raise AssertionError("accepted " + label)
        child = root / "distinct-negative-cost"
        child.mkdir()
        panel, witness, fixture = make_fixture(child, 1700, (1,2,3,4))
        result = audit(receipt.encoded(panel), receipt.encoded(witness),
                       child, fixture)
        ratio = result["provisional_best_baseline_over_candidate_exact"]
        if (ratio["numerator"] >= ratio["denominator"] or
                result["qualifies_as_signed_speedup"]):
            raise AssertionError("negative cost arm should remain negative")
    if refused != 3 or old_gate_false_admissions != 3:
        raise AssertionError("lost repeated/aliased Q regression coverage")
    return {
        "schema": "ct320-source-only-selftest/v1",
        "genuine_toy_group_Q_checks": 5 * 28,
        "old_gate_degenerate_panels_accepted": old_gate_false_admissions,
        "new_gate_degenerate_panels_refused": refused,
        "toy_distinct_positive_negative_cost_panels": 2,
        "native_jacobian_executions": 0,
        "pcc": "unverified",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--panel", type=Path)
    parser.add_argument("--witness", type=Path)
    parser.add_argument("--raw-root", type=Path)
    parser.add_argument("--fixture", type=Path)
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True))
    else:
        if any(x is None for x in (args.witness, args.raw_root, args.fixture)):
            refuse("witness, raw-root and fixture are required")
        print(json.dumps(audit(args.panel.read_bytes(), args.witness.read_bytes(),
                              args.raw_root, args.fixture), sort_keys=True))


if __name__ == "__main__":
    main()
