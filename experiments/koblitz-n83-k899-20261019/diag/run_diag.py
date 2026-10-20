#!/usr/bin/env python3
"""K899 go/no-go diagnostic for the n=83 rank-probe producer (one runner, one pinned CPU).

Diagnostic only: no decision rule, no frozen panel. It answers three
questions before the Tier 1 experiment is frozen:

1. Does the rank-probe producer (koblitz-n83-rankprobe-20261019, restored
   and digest-checked by that experiment's own restore.py, built unchanged)
   accept the nested K899 base
   (n83-compact-orbit-k899-20261012/runs/K899/base.jsonl, of which B's K600
   base is an exact prefix) without code changes?
2. Index build time at K899 and the rank stage's wall time per probe (first
   50 attempts and the whole stage), against the same numbers at K600 on the
   same runner.
3. Exactness at K899: the written factor-log table re-verified in the pinned
   pure-Python oracle ([L_j]G = R_j for every column), its first 600 logs
   against B's archived K600 table (the K600 base is a prefix and the logs
   of fixed points are unique), the Q0 scalar at K899 equal to the archived
   scalar and replayed in the oracle, and the mean probes per rank attempt
   against the law r / (166 E), E = root-table entries.

Run order (one process at a time, pinned): cP600, kP899 (writes the K899
table), kP600, cP899, cP600, cP899, cPI600, cPI899. Diagnostic rank seed
8991 (not used by any frozen experiment).
"""

import argparse
import hashlib
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPERIMENTS = HERE.parent.parent
RP = EXPERIMENTS / "koblitz-n83-rankprobe-20261019"
RECONCILE = EXPERIMENTS / "koblitz-n83-reconcile-20261014"
sys.path.insert(0, str(RECONCILE))
import verify_log_table  # noqa: E402
import arm as reconcile_arm  # noqa: E402
sys.path.insert(0, str(RP))
from verify_receipt import oracle  # noqa: E402  (the pinned oracle in RP's restored snapshot)

BASES = {
    600: RP / "snapshots/r770/experiments/koblitz-single-target-n83-20261006/base_n83_K600.jsonl",
    899: EXPERIMENTS / "n83-compact-orbit-k899-20261012/runs/K899/base.jsonl",
}
TABLE600 = EXPERIMENTS / ("koblitz-single-target-n83-tier1-20261014/tier1_github_38523707244/"
                          "precompute/factor_logs_n83_K600.json")
SEED = 8991
Q0_SCALAR = 3141592653589793


def run(binary, base, point, seed, env_extra, cpu, out_dir, tag):
    out_dir.mkdir(parents=True, exist_ok=True)
    points = out_dir / (tag + ".points.jsonl")
    points.write_text(json.dumps([str(v) for v in point]) + "\n")
    out = out_dir / (tag + ".ic.jsonl")
    env = dict(reconcile_arm.BASE_ENV, KIC_RANK_THREADS="1", KIC_TARGET_THREADS="1", KIC_INDEX_DIGEST="1",
               KIC_ROOT_TABLE="compact", KIC_STATE_FOLD="1", KIC_FOLD_PLANT="0",
               KIC_TARGET_CANON="lift", KIC_SCAN_ORDER="feistel", KIC_PROBE_PIPELINE="prefetch")
    env.update(env_extra)
    started = time.time()
    proc = subprocess.run([str(binary), str(base), str(points), str(seed), str(out)], env=env,
                          capture_output=True, text=True, preexec_fn=lambda: os.sched_setaffinity(0, {cpu}))
    wall = time.time() - started
    (out_dir / (tag + ".stdout.txt")).write_text(proc.stdout)
    (out_dir / (tag + ".stderr.txt")).write_text(proc.stderr[-20000:])
    summary = (reconcile_arm.rows(proc.stdout) or [{}])[-1]
    records = reconcile_arm.rows(out.read_text()) if out.exists() else []
    record = records[0] if records else {}
    return proc.returncode, wall, summary, record


