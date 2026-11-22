#!/usr/bin/env python3
"""CT315 source-only gate for a future measured, paired COMPLETE cold ECDLP panel.

This checker is not an independently signed execution/solve verifier.
It never declares a speedup. Self-tests fabricate all clocks and logs.
"""
import argparse
import copy
import hashlib
import json
import random
import re
from pathlib import Path

SCHEMA = "ct315-complete-cold-panel/v1"
ARMS = ("retained", "candidate", "candidate", "retained", "rho", "bsgs", "ic")
PHASES = ("setup", "transfer", "precomputation", "relation_collection",
          "linear_algebra", "individual_descent", "recovery",
          "verification", "teardown")
RUN_FIELDS = frozenset((
    "block", "position", "run_id", "arm", "target_id", "curve_id",
    "subgroup_order", "expected_scalar", "result_scalar",
    "host", "cpu_affinity", "source_sha256", "binary_sha256",
    "argv_sha256", "stdout_sha256", "receipt_sha256", "phases_ns",
    "external_wall_ns", "peak_rss_kib", "cold", "pcc"
))
HEX = re.compile(r"[0-9a-f]{64}\Z")


def refuse(why):
    raise ValueError("CT315: " + why)


def integer(v, name, minimum=0):
    if type(v) is not int or v < minimum:
        refuse(name + " must be a JSON integer >= " + str(minimum))
    return v


def strict_json(raw):
    def unique(pairs):
        o = {}
        for k, v in pairs:
            if k in o:
                refuse("duplicate JSON key " + k)
            o[k] = v
        return o

    def reject_constant(v):
        refuse("non-JSON constant " + v)

    return json.loads(raw, object_pairs_hook=unique, parse_constant=reject_constant)


