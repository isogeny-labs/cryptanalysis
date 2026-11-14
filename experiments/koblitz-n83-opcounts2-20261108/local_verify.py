#!/usr/bin/env python3
"""Local verification of the counting pass on one point and seed per base (D4, M38).

For each base, the rank process (the k4c400 protocol's kD4FO / kM38FO
configuration) and the cold process (cD4FO / cM38FO, cached verified factor
logs) are run with exactly the environment of the k4c400 `arm.py`, by:

* `parent`: `ic_online_fieldops2_r770` built from the frozen field-ops-2
  source (d923d63a...), the uncounted producer;
* `off`: `ic_online_fieldops2_counted_r770` (feature op-counts) without
  KIC_OPCOUNTS;
* `on`: the same binary with KIC_OPCOUNTS=1, `--repeats` times.

Checked: every run exits 0 and passes the k4c400 `arm.check` gates against
its base (index and layout digests, closure shape, the frozen factor-log
table, ...), with the arm's field_ops_pipeline replaced by field-ops-2's; the
rank process writes the base's frozen factor-log table; `off` and `on`
outputs equal `parent`'s with timing fields, hardware counters and the
`op_counts` key removed; `on` counts are identical over the repeats; and the
counted probes are compared with the producer's own probe counts.

Writes `verify/local_verify.json` (no timings). No timing claims are made.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
K4C400 = HERE.parent / "koblitz-n83-k4c400-20261107"
FIELDOPS = HERE.parent / "koblitz-n83-fieldops-20261104"
FIELDOPS2 = HERE.parent / "koblitz-n83-fieldops2-20261107"
# The k4c400 arm.py, unchanged, under its own name (it imports the reconcile experiment's `arm`).
_spec = importlib.util.spec_from_file_location("k4c400_arm", K4C400 / "arm.py")
k4arm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(k4arm)

PIPELINE2 = ("fmul_clmul_inline+sqr_clmul_inline+state_square_clmul+maps_le_bytes+selftest_round_tables"
             "+n83_const_reduce_shift")
CLOSURE = {"M38": (16, 64), "D4": (4, 165)}
VOLATILE_SUFFIX = ("_ms", "_ns")
VOLATILE_PART = ("hw_", "peak_rss", "timing")


def volatile(key):
    return key in ("ms", "ns") or key.endswith(VOLATILE_SUFFIX) or any(part in key for part in VOLATILE_PART)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def strip(value):
    """Drop timing, hardware-counter, memory and op_counts fields, recursively."""
    if isinstance(value, dict):
        return {k: strip(v) for k, v in value.items()
                if k != "op_counts" and not volatile(k)}
    if isinstance(value, list):
        return [strip(v) for v in value]
    return value


def header(base, scratch):
    path = scratch / ("base_n83_closure_%s.jsonl" % base)
    if not path.exists():
        columns, cap = CLOSURE[base]
        subprocess.run([sys.executable, str(FIELDOPS / "make_closure_base.py"), "--columns", str(columns),
                        "--norm", str(cap), "--out", str(path)], check=True, stdout=subprocess.DEVNULL)
    want = k4arm.protocol()["online"]["bases"][base]["header_sha256"]
    if sha256(path) != want:
        raise SystemExit("closure header %s differs from the k4c400 frozen digest" % base)
    return path


def run(binary, base_path, point, seed, arm_name, folder, counting):
    protocol = k4arm.protocol()
    arm = dict(protocol["arms"][arm_name], field_ops_pipeline=PIPELINE2)
    spec = protocol["online"]["bases"][arm["base"]]
    rank = arm["kind"] == "ic_rank"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "points.jsonl"
    target.write_text(json.dumps([str(v) for v in point], separators=(",", ":")) + "\n")
    out = folder / "ic.jsonl"
    if out.exists():
        out.unlink()
    env = dict(k4arm.BASE_ENV, KIC_RANK_THREADS="1", KIC_TARGET_THREADS="1", KIC_INDEX_DIGEST="1",
               KIC_ROOT_TABLE=arm["table"], KIC_STATE_FOLD="1", KIC_FOLD_PLANT="0",
               KIC_INDEX_CANON=arm["index_canon"], KIC_SCAN_SELFTEST=arm["scan_selftest"],
               KIC_TARGET_CANON="lift", KIC_SCAN_ORDER="feistel", KIC_PROBE_PIPELINE="prefetch")
    table = K4C400 / spec["factor_log_table"]
    logs_out = folder / "factor_logs.json"
    if rank:
        env.update(KIC_LOG_TABLE_OUT=str(logs_out), KIC_RANK_CANON=arm["rank_canon"],
                   KIC_RANK_ORDER=arm["rank_order"], KIC_RANK_PROBE=arm["rank_probe"],
                   KIC_RANK_SOLVE=arm["rank_solve"])
    else:
        env["KIC_LOG_TABLE_IN"] = str(table)
    if counting:
        env["KIC_OPCOUNTS"] = "1"
    # Never CPU 2 (other agents time there); lowest priority.
    proc = subprocess.run(["nice", "-n", "19", "taskset", "-c", "3", str(binary), str(base_path), str(target),
                           str(seed), str(out)], env=env, capture_output=True, text=True)
    records = k4arm.reconcile_arm.rows(out.read_text()) if out.exists() else []
    summary = (k4arm.reconcile_arm.rows(proc.stdout) or [{}])[-1]
    record = records[0] if records else {}
    issues = [] if proc.returncode == 0 else ["exit %d: %s" % (proc.returncode, proc.stderr[-400:])]
    issues += k4arm.check(summary, record, spec, arm, point, rank)
    if rank:
        produced = json.loads(logs_out.read_text())["logs"] if logs_out.exists() else None
        if produced != json.loads(table.read_text())["logs"]:
            issues.append("rank-stage factor logs differ from the base's frozen table")
    return {"summary": summary, "record": record, "issues": issues}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, required=True, help="ic_online_fieldops2_r770")
    parser.add_argument("--counted", type=Path, required=True, help="ic_online_fieldops2_counted_r770 (op-counts)")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--bases", default="D4,M38")
    parser.add_argument("--point-id", default="s000")
    parser.add_argument("--rank-seed", type=int, default=2501)
    parser.add_argument("--cold-seed", type=int, default=7)
    parser.add_argument("--out", type=Path, default=HERE / "verify" / "local_verify.json")
    parser.add_argument("--counts-out", type=Path, default=HERE / "verify" / "counts.jsonl",
                        help="the counting pass in counted_band.py's --counts shape (band arm = base name)")
    args = parser.parse_args()
    scratch = HERE / "verify" / "scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    targets = json.loads((K4C400 / "inputs" / "cold_targets.json").read_text())["points"]
    point = next(p["point"] for p in targets if "s%03d" % p["seed"] == args.point_id)
    result = {"schema": "opcounts2-local-verify/v1", "point_id": args.point_id, "point": point,
              "rank_seed": args.rank_seed, "cold_seed": args.cold_seed, "repeats": args.repeats,
              "binaries_sha256": {"parent": sha256(args.parent), "counted": sha256(args.counted)},
              "host": os.uname().nodename, "bases": {}, "ok": True}
    count_rows = []
    for base in args.bases.split(","):
        base_path = header(base, scratch)
        entry = {"header_sha256": sha256(base_path), "processes": {}}
        for kind, arm_name, seed in (("rank", "k%sFO" % base, args.rank_seed), ("cold", "c%sFO" % base, args.cold_seed)):
            folder = scratch / base / kind
            parent = run(args.parent, base_path, point, seed, arm_name, folder / "parent", False)
            off = run(args.counted, base_path, point, seed, arm_name, folder / "off", False)
            ons = [run(args.counted, base_path, point, seed, arm_name, folder / ("on%d" % i), True)
                   for i in range(args.repeats)]
            ref = {"summary": strip(parent["summary"]), "record": strip(parent["record"])}
            dropped = sorted({k for k in list(parent["summary"]) + list(parent["record"]) if volatile(k)})
            counts = [{"summary": on["summary"].get("op_counts"), "record": on["record"].get("op_counts")}
                      for on in ons]
            s = parent["summary"]
            producer_probes = (sum(p for p in s.get("rank_attempt_probes") or [] if p) if kind == "rank"
                               else parent["record"].get("probes"))
            proc = {
                "arm": arm_name, "seed": seed,
                "issues": {"parent": parent["issues"], "off": off["issues"],
                           "on": [on["issues"] for on in ons]},
                "off_equals_parent": {"summary": strip(off["summary"]) == ref["summary"],
                                      "record": strip(off["record"]) == ref["record"]},
                "off_summary_diff_keys": sorted(k for k in set(ref["summary"]) | set(strip(off["summary"]))
                                                if ref["summary"].get(k) != strip(off["summary"]).get(k)),
                "off_has_no_op_counts": "op_counts" not in off["summary"] and "op_counts" not in off["record"],
                "on_equals_parent": [{"summary": strip(on["summary"]) == ref["summary"],
                                      "record": strip(on["record"]) == ref["record"]} for on in ons],
                "counts_identical_over_repeats": all(c == counts[0] for c in counts),
                "digests": {"index_digest": s.get("index_digest"), "rank_relations_blake3": s.get("rank_relations_blake3"),
                            "factor_log_table_input_blake3": (s.get("factor_log_table") or {}).get("input_blake3")},
                "producer_probes": producer_probes,
                "compared_keys": {"summary": len(ref["summary"]), "record": len(ref["record"]),
                                  "dropped_top_level": dropped},
                "op_counts": counts[0],
            }
            proc["ok"] = (not parent["issues"] and not off["issues"] and not any(on["issues"] for on in ons)
                          and all(proc["off_equals_parent"].values()) and proc["off_has_no_op_counts"]
                          and all(all(x.values()) for x in proc["on_equals_parent"])
                          and proc["counts_identical_over_repeats"] and counts[0]["summary"] is not None)
            result["ok"] &= proc["ok"]
            on = ons[0]
            count_rows.append({
                "arm": base, "base": base, "point_id": args.point_id, "pair": 1, "process": kind,
                "summary_op_counts": on["summary"].get("op_counts"), "record_op_counts": on["record"].get("op_counts"),
                "rank_probes": sum(p for p in on["summary"].get("rank_attempt_probes") or [] if p),
                "rank_attempts": len(on["summary"].get("rank_attempt_probes") or []),
                "online_probes": on["record"].get("probes")})
            entry["processes"][kind] = proc
            print(base, kind, "ok" if proc["ok"] else "FAIL", json.dumps(proc["issues"])[:300], flush=True)
        result["bases"][base] = entry
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.counts_out.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in count_rows))
    print("ok=%s" % result["ok"])
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