def describe(tag, k, code, wall, summary, record, rank):
    timing = summary.get("timing_ms") or {}
    row = {"tag": tag, "K": k, "exit": code, "process_wall_s": wall,
           "orbit_columns": summary.get("orbit_columns"), "base_hash": summary.get("base_hash"),
           "regular_states": summary.get("regular_states"), "stored_states": summary.get("stored_states"),
           "root_table_entries": summary.get("root_table_entries"),
           "root_table_slots": summary.get("root_table_slots"), "root_table_bytes": summary.get("root_table_bytes"),
           "peak_rss_bytes": summary.get("peak_rss_bytes"), "timing_ms": timing,
           "cold_phase_ms": summary.get("cold_phase_ms"), "cold_in_process_ms": summary.get("cold_in_process_ms"),
           "setup_ms": summary.get("setup_complete_ns", 0) / 1e6,
           "scan_order_selftest": summary.get("scan_order_selftest"),
           "index_digest": summary.get("index_digest"), "index_canonicalizer": summary.get("index_canonicalizer"),
           "factor_log_table": summary.get("factor_log_table"),
           "targets_solved": summary.get("targets_solved"), "targets_failed": summary.get("targets_failed"),
           "target": {"recovered_scalar": record.get("recovered_scalar"), "probes": record.get("probes"),
                      "online_ms": record.get("online_ms"), "relation": record.get("point_indices"),
                      "group_verified": record.get("group_verified")}}
    if rank:
        ns = summary.get("rank_attempt_ns") or []
        probes = summary.get("rank_attempt_probes") or []
        entries = summary.get("root_table_entries") or 0
        r = 8569786107849059
        law = r / (166.0 * entries) if entries else None
        good = [(t, p) for t, p in zip(ns, probes) if p]
        first = good[:50]
        row["rank"] = {
            "rank": summary.get("rank"), "attempts": summary.get("rank_attempts"),
            "failures": summary.get("rank_failures"), "rows_without_gain": summary.get("rank_rows_without_gain"),
            "probes_total": summary.get("rank_probes_total"), "probes_mean": summary.get("rank_probes_mean"),
            "probes_sd": statistics.pstdev([p for _, p in good]) if good else None,
            "law_mean": law, "probes_mean_over_law": (summary.get("rank_probes_mean") / law) if law else None,
            "ns_per_probe_all": sum(t for t, _ in good) / sum(p for _, p in good) if good else None,
            "ns_per_probe_first50": sum(t for t, _ in first) / sum(p for _, p in first) if first else None,
            "first50_ms": sum(t for t, _ in first) / 1e6, "first50_probes": sum(p for _, p in first),
            "attempt_ns": ns, "attempt_probes": probes,
            "rank_relations_blake3": summary.get("rank_relations_blake3"),
            "frame_builds": summary.get("rank_frame_builds"), "rank_solve": summary.get("rank_solve"),
        }
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bin-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cpu", type=int, required=True)
    parser.add_argument("--only", help="comma list of tags (local smoke only)")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    point = [int(v) for v in json.loads((RP / "protocol.json").read_text())["design"]["q0_point"]]
    binary = args.bin_dir / "ic_online_rankprobe_r770"
    curve = oracle()
    table899 = args.out / "factor_logs_n83_K899.json"
    table600_written = args.out / "factor_logs_n83_K600_seed8991.json"
    rank = {"KIC_RANK_CANON": "lift", "KIC_RANK_ORDER": "feistel", "KIC_RANK_PROBE": "target",
            "KIC_RANK_SOLVE": "frame"}
    plan = [
        ("cP600_a", 600, {"KIC_LOG_TABLE_IN": str(TABLE600)}, False),
        ("kP899", 899, dict(rank, KIC_LOG_TABLE_OUT=str(table899)), True),
        ("kP600", 600, dict(rank, KIC_LOG_TABLE_OUT=str(table600_written)), True),
        ("cP899_a", 899, {"KIC_LOG_TABLE_IN": str(table899)}, False),
        ("cP600_b", 600, {"KIC_LOG_TABLE_IN": str(TABLE600)}, False),
        ("cP899_b", 899, {"KIC_LOG_TABLE_IN": str(table899)}, False),
        ("cPI600", 600, {"KIC_LOG_TABLE_IN": str(TABLE600), "KIC_INDEX_CANON": "lift"}, False),
        ("cPI899", 899, {"KIC_LOG_TABLE_IN": str(table899), "KIC_INDEX_CANON": "lift"}, False),
    ]
    only = set(args.only.split(",")) if args.only else None
    rows = []
    checks = {}
    for tag, k, extra, is_rank in plan:
        if only and tag not in only:
            continue
        if "KIC_LOG_TABLE_IN" in extra and not Path(extra["KIC_LOG_TABLE_IN"]).exists():
            rows.append({"tag": tag, "K": k, "skipped": "factor-log table missing"})
            continue
        code, wall, summary, record = run(binary, BASES[k], point, SEED, extra, args.cpu, args.out / "raw", tag)
        row = describe(tag, k, code, wall, summary, record, is_rank)
        scalar = record.get("recovered_scalar")
        row["target"]["scalar_is_q0"] = scalar is not None and int(scalar) == Q0_SCALAR
        row["target"]["oracle_replay"] = (scalar is not None and
                                          curve.mul(curve.g, int(scalar)) == curve.decode(point))
        rows.append(row)
        print(json.dumps({key: row.get(key) for key in ("tag", "exit", "process_wall_s", "setup_ms")} |
                         {"index_ms": row["timing_ms"].get("index_build"),
                          "rank_ms": row["timing_ms"].get("rank_stage"),
                          "ns_probe": (row.get("rank") or {}).get("ns_per_probe_all")}), flush=True)
        if tag == "kP899" and table899.exists():
            checks["k899_table_oracle"] = verify_log_table.verify(table899, BASES[899], curve)
            logs899 = json.loads(table899.read_text())["logs"]
            logs600 = json.loads(TABLE600.read_text())["logs"]
            checks["k899_first600_equal_B_K600"] = logs899[:600] == logs600
            checks["k899_table_sha256"] = hashlib.sha256(table899.read_bytes()).hexdigest()
            checks["k899_logs_sha256"] = hashlib.sha256(json.dumps(logs899).encode()).hexdigest()
        if tag == "kP600" and table600_written.exists():
            checks["k600_written_equal_B_K600"] = (json.loads(table600_written.read_text())["logs"] ==
                                                   json.loads(TABLE600.read_text())["logs"])
    by = {row["tag"]: row for row in rows if "skipped" not in row}

    def mean_of(tags, getter):
        values = [getter(by[t]) for t in tags if t in by and getter(by[t]) is not None]
        return sum(values) / len(values) if values else None

    index = lambda row: row["timing_ms"].get("index_build")  # noqa: E731
    setup = lambda row: row["setup_ms"]  # noqa: E731
    derived = {
        "index_ms_cold_K600": mean_of(["cP600_a", "cP600_b"], index),
        "index_ms_cold_K899": mean_of(["cP899_a", "cP899_b"], index),
        "index_ms_rank_K600": mean_of(["kP600"], index),
        "index_ms_rank_K899": mean_of(["kP899"], index),
        "index_ms_lift_K600": mean_of(["cPI600"], index),
        "index_ms_lift_K899": mean_of(["cPI899"], index),
        "setup_ms_cold_K600": mean_of(["cP600_a", "cP600_b"], setup),
        "setup_ms_cold_K899": mean_of(["cP899_a", "cP899_b"], setup),
        "setup_ms_lift_K600": mean_of(["cPI600"], setup),
        "setup_ms_lift_K899": mean_of(["cPI899"], setup),
    }
    for k in (600, 899):
        rk = (by.get("kP%d" % k) or {}).get("rank") or {}
        derived["rank_stage_ms_K%d" % k] = (by.get("kP%d" % k) or {}).get("timing_ms", {}).get("rank_stage")
        derived["ns_per_probe_all_K%d" % k] = rk.get("ns_per_probe_all")
        derived["ns_per_probe_first50_K%d" % k] = rk.get("ns_per_probe_first50")
        derived["probes_mean_over_law_K%d" % k] = rk.get("probes_mean_over_law")
        derived["first50_ms_K%d" % k] = rk.get("first50_ms")
    gates = {
        "index_build_K899_le_55s": (derived["index_ms_cold_K899"] or 1e18) <= 55_000,
        "ns_per_probe_K899_le_150": (derived["ns_per_probe_all_K899"] or 1e18) <= 150 and
                                    (derived["ns_per_probe_first50_K899"] or 1e18) <= 150,
        "every_process_exit0_one_target_q0_scalar_oracle": all(
            row["exit"] == 0 and row["targets_solved"] == 1 and row["target"]["scalar_is_q0"] and
            row["target"]["oracle_replay"] for row in by.values()),
        "k899_table_oracle_pass": (checks.get("k899_table_oracle") or {}).get("status") == "PASS",
        "k899_first600_equal_B_K600": checks.get("k899_first600_equal_B_K600") is True,
        "k600_written_equal_B_K600": checks.get("k600_written_equal_B_K600") is True,
    }
    result = {"kind": "n83-k899-diagnostic", "seed": SEED, "cpu": args.cpu, "rows": rows,
              "checks": checks, "derived": derived, "gates": gates,
              "go": all(gates.values()),
              "note": "diagnostic only; one process per arm (two for cold), Q0; not timing evidence for a claim"}
    (args.out / "diag.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"derived": derived, "gates": gates, "go": result["go"],
                      "checks": {k: v for k, v in checks.items() if k != "k899_table_oracle"}}, indent=1))


if __name__ == "__main__":
    main()
