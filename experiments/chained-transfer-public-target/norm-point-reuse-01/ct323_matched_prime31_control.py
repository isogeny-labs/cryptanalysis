#!/usr/bin/env python3
"""CT323: matched fresh Q, same-CPU native BSGS/negation-DP-rho controls.

Live child process wall and RSS; unsigned, no transferred solver, no
independently authenticated blindness, and NOT strongest rho/IC. [pcc:unverified]
"""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import tempfile

import ct317_group_replay as group
import ct321_blind_challenge as blind
import ct322_live_prime31_bsgs as bsgs

RHO_KEYS = {"schema", "result_scalar", "walk_steps",
            "distinguished_entries", "restarts", "affine_adds",
            "field_inversions", "inside_ns", "original_jacobian_calls", "pcc"}

def refuse(msg):
    raise ValueError("CT323: " + msg)

def verify_rho(raw, Q, curve):
    ans = group.strict(raw)
    if (type(ans) is not dict or set(ans) != RHO_KEYS or
        ans["schema"] != "ct323-native-rho/v1" or
        ans["pcc"] != "unverified" or ans["original_jacobian_calls"] != 0):
        refuse("native rho schema")
    for field in ("result_scalar", "walk_steps", "distinguished_entries",
                  "restarts", "affine_adds", "field_inversions", "inside_ns"):
        if type(ans[field]) is not int or ans[field] < 1:
            refuse("missing positive rho counter " + field)
    n = curve["subgroup_prime"]
    m = __import__("math").isqrt(n-1) + 1
    if (ans["result_scalar"] >= n or
        ans["walk_steps"] > 64*m or
        ans["distinguished_entries"] > 65536 or
        ans["restarts"] > ans["walk_steps"]+1):
        refuse("native rho exceeded registered limits")
    if group.mul(ans["result_scalar"], tuple(curve["generator"]),
                 curve["p"], curve["a"]) != tuple(Q):
        refuse("independent rho Q=[k]G group check failed")
    return ans

def run_child(binary, fields, directory, mode, Q, curve):
    result = bsgs.native_child(binary, fields, directory)
    original = result.pop("native")
    ans = (bsgs.check_response(original, Q, curve) if mode == "bsgs"
           else verify_rho(original, Q, curve))
    return ans, result

def negative_controls(binary, mode, root):
    tests = [
        ("toy-ok", (97,2,3,5,3,6,80,10), True),
        ("toy-off-curve", (97,2,3,5,3,6,80,11), False),
        ("toy-composite-prime", (95,2,3,5,3,6,80,10), False),
        ("toy-composite-order", (97,2,3,4,3,6,80,10), False),
    ]
    toy = {"subgroup_prime":5, "p":97, "a":2, "generator":[3,6]}
    checked = 0
    for name, fields, positive in tests:
        wd = root / (mode+"-"+name)
        wd.mkdir()
        if not positive:
            try:
                bsgs.native_child(binary, fields, wd)
            except ValueError:
                checked += 1
            else:
                refuse(mode + " accepted invalid " + name)
        else:
            ans, _ = run_child(binary, fields, wd, mode, (80,10), toy)
            if ans["result_scalar"] != 2:
                refuse(mode + " solved wrong toy scalar")
            forged = dict(ans)
            forged["result_scalar"] = 3
            try:
                raw = blind.canonical(forged)
                if mode == "bsgs":
                    bsgs.check_response(raw, (80,10), toy)
                else:
                    verify_rho(raw, (80,10), toy)
            except ValueError:
                checked += 1
            else:
                refuse(mode + " accepted forged scalar")
            checked += 1
    return checked

