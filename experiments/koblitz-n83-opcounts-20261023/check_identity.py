#!/usr/bin/env python3
"""Bit-identity and overhead check of the op-counting producer (local, diagnostic).

Runs the frozen stacked binary `ic_online_stacked_r770`, the counted source
built without `op-counts` ("off") and with it ("on") through the stacked
experiment's own `arm.py`, unchanged (its environment, gates and checks), and
compares every output that is not a clock:

* `cold`: arm cS on Q0 (seed 7, verified cached factor-log table), `--rounds`
  interleaved rounds of (frozen, off, on) in a rotated order. Compared: the
  target record's relation, x-codes, intermediates, probes, root calls,
  relation checks, skipped states and scalar; the summary's index digest,
  state and table counts.
* `rank` (with `--rank`): arm kS on K1 point s000 at rank seed 101 (the
  archived K1 process, run 38862448935 serial 42), with `on` and `off`.
  Compared with each other and with the archived record: every attempt's
  probes, `rank_relations_blake3`, root calls, and the written factor-log
  table (arm.py requires it to equal B's archived table).

Overhead is reported as on / off and on / frozen of the producer's own clocks
(setup, index build, rank stage, online), per round and as a median. This is
the cloud-agent VM, so the ratios are diagnostics, not Tier 1 timing.
"""

import argparse
import base64
import hashlib
import json
import os
import statistics
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STACKED = HERE.parent / "koblitz-n83-stacked-20261016"
ARCHIVE = STACKED / "run_github_38862448935" / "panel" / "runs"
ARCHIVED_K1 = {"kS": "00042", "kP": "00043"}

TARGET_KEYS = ("point_indices", "x_codes", "pinned_intermediates", "probes", "root_calls",
               "relation_checks", "skipped_symmetric_states", "recovered_scalar", "group_verified",
               "fold_audit_probes", "filter_passes", "scan_start_or_key")
SUMMARY_KEYS = ("base_hash", "regular_states", "stored_states", "root_table_entries", "root_table_slots",
                "index_digest", "rank", "rank_attempts", "rank_relations", "rank_failures",
                "rank_probes_total", "rank_root_calls_total", "rank_rows_without_gain",
                "rank_attempt_probes", "rank_relations_blake3", "rank_skipped_symmetric_states")


def decode(stdout):
    lines = [line for line in stdout.splitlines() if line.startswith("raw_b64=")]
    if len(lines) != 1:
        raise ValueError("no raw record in arm output")
    return json.loads(base64.b64decode(lines[0][len("raw_b64="):]))


def split(record):
    targets = [r for r in record["records"] if r.get("kind") == "compact_orbit_dlp_target"]
    summary = [r for r in record["records"] if r.get("kind") == "compact_orbit_dlp_summary"]
    return targets, (summary[0] if summary else {})


def run_arm(binary, arm, point, seed, cpu):
    protocol = json.loads((STACKED / "protocol.json").read_text())
    kind = protocol["arms"][arm]["kind"]
    argv = [sys.executable, str(STACKED / "arm.py"), "--arm", arm, "--kind", kind, "--panel", "identity",
            "--binary", str(binary), "--seed", str(seed), "--point", "%s,%s" % tuple(point),
            "--base", str(STACKED / protocol["online"]["base"]),
            "--log-table", str((STACKED / protocol["online"]["factor_log_table"]).resolve())]
    if cpu is not None:
        argv = ["taskset", "-c", str(cpu)] + argv
    proc = subprocess.run(argv, cwd=str(STACKED), capture_output=True, text=True)
    record = decode(proc.stdout)
    targets, summary = split(record)
    return {"returncode": proc.returncode, "issues": record["issues"], "targets": targets,
            "summary": summary, "fields": record["fields"]}


def comparable(result):
    target = result["targets"][0] if result["targets"] else {}
    return ({key: target.get(key) for key in TARGET_KEYS},
            {key: result["summary"].get(key) for key in SUMMARY_KEYS})


def clocks(result):
    summary = result["summary"]
    timing = summary.get("timing_ms") or {}
    target = result["targets"][0] if result["targets"] else {}
    return {"setup_ms": summary.get("setup_complete_ns", 0) / 1e6, "index_build_ms": timing.get("index_build"),
            "rank_stage_ms": timing.get("rank_stage"), "online_ms": target.get("online_ms"),
            "cold_in_process_ms": summary.get("cold_in_process_ms")}


def archived(arm):
    record = decode((ARCHIVE / (ARCHIVED_K1[arm] + ".stdout.txt")).read_text())
    return split(record)[1]


