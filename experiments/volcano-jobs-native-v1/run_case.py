#!/usr/bin/env python3
"""Run one frozen ca-volcano workload and emit isolated_bench's result row."""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import subprocess
import sys
import time
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKLOADS = Path(__file__).with_name("workloads.json")


def mix64(x: int) -> int:
    x &= (1 << 64) - 1
    x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & ((1 << 64) - 1)
    x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & ((1 << 64) - 1)
    return x ^ (x >> 31)


def trial_seed(seed: int, trial: int) -> int:
    return mix64((seed * 0x9E3779B97F4A7C15 + trial) & ((1 << 64) - 1)) | 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ca", type=Path, required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--jobs", choices=("serial", "1", "4"), required=True)
    parser.add_argument("--trials", type=int, required=True)
    parser.add_argument("--per-level", type=int, required=True)
    parser.add_argument("--controls", type=int, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cases = json.loads(WORKLOADS.read_text())["cases"]
    try:
        case = next(c for c in cases if c["id"] == args.case)
    except StopIteration:
        raise SystemExit("unknown workload case")

    arms = 1 if case["id"] == "hist-shape-33bit-36solves" else 6
    if args.trials * arms != 36:
        raise SystemExit("protocol case must contain exactly 36 solves")
    cmd = [str(args.ca), "volcano", "--p", str(case["p"]),
           "--a", str(case["a"]), "--b", str(case["b"]),
           "--order", str(case["curve_order"]), "--ell", str(case["ell"]),
           "--seed", str(case["seed"]), "--trials", str(args.trials),
           "--per-level", str(args.per_level), "--controls", str(args.controls),
           "--threads", "1", "--dp-bits", "8", "--r", "16"]
    if args.jobs != "serial":
        cmd.extend(["--jobs", args.jobs])

    with tempfile.TemporaryDirectory(prefix="volcano-jobs-v1-") as tmp:
        temp = Path(tmp)
        trials_path, diagram_path = temp / "trials.csv", temp / "volcano.diagram.json"
        cmd.extend(["--trials-out", str(trials_path), "--diagram", str(diagram_path)])
        start = time.monotonic_ns()
        proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
        online_ms = (time.monotonic_ns() - start) / 1_000_000

        if proc.stdout:
            print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.stderr:
            print(proc.stderr, file=sys.stderr, end="" if proc.stderr.endswith("\n") else "\n")
        if proc.returncode != 0:
            return proc.returncode or 1
        try:
            payload = json.loads(proc.stdout)
            raw_csv = trials_path.read_text()
            trials = list(csv.DictReader(io.StringIO(raw_csv)))
            diagram = json.loads(diagram_path.read_text())
        except (OSError, json.JSONDecodeError, csv.Error) as exc:
            print("campaign output parse failure:", exc, file=sys.stderr)
            return 1

        expected_generator = ",".join(map(str, case["generator"]))
        expected_target = ",".join(map(str, case["target"]))
        expected_jobs = 1 if args.jobs == "serial" else int(args.jobs)
        checks = {
            "status": payload.get("status") == "ok",
            "curve_order": payload.get("order") == case["curve_order"],
            "subgroup_order": payload.get("n") == case["subgroup_order"],
            "seed": payload.get("rho", {}).get("seed") == case["seed"],
            "trials": payload.get("rho", {}).get("trials") == args.trials,
            "solves": payload.get("rho", {}).get("solves") == 36,
            "wrong": payload.get("rho", {}).get("wrong") == 0,
            "ell": payload.get("ell") == case["ell"],
            "answer": payload.get("k") == case["known_scalar"],
            "generator": payload.get("g") == expected_generator,
            "target": payload.get("h") == expected_target,
            "curve_count": len(payload.get("curves", [])) == arms,
            "trial_rows": len(trials) == 36,
            "diagram_schema": diagram.get("schema") == "volcano-diagram/v1",
        }
        if args.jobs != "serial":
            checks["jobs"] = payload.get("rho", {}).get("jobs") == expected_jobs
        else:
            checks["serial_workers"] = payload.get("rho", {}).get("jobs", 1) == 1
        checks["trial_seeds"] = all(
            int(row["seed"]) == trial_seed(case["seed"], int(row["trial"]))
            for row in trials
        )
        checks["arm_trial_coverage"] = (
            {(row["arm"], int(row["trial"])) for row in trials}
            == {(arm["arm"], t) for arm in payload.get("curves", [])
                for t in range(args.trials)}
        )
        if not all(checks.values()):
            print("correctness checks failed: " + json.dumps(checks, sort_keys=True),
                  file=sys.stderr)
            return 1

        ops_rows = [{key: row[key] for key in
                     ("arm", "vertex", "level", "trial", "seed", "ops")}
                    for row in trials]
        ops_sha = hashlib.sha256(
            (json.dumps(ops_rows, sort_keys=True, separators=(",", ":")) + "\n").encode()
        ).hexdigest()
        print("TRIALS_BEGIN")
        print(raw_csv, end="" if raw_csv.endswith("\n") else "\n")
        print("TRIALS_END")
        print("DIAGRAM_B64=" + base64.b64encode(diagram_path.read_bytes()).decode("ascii"))
        print("online_ms=%.6f verified=1 workload_id=%s answer=%s generator=%s target=%s solves=36 jobs=%d ops_sha256=%s" % (
            online_ms, case["workload_id"], case["known_scalar"], expected_generator,
            expected_target, expected_jobs, ops_sha))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