def compare(rho_binary, bsgs_binary):
    with tempfile.TemporaryDirectory(prefix="ct323-matched-") as td:
        root = Path(td)
        controls = (negative_controls(rho_binary, "rho", root) +
                    negative_controls(bsgs_binary, "bsgs", root))
        public_file = root / "public.json"
        private_file = root / "private.json"
        issued = blind.publish(bsgs.PRIME31, 4, public_file, private_file)
        public_raw = public_file.read_bytes()
        public = group.strict(public_raw)
        curve = public["witness"]
        observations, secret_observations = [], []
        # No private file read until after every complete cold trial exits.
        for block, target in enumerate(curve["targets"]):
            Q = target["Q"]
            if block % 2 == 0:
                ordering = ("bsgs", "rho", "rho", "bsgs")
            else:
                ordering = ("rho", "bsgs", "bsgs", "rho")
            fields = (curve["p"],curve["a"],curve["b"],
                      curve["subgroup_prime"],*curve["generator"],*Q)
            for slot, arm in enumerate(ordering):
                wd = root / ("block-%d-slot-%d" % (block,slot))
                wd.mkdir()
                executable = bsgs_binary if arm == "bsgs" else rho_binary
                ans, cap = run_child(executable, fields, wd, arm, Q, curve)
                secret_observations.append((target["target_id"],
                                            ans["result_scalar"]))
                observations.append({
                    "block":block, "position":slot, "arm":arm,
                    "target_id":target["target_id"],
                    "external_wall_ns":cap["external_wall_ns"],
                    "peak_rss_kib":cap["peak_rss_kib"],
                    "cpu_affinity":cap["cpu_affinity"],
                    "argv_sha256":cap["argv_sha256"],
                    "binary_sha256":cap["binary_sha256"],
                    "stdout_sha256":cap["stdout_sha256"],
                    "stderr_sha256":cap["stderr_sha256"],
                    "affine_adds":ans["affine_adds"],
                    "field_inversions":ans["field_inversions"],
                    "inside_ns":ans["inside_ns"],
                    **({"walk_steps":ans["walk_steps"],
                        "distinguished_entries":ans["distinguished_entries"],
                        "restarts":ans["restarts"]} if arm=="rho" else {
                        "baby_table_entries":ans["baby_table_entries"],
                        "giant_iterations":ans["giant_iterations"]})
                })
        # Reveal only now, after all native children have exited.
        private_raw = private_file.read_bytes()
        admission = blind.audit(public_raw, private_raw)
        revealed = group.strict(private_raw)
        true_k = {entry["target_id"]:entry["scalar"]
                  for entry in revealed["reveals"]}
        for tid, k in secret_observations:
            if true_k.get(tid) != k:
                refuse("post-exit reveal mismatch for " + tid)
        for block in range(4):
            rows = observations[4*block:4*block+4]
            if [r["arm"] for r in rows] != (
                 ["bsgs","rho","rho","bsgs"] if block%2==0
                 else ["rho","bsgs","bsgs","rho"]):
                refuse("ABBA order changed")
            if len({tuple(r["cpu_affinity"]) for r in rows}) != 1:
                refuse("CPU affinity diverged")
        stats = {}
        for arm in ("bsgs","rho"):
            rows = [r for r in observations if r["arm"]==arm]
            stats[arm] = {
                "native_children":len(rows),
                "median_external_wall_ns":statistics.median(
                    r["external_wall_ns"] for r in rows),
                "median_peak_rss_kib":statistics.median(
                    r["peak_rss_kib"] for r in rows),
                "total_affine_adds":sum(r["affine_adds"] for r in rows),
                "total_field_inversions":sum(r["field_inversions"] for r in rows),
            }
        return {
            "schema":"ct323-native-same-Q-bsgs-rho/v1",
            "source_curve":curve["curve_id"],
            "subgroup_order":curve["subgroup_prime"],
            "source": "CT322 existing ordinary prime31, not new weak curve",
            "public_challenge_sha256":issued["public_sha256"],
            "public_challenge":public,
            "matched_blocks":4,
            "matched_fresh_native_children":len(observations),
            "verified_post_exit_public_discrete_logs":len(secret_observations),
            "commitments_rechecked":admission["target_count"],
            "toy_and_corruption_controls":controls,
            "statistics":stats,
            "raw_child_digest_and_counter_rows":observations,
            "strongest_optimized_rho_or_ic":False,
            "transferred_candidate_executions":0,
            "original_jacobian_native_executions":0,
            "full_seven_arm_cold_panel":False,
            "independent_execution_authenticated":False,
            "qualified_complete_ECDLP_speedup":False,
            "pcc":"unverified",
        }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rho-native", type=Path, required=True)
    parser.add_argument("--bsgs-native", type=Path, required=True)
    args=parser.parse_args()
    print(json.dumps(compare(args.rho_native,args.bsgs_native),
                     sort_keys=True))

if __name__ == "__main__":
    main()