def ratios(rows, numerator, denominator, key):
    values = []
    for row in rows:
        a, b = row[numerator][key], row[denominator][key]
        if a and b:
            values.append(a / b)
    return {"per_round": values, "median": statistics.median(values) if values else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen", required=True, type=Path, help="ic_online_stacked_r770")
    parser.add_argument("--off", required=True, type=Path, help="counted source, built without op-counts")
    parser.add_argument("--on", required=True, type=Path, help="counted source, built with op-counts")
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--rank", action="store_true", help="also run kS to full rank with on and off")
    parser.add_argument("--cpu", type=int, default=None)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    schedule = json.loads((STACKED / "schedule.json").read_text())
    runs = [run for segment in schedule["segments"] for run in segment["runs"]]
    q0 = next(run for run in runs if run["point_id"] == "q0" and run["arm"] == "cS")
    k1 = next(run for segment in schedule["segments"] if segment["id"] == "K1"
              for run in segment["runs"] if run["arm"] == "kS")
    binaries = {"frozen": args.frozen, "off": args.off, "on": args.on}
    result = {"binaries_sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest()
                                  for name, path in binaries.items()},
              "host": os.uname().nodename, "cpu": args.cpu, "cold": [], "rank": {}}
    order = ["frozen", "off", "on"]
    for round_index in range(args.rounds):
        row = {}
        for name in order[round_index % 3:] + order[:round_index % 3]:
            row[name] = run_arm(binaries[name], "cS", q0["point"], q0["seed"], args.cpu)
            print(json.dumps({"round": round_index, "binary": name, "returncode": row[name]["returncode"],
                              "issues": row[name]["issues"], **clocks(row[name])}), flush=True)
        result["cold"].append(row)
    cold_ok = all(row[name]["returncode"] == 0 and not row[name]["issues"]
                  for row in result["cold"] for name in order)
    reference = comparable(result["cold"][0]["frozen"])
    cold_identical = all(comparable(row[name]) == reference for row in result["cold"] for name in order)
    on_counts = [row["on"]["summary"].get("op_counts") for row in result["cold"]]
    off_counts = [row["off"]["summary"].get("op_counts") for row in result["cold"]]
    checks = {
        "cold_all_valid": cold_ok,
        "cold_outputs_identical_frozen_off_on": cold_identical,
        "cold_on_counts_enabled": all((c or {}).get("enabled") is True for c in on_counts),
        "cold_off_counts_disabled": all(c == {"enabled": False} for c in off_counts),
        "cold_frozen_has_no_counts": all("op_counts" not in row["frozen"]["summary"] for row in result["cold"]),
        "cold_on_counts_deterministic": all(c == on_counts[0] for c in on_counts),
    }
    timing = {}
    clock_rows = [{name: clocks(row[name]) for name in order} for row in result["cold"]]
    for key in ("setup_ms", "index_build_ms", "online_ms", "cold_in_process_ms"):
        timing[key] = {"on_over_off": ratios(clock_rows, "on", "off", key),
                       "on_over_frozen": ratios(clock_rows, "on", "frozen", key),
                       "off_over_frozen": ratios(clock_rows, "off", "frozen", key)}
    result["clocks"] = clock_rows
    if args.rank:
        want = archived("kS")
        for name in ("on", "off"):
            result["rank"][name] = run_arm(binaries[name], "kS", k1["point"], k1["seed"], args.cpu)
            print(json.dumps({"rank": name, "returncode": result["rank"][name]["returncode"],
                              "issues": result["rank"][name]["issues"], **clocks(result["rank"][name])}),
                  flush=True)
        for name in ("on", "off"):
            summary = result["rank"][name]["summary"]
            checks["rank_%s_valid" % name] = (result["rank"][name]["returncode"] == 0 and
                                              not result["rank"][name]["issues"])
            checks["rank_%s_equals_archived_K1" % name] = all(
                summary.get(key) == want.get(key)
                for key in ("rank_attempt_probes", "rank_relations_blake3", "rank_probes_total",
                            "rank_root_calls_total", "rank_attempts", "rank_relations", "rank"))
        checks["rank_on_equals_off"] = comparable(result["rank"]["on"]) == comparable(result["rank"]["off"])
        rank_clocks = {name: clocks(result["rank"][name]) for name in ("on", "off")}
        timing["rank_stage_ms"] = {"on_over_off": rank_clocks["on"]["rank_stage_ms"] /
                                   rank_clocks["off"]["rank_stage_ms"]}
        result["rank_clocks"] = rank_clocks
    result["checks"] = checks
    result["overhead"] = timing
    result["identical"] = all(checks.values())
    for row in result["cold"]:
        for name in order:
            row[name] = {"returncode": row[name]["returncode"], "issues": row[name]["issues"],
                         "comparable": comparable(row[name]), "op_counts": row[name]["summary"].get("op_counts"),
                         "target_op_counts": (row[name]["targets"] or [{}])[0].get("op_counts")}
    for name, value in list(result["rank"].items()):
        result["rank"][name] = {"returncode": value["returncode"], "issues": value["issues"],
                                "rank_relations_blake3": value["summary"].get("rank_relations_blake3"),
                                "op_counts": value["summary"].get("op_counts"),
                                "target_op_counts": (value["targets"] or [{}])[0].get("op_counts")}
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "overhead_medians": {
        key: {k: (v["median"] if isinstance(v, dict) else v) for k, v in value.items()}
        for key, value in timing.items()}}, indent=2, sort_keys=True))
    return 0 if result["identical"] else 1


if __name__ == "__main__":
    sys.exit(main())