def audit(panel):
    if type(panel) is not dict or set(panel) != {
        "schema", "memory_cap_kib", "runs"
    } or panel["schema"] != SCHEMA:
        refuse("wrong panel schema")
    cap = integer(panel["memory_cap_kib"], "memory cap", 1)
    runs = panel["runs"]
    if type(runs) is not list or len(runs) < 28 or len(runs) % 7:
        refuse("need >=4 complete seven-run blocks")
    run_ids = set()
    global_host = None
    per_arm_binaries = {}
    blocks = []
    for block in range(len(runs) // 7):
        group = runs[7 * block:7 * block + 7]
        common = None
        for pos, (row, arm) in enumerate(zip(group, ARMS)):
            if type(row) is not dict or set(row) != RUN_FIELDS:
                refuse("run fields differ at block/position %s/%s" % (block, pos))
            if (integer(row["block"], "block") != block or
                    integer(row["position"], "position") != pos or
                    row["arm"] != arm):
                refuse("ABBA order or baseline schedule changed")
            if (type(row["run_id"]) is not str or not row["run_id"] or
                    row["run_id"] in run_ids):
                refuse("missing or reused run id")
            run_ids.add(row["run_id"])
            if row["cold"] is not True or row["pcc"] != "unverified":
                refuse("warm run or ungrounded PCC standing")
            for name in ("target_id", "curve_id", "host"):
                if type(row[name]) is not str or not row[name]:
                    refuse("missing " + name)
            subgroup = integer(row["subgroup_order"], "subgroup order", 2)
            expected = integer(row["expected_scalar"], "expected scalar")
            recovered = integer(row["result_scalar"], "recovered scalar")
            if expected >= subgroup or recovered != expected:
                refuse("mismatched target or recovered logarithm")
            aff = row["cpu_affinity"]
            if (type(aff) is not list or not aff or
                    any(type(c) is not int or c < 0 for c in aff) or
                    aff != sorted(set(aff))):
                refuse("invalid CPU affinity")
            for name in ("source_sha256", "binary_sha256", "argv_sha256",
                         "stdout_sha256", "receipt_sha256"):
                if type(row[name]) is not str or HEX.fullmatch(row[name]) is None:
                    refuse("missing or invalid " + name)
            compiled = (row["source_sha256"], row["binary_sha256"],
                        row["argv_sha256"])
            if arm in per_arm_binaries and per_arm_binaries[arm] != compiled:
                refuse("arm changed executable/source/arguments between blocks")
            per_arm_binaries.setdefault(arm, compiled)
            phases = row["phases_ns"]
            if type(phases) is not dict or set(phases) != set(PHASES):
                refuse("incomplete cold cost phases")
            total = sum(integer(phases[k], "phase " + k) for k in PHASES)
            if (phases["verification"] == 0 or phases["recovery"] == 0 or
                    phases["setup"] == 0):
                refuse("setup/recovery/verification not charged")
            wall = integer(row["external_wall_ns"], "cold external wall", 1)
            if total > wall:
                refuse("nonoverlapping phase cost exceeds cold external wall")
            rss = integer(row["peak_rss_kib"], "measured peak RSS", 1)
            if rss > cap:
                refuse("run exceeded preregistered memory tier")
            key = (row["target_id"], row["curve_id"], subgroup, expected,
                   row["host"], tuple(aff))
            if common is not None and key != common:
                refuse("different public target/curve/scalar/host inside block")
            common = key
            if global_host is None:
                global_host = (row["host"], tuple(aff))
            if global_host != (row["host"], tuple(aff)):
                refuse("host/affinity drift between blocks")
        walls = [r["external_wall_ns"] for r in group]
        # Twice the true ns value, so paired A/B arithmetic stays integral.
        candidate_twice = walls[1] + walls[2]
        choices = {
            "retained": walls[0] + walls[3],
            "rho": 2 * walls[4],
            "bsgs": 2 * walls[5],
            "ic": 2 * walls[6],
        }
        best_arm = min(("retained", "rho", "bsgs", "ic"),
                       key=lambda a: (choices[a], a))
        best_twice = choices[best_arm]
        blocks.append({
            "block": block, "target_id": common[0],
            "best_baseline": best_arm,
            "best_baseline_twice_ns": best_twice,
            "candidate_twice_ns": candidate_twice,
            "baseline_faster": best_twice < candidate_twice,
            "candidate_faster": best_twice > candidate_twice,
            "tie": best_twice == candidate_twice,
            "retained_aa_ratio": [
                walls[0], walls[3]
            ],
            "candidate_aa_ratio": [walls[1], walls[2]],
            "peak_rss_kib_by_run": [r["peak_rss_kib"] for r in group],
        })
    numerator = sum(r["best_baseline_twice_ns"] for r in blocks)
    denominator = sum(r["candidate_twice_ns"] for r in blocks)
    if denominator <= 0:
        refuse("invalid aggregate candidate time")
    rng = random.Random(315)
    ratios = []
    for _ in range(2048):
        sample = [blocks[rng.randrange(len(blocks))] for _ in blocks]
        ratios.append(sum(r["best_baseline_twice_ns"] for r in sample) /
                      sum(r["candidate_twice_ns"] for r in sample))
    ratios.sort()
    return {
        "schema": "ct315-provisional-complete-cold-cost/v1",
        "blocks": blocks,
        "cold_processes": len(runs),
        "methods": list(dict.fromkeys(ARMS)),
        "charged_phases": list(PHASES),
        "complete_phase_and_rss_fields_present": True,
        "best_baseline_over_candidate_exact": {
            "numerator": numerator, "denominator": denominator
        },
        "descriptive_block_bootstrap_ratio_95": [
            ratios[51], ratios[1996]
        ],
        "bootstrap_assumptions_and_independence_unverified": True,
        "same_source_group_law_independently_checked": False,
        "execution_independently_verified": False,
        "complete_cost_independently_reproduced": False,
        "measured_original_model_executions_by_this_checker": 0,
        "qualifies_as_signed_speedup": False,
        "pcc": "unverified",
    }


def self_test():
    def fixture(candidate):
        rows = []
        sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
        walls = (1000, candidate, candidate, 1000, 850, 950, 900)
        for b in range(4):
            for pos, (arm, wall) in enumerate(zip(ARMS, walls)):
                rows.append({
                    "block": b, "position": pos,
                    "run_id": "synthetic-%d-%d" % (b, pos),
                    "arm": arm, "target_id": "synthetic-Q-%d" % b,
                    "curve_id": "synthetic-primefield", "subgroup_order": 101,
                    "expected_scalar": 17, "result_scalar": 17,
                    "host": "synthetic-host", "cpu_affinity": [0],
                    "source_sha256": sha("source-" + arm),
                    "binary_sha256": sha("binary-" + arm),
                    "argv_sha256": sha("argv-" + arm),
                    "stdout_sha256": sha("stdout-%d-%d" % (b, pos)),
                    "receipt_sha256": sha("receipt-%d-%d" % (b, pos)),
                    "phases_ns": dict.fromkeys(PHASES, 0) |
                        {"setup": 50, "recovery": 50, "verification": 50},
                    "external_wall_ns": wall, "peak_rss_kib": 1000,
                    "cold": True, "pcc": "unverified",
                })
        return {"schema": SCHEMA, "memory_cap_kib": 8192, "runs": rows}

    positive = audit(fixture(800))
    negative = audit(fixture(1200))
    frac = positive["best_baseline_over_candidate_exact"]
    if not (frac == {"numerator": 6800, "denominator": 6400} and
            negative["best_baseline_over_candidate_exact"]["numerator"] <
            negative["best_baseline_over_candidate_exact"]["denominator"]):
        raise AssertionError("positive/negative cold frontier checks incorrect")
    mutations = [
        lambda x: x["runs"][0]["phases_ns"].pop("linear_algebra"),
        lambda x: x["runs"][0].update(peak_rss_kib=None),
        lambda x: x["runs"][0].update(peak_rss_kib=0),
        lambda x: x["runs"].pop(),
        lambda x: x["runs"][0].update(arm="candidate"),
        lambda x: x["runs"][4].update(arm="retained"),
        lambda x: x["runs"][1].update(target_id="another public Q"),
        lambda x: x["runs"][1].update(result_scalar=13),
        lambda x: x["runs"][2].update(host="other host"),
        lambda x: x["runs"][7].update(run_id="synthetic-0-0"),
        lambda x: x["runs"][0].update(external_wall_ns=100),
        lambda x: x["runs"][0].update(source_sha256="not a SHA"),
        lambda x: x["runs"][7].update(binary_sha256="0"*64),
        lambda x: x["runs"][0].update(cold=False),
        lambda x: x["runs"][0].update(pcc="verified"),
        lambda x: x["runs"][0].update(cpu_affinity=[True]),
        lambda x: x["runs"][0].update(peak_rss_kib=8193),
    ]
    for n, change in enumerate(mutations):
        mutated = copy.deepcopy(fixture(800))
        change(mutated)
        try:
            audit(mutated)
        except ValueError:
            continue
        raise AssertionError("admitted synthetic mutation " + str(n))
    for raw in ('{"schema":"a","schema":"a"}', '{"v":NaN}'):
        try:
            strict_json(raw)
        except ValueError:
            continue
        raise AssertionError("malformed JSON accepted")
    return {"schema": "ct315-synthetic-only-selftest/v1",
            "positive_and_negative_controls": 2,
            "mutations_rejected": len(mutations) + 2,
            "synthetic_cold_processes": 28,
            "actual_native_executions": 0, "pcc": "unverified"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test", action="store_true")
    g.add_argument("--panel", type=Path)
    a = p.parse_args()
    if a.self_test:
        print(json.dumps(self_test(), sort_keys=True))
    else:
        print(json.dumps(audit(strict_json(a.panel.read_bytes())), sort_keys=True))


if __name__ == "__main__":
    main()
