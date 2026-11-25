#!/usr/bin/env python3
"""CT325 independent retrospective CT324 public-panel RECORD audit.

No producer imports; no independent native execution, Jacobian transfer, optimized-rho
benchmark or PCC signature is asserted. Original artifact custody is SHA-bound.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import itertools
import json
import math
import statistics
from pathlib import Path

PANEL_SHA = "0ded77e0a6c955d27383b96d2aff128a680f32436328df199f385fd0ae2a5667"
CHALLENGE_SHA = "6b381ca3600137351b45f77f204a8e08c94ef2ab69d7c308d246cae7e69c8147"
ARMS = ("bsgs", "old", "new")
ROOT = {"schema", "public_challenge_sha256", "source_curve", "public_target_count",
        "native_children", "correct_public_logs", "statistics", "observations",
        "original_jacobian_executions", "strongest_optimized_rho",
        "complete_transfer_advantage", "independent_pcc", "pcc"}
ROW = {"affine_adds", "argv_sha256", "arm", "batch_waves", "binary_sha256",
       "block", "cpu_affinity", "field_inversions", "peak_rss_kib", "position",
       "stderr_sha256", "stdout_sha256", "target_id", "walk_steps", "wall_ns"}
SUMMARY = {"n", "median_external_wall_ns", "median_peak_rss_kib",
           "total_affine_adds", "total_field_inversions"}

def need(pred, reason):
    if not pred:
        raise ValueError("CT325: " + reason)

def integer(x):
    return type(x) is int

def digest(x):
    return type(x) is str and len(x) == 64 and all(c in "0123456789abcdef" for c in x)

def validate(data):
    need(type(data) is dict and set(data) == ROOT, "whole root schema")
    need(data["schema"] == "ct324-three-arm-native-cold/v1", "schema version")
    need(data["public_challenge_sha256"] == CHALLENGE_SHA, "challenge SHA")
    need(data["source_curve"] == "crypto-prime31-exact-ordinary-20261115", "curve")
    need(integer(data["public_target_count"]) and data["public_target_count"] == 4,
         "four distinct target population")
    for field, expected in (("native_children",24), ("correct_public_logs",24),
                            ("original_jacobian_executions",0)):
        need(integer(data[field]) and data[field] == expected, field)
    need(data["strongest_optimized_rho"] is False and
         data["complete_transfer_advantage"] is False and
         data["independent_pcc"] is False and data["pcc"] == "unverified",
         "cannot silently promote unverified standing")
    rows = data["observations"]
    need(type(rows) is list and len(rows) == 24, "24 original rows")
    binary = {}
    argv_by_target = {}
    signature_by_target = {}
    for i, r in enumerate(rows):
        need(type(r) is dict and set(r) == ROW, "row schema " + str(i))
        b, position = divmod(i, 6)
        need(integer(r["block"]) and r["block"] == b and
             integer(r["position"]) and r["position"] == position, "row location")
        order = (("bsgs", "old", "new", "new", "old", "bsgs") if b % 2 == 0
                 else ("new", "old", "bsgs", "bsgs", "old", "new"))
        arm = order[position]
        need(r["arm"] == arm, "original row arm/order")
        need(r["target_id"] == "ct321-%04d" % b, "four target IDs")
        need(type(r["cpu_affinity"]) is list and r["cpu_affinity"] == [0], "CPU")
        for k in ("argv_sha256", "binary_sha256", "stdout_sha256", "stderr_sha256"):
            need(digest(r[k]), "invalid digest in " + k)
        for k in ("wall_ns", "peak_rss_kib", "affine_adds", "field_inversions"):
            need(integer(r[k]) and r[k] > 0, "invalid " + k)
        need(r["field_inversions"] <= r["affine_adds"], "inversion count")
        need(arm not in binary or binary[arm] == r["binary_sha256"], "changed arm binary")
        binary[arm] = r["binary_sha256"]
        key = (arm, b)
        need(key not in argv_by_target or argv_by_target[key] == r["argv_sha256"],
             "unpaired argv")
        argv_by_target[key] = r["argv_sha256"]
        if arm == "bsgs":
            need(r["batch_waves"] is None and r["walk_steps"] is None, "BSGS walk fields")
        elif arm == "old":
            need(r["batch_waves"] is None and integer(r["walk_steps"]) and
                 r["walk_steps"] > 0, "old-rho walks")
        else:
            need(integer(r["batch_waves"]) and r["batch_waves"] > 0 and
                 integer(r["walk_steps"]) and r["walk_steps"] >= r["batch_waves"],
                 "new-rho batch fields")
        signature = (r["affine_adds"], r["field_inversions"],
                     r["walk_steps"], r["batch_waves"])
        need(key not in signature_by_target or signature_by_target[key] == signature,
             "same-Q repeated deterministic work is not another independent target")
        signature_by_target[key] = signature
    for arm in ARMS:
        need(len({argv_by_target[(arm, b)] for b in range(4)}) == 4,
             "reused target argv within arm")
    summaries = data["statistics"]
    need(type(summaries) is dict and set(summaries) == set(ARMS), "summary arms")
    for arm in ARMS:
        actual = summaries[arm]
        need(type(actual) is dict and set(actual) == SUMMARY, "summary schema " + arm)
        r = [v for v in rows if v["arm"] == arm]
        expected = {
            "n": len(r),
            "median_external_wall_ns": statistics.median(v["wall_ns"] for v in r),
            "median_peak_rss_kib": statistics.median(v["peak_rss_kib"] for v in r),
            "total_affine_adds": sum(v["affine_adds"] for v in r),
            "total_field_inversions": sum(v["field_inversions"] for v in r),
        }
        for k in SUMMARY:
            need(type(actual[k]) in (int,float) and math.isfinite(actual[k]) and
                 actual[k] == expected[k], "source summary incorrect " + arm + ":" + k)
        need(expected["n"] == 8, "two processes per target per arm")
    return rows

def geo(ratios):
    return math.exp(math.fsum(math.log(x) for x in ratios) / len(ratios))

def sensitivity(ratios):
    need(len(ratios) == 4 and all(math.isfinite(x) and x > 0 for x in ratios),
         "invalid target block ratios")
    draws = sorted(geo([ratios[i] for i in ids])
                   for ids in itertools.product(range(4),repeat=4))
    need(len(draws) == 256, "256 exact bootstrap draws")
    original = math.fsum(math.log(x) for x in ratios)
    signs = list(itertools.product((-1,1),repeat=4))
    p = sum(math.fsum(s*math.log(x) for s,x in zip(t,ratios)) >= original-1e-12
            for t in signs) / 16
    return {
        "geometric_mean_baseline_over_candidate": geo(ratios),
        "four_block_bootstrap_nearest_rank_95pct_exploratory": [draws[6],draws[249]],
        "one_sided_sign_flip_sensitivity_p_conditional": p,
        "number_of_target_blocks": 4,
        "number_of_bootstrap_resamples_enumerated": 256,
        "number_of_sign_flips_enumerated": 16,
    }

def audit(data):
    rows = validate(data)
    blocks, oldnew, bsgsnew = [], [], []
    for b in range(4):
        s = [r for r in rows if r["block"] == b]
        means = {arm: statistics.mean(r["wall_ns"] for r in s if r["arm"] == arm)
                 for arm in ARMS}
        a = means["old"]/means["new"]
        c = means["bsgs"]/means["new"]
        oldnew.append(a)
        bsgsnew.append(c)
        blocks.append({
            "target_id": "ct321-%04d" % b,
            "two_run_mean_wall_ns": means,
            "old_over_new": a,
            "bsgs_over_new": c,
            "old_walk_steps": next(r["walk_steps"] for r in s if r["arm"] == "old"),
            "new_walk_steps": next(r["walk_steps"] for r in s if r["arm"] == "new"),
        })
    return {
        "scope": "retrospective source-bound independent RECORD arithmetic; not native replay/PCC/transfer",
        "source_panel_sha256": PANEL_SHA,
        "source_artifact_sha256": "eb095b6d6eb29195ced78751fc6a220999c2765a6b49df9e1e9341e1ae6a56a9",
        "observations": 24,
        "independent_distinct_public_targets": 4,
        "per_target": blocks,
        "old_over_new_target_blocks": sensitivity(oldnew),
        "bsgs_over_new_target_blocks": sensitivity(bsgsnew),
        "ratio_of_unpaired_arm_medians_old_over_new_for_context_only":
            data["statistics"]["old"]["median_external_wall_ns"] /
            data["statistics"]["new"]["median_external_wall_ns"],
        "published_arm_totals_independently_recomputed": data["statistics"],
        "original_jacobian_executions": 0,
        "complete_transfer_advantage": False,
        "strongest_optimized_rho": False,
        "independent_signed_pcc": False,
        "standing": "[pcc:unverified]",
    }

def load(path):
    raw = path.read_bytes()
    need(len(raw) == 14435 and hashlib.sha256(raw).hexdigest() == PANEL_SHA,
         "whole actual original 14,435-byte panel exact SHA256")
    return json.loads(raw.decode("utf-8"),
                      parse_constant=lambda x: need(False, "nonfinite JSON"))

def controls(source):
    need(audit(source)["observations"] == 24, "untouched frozen positive")
    mutators = [
        lambda d: d["observations"].pop(),
        lambda d: d["observations"][0].__setitem__("position",1),
        lambda d: d["observations"][0].__setitem__("target_id","ct321-0001"),
        lambda d: d["observations"][0].__setitem__("wall_ns",-2),
        lambda d: d["observations"][1].__setitem__("peak_rss_kib",None),
        lambda d: d["statistics"]["new"].__setitem__("median_external_wall_ns",0),
        lambda d: d["observations"][0].__setitem__("binary_sha256","0"*64),
        lambda d: d["observations"][0].__setitem__("field_inversions",999999),
        lambda d: d["observations"][2].pop("batch_waves"),
        lambda d: d.__setitem__("complete_transfer_advantage",True),
        lambda d: d.__setitem__("public_challenge_sha256","0"*64),
        lambda d: d["observations"][5].__setitem__("argv_sha256","0"*64),
        lambda d: d["observations"][6].__setitem__("target_id","ct321-0000"),
        lambda d: d["observations"][1].__setitem__("walk_steps",2),
    ]
    for i, change in enumerate(mutators):
        test = copy.deepcopy(source)
        change(test)
        try:
            audit(test)
        except ValueError:
            continue
        raise AssertionError("forged row control accepted: " + str(i))
    return {"original_cases_passed":1, "semantic_mutations_rejected":len(mutators),
            "fresh_original_native_runs":0, "pcc":"unverified"}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--panel", type=Path, required=True)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    data = load(args.panel)
    result = controls(data) if args.self_test else audit(data)
    print(json.dumps(result,sort_keys=True,separators=(",",":")))

if __name__ == "__main__":
    main()
