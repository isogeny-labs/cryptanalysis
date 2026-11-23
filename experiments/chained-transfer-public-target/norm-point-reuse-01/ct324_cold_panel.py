#!/usr/bin/env python3
"""CT324-B preregistered three-arm native cold public-target comparison.

This is a producer-run exploratory control, not a complete transfer solver,
strongest rho or independent signed PCC. [pcc:unverified]
"""
import argparse
import json
from pathlib import Path
import statistics
import tempfile

import ct317_group_replay as group
import ct321_blind_challenge as blind
import ct322_live_prime31_bsgs as bsgs
import ct323_matched_prime31_control as oldrho

NEW_FIELDS = {"schema", "result_scalar", "walk_steps", "distinguished_entries",
              "restarts", "affine_adds", "field_inversions", "batch_waves",
              "batched_elements", "inside_ns", "original_jacobian_calls", "pcc"}

def reject(msg):
    raise ValueError("CT324-B: " + msg)

def verify_new(raw, target, curve):
    x = group.strict(raw)
    if (type(x) is not dict or set(x) != NEW_FIELDS
        or x["schema"] != "ct324-native-batched-rho/v1"
        or x["original_jacobian_calls"] != 0 or x["pcc"] != "unverified"):
        reject("new native schema mismatch")
    for field in NEW_FIELDS - {"schema", "pcc"}:
        if type(x[field]) is not int or x[field] < 0:
            reject("invalid native field " + field)
    if (x["result_scalar"] == 0 or x["result_scalar"] >= curve["subgroup_prime"]
        or x["walk_steps"] > 64 * (__import__("math").isqrt(curve["subgroup_prime"]-1)+1)
        or x["distinguished_entries"] > 65536
        or x["batch_waves"] > x["walk_steps"]
        or x["field_inversions"] > x["affine_adds"]
        or x["batched_elements"] > x["walk_steps"]
        or x["inside_ns"] == 0):
        reject("native counters outside limits")
    point = group.mul(x["result_scalar"], tuple(curve["generator"]),
                      curve["p"], curve["a"])
    if point != tuple(target):
        reject("independent source group equation failed")
    return x

def evaluate(arm, path, fields, root, target, curve):
    folder = root / path
    folder.mkdir()
    capture = bsgs.native_child(arm[1], fields, folder)
    native_raw = capture.pop("native")
    if arm[0] == "bsgs":
        answer = bsgs.check_response(native_raw, target, curve)
    elif arm[0] == "old":
        answer = oldrho.verify_rho(native_raw, target, curve)
    else:
        answer = verify_new(native_raw, target, curve)
    return {
        "arm": arm[0],
        "result_scalar": answer["result_scalar"],
        "wall_ns": capture["external_wall_ns"],
        "peak_rss_kib": capture["peak_rss_kib"],
        "affine_adds": answer["affine_adds"],
        "field_inversions": answer["field_inversions"],
        "batch_waves": answer.get("batch_waves"),
        "walk_steps": answer.get("walk_steps"),
        "binary_sha256": capture["binary_sha256"],
        "argv_sha256": capture["argv_sha256"],
        "stdout_sha256": capture["stdout_sha256"],
        "stderr_sha256": capture["stderr_sha256"],
        "cpu_affinity": capture["cpu_affinity"],
    }

def compare(bsgs_binary, old_binary, new_binary):
    with tempfile.TemporaryDirectory(prefix="ct324-panel-") as td:
        root=Path(td)
        bins={"bsgs":bsgs_binary,"old":old_binary,"new":new_binary}
        toy=(97,2,3,5,3,6,80,10)
        toycurve={"p":97,"a":2,"subgroup_prime":5,"generator":[3,6]}
        for key in ("bsgs","old","new"):
            r=evaluate((key,bins[key]),"toy-"+key,toy,root,[80,10],toycurve)
            if r["result_scalar"] != 2:
                reject("toy recovered wrong scalar in "+key)
        pub_path=root/"public.json"
        private_path=root/"private.json"
        issued=blind.publish(bsgs.PRIME31,4,pub_path,private_path)
        public_raw=pub_path.read_bytes()
        pub=group.strict(public_raw)
        curve=pub["witness"]
        obs=[]
        for block,target in enumerate(curve["targets"]):
            Q=target["Q"]
            fields=(curve["p"],curve["a"],curve["b"],
                    curve["subgroup_prime"],*curve["generator"],*Q)
            order=(("bsgs","old","new","new","old","bsgs") if block%2==0
                   else ("new","old","bsgs","bsgs","old","new"))
            for position,key in enumerate(order):
                r=evaluate((key,bins[key]),"b%d-s%d"%(block,position),
                           fields,root,Q,curve)
                obs.append(dict(r,block=block,position=position,
                                target_id=target["target_id"]))
        # The private scalar/salt manifest is first read after all native children exit.
        private_raw=private_path.read_bytes()
        revealed=blind.audit(public_raw,private_raw)
        secret=group.strict(private_raw)
        true_k={x["target_id"]:x["scalar"] for x in secret["reveals"]}
        for r in obs:
            if true_k.get(r["target_id"]) != r["result_scalar"]:
                reject("post-exit reveal mismatch")
        for block in range(4):
            rows=obs[6*block:6*block+6]
            observed=[r["arm"] for r in rows]
            expected=(["bsgs","old","new","new","old","bsgs"] if block%2==0
                      else ["new","old","bsgs","bsgs","old","new"])
            if observed!=expected or len({tuple(r["cpu_affinity"]) for r in rows})!=1:
                reject("order or affinity")
        stats={}
        for name in ("bsgs","old","new"):
            rows=[r for r in obs if r["arm"]==name]
            stats[name]={
                "n":len(rows),
                "median_external_wall_ns":statistics.median(r["wall_ns"] for r in rows),
                "median_peak_rss_kib":statistics.median(r["peak_rss_kib"] for r in rows),
                "total_affine_adds":sum(r["affine_adds"] for r in rows),
                "total_field_inversions":sum(r["field_inversions"] for r in rows),
            }
        return {"schema":"ct324-three-arm-native-cold/v1",
                "public_challenge_sha256":issued["public_sha256"],
                "source_curve":curve["curve_id"],
                "public_target_count":revealed["target_count"],
                "native_children":len(obs),
                "correct_public_logs":len(obs),
                "statistics":stats,
                "observations":obs,
                "original_jacobian_executions":0,
                "strongest_optimized_rho":False,
                "complete_transfer_advantage":False,
                "independent_pcc":False,
                "pcc":"unverified"}

if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bsgs",required=True,type=Path)
    ap.add_argument("--old",required=True,type=Path)
    ap.add_argument("--new",required=True,type=Path)
    args=ap.parse_args()
    print(json.dumps(compare(args.bsgs,args.old,args.new),sort_keys=True))
