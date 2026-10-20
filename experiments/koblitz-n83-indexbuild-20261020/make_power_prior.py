#!/usr/bin/env python3
"""Build the power prior (`inputs/power_prior.json`) from the Tier 1 template's archived run.

Source: run 39359922687, `koblitz-n83-closure-indexlift-rep-20261020`
(claude/n83-closure-indexlift-rep, commit 3f5dfdfa1, PR #1002), archived
there as `run_github_39359922687/`. That run measured the current row's
producer (side A of this experiment, arms kM38I and cM38I, unchanged) in
30 alternating primary pairs and 20 A/A pairs on one GitHub runner.
`--run-dir` points at a copy of that directory; the SHA-256 of its
`panel/runs.jsonl` is checked against `RUNS_SHA256`. Each raw record's
SHA-256 must equal the wrapper's `raw_result_sha256`, and only valid rows
are used.

Per primary pair (point, pair) it keeps kM38I's rank stage and process wall,
and cM38I's cold time, setup, index build, scan self-test and process wall.
Per A/A pair it keeps the B / Baa ratios of the rank stage (kM38I /
kM38Iaa) and of the cold time, index build and self-test (cM38I /
cM38Iaa). Every arm's process walls are kept for the runtime estimate.

Nothing here is a result of this experiment; the prior only sizes the
design (`power_check.py`). The candidate's effect is not in it: the
power check models it from the local diagnostic profile
(`inputs/local_profile.json`).
"""

import argparse
import base64
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "inputs" / "power_prior.json"
RUNS_SHA256 = "c7d215bffa9e50ef6f4c2e6b1be7110bbad463c4c789e3a1b49c80a8200c4397"


def raw_of(run_dir, row):
    lines = (run_dir / "panel" / row["stdout_file"]).read_text().splitlines()
    encoded = next(line[len("raw_b64="):] for line in lines if line.startswith("raw_b64="))
    raw_bytes = base64.b64decode(encoded, validate=True)
    summary = dict(w.split("=", 1) for w in next(l for l in reversed(lines) if "raw_result_sha256=" in l).split()
                   if "=" in w)
    if summary["raw_result_sha256"] != hashlib.sha256(raw_bytes).hexdigest():
        raise SystemExit("raw record digest differs for serial %d" % row["serial"])
    return json.loads(raw_bytes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    runs_path = args.run_dir / "panel" / "runs.jsonl"
    run_sha = hashlib.sha256(runs_path.read_bytes()).hexdigest()
    if run_sha != RUNS_SHA256:
        raise SystemExit("runs.jsonl differs from the pinned archive: " + run_sha)
    rows = [json.loads(line) for line in runs_path.read_text().splitlines() if line]
    sides, walls = {}, {}
    for row in rows:
        if row["status"] != "valid":
            continue
        walls.setdefault(row["arm"], []).append(row["process_wall_ms"])
        if row.get("role") not in ("primary", "aa"):
            continue
        raw = raw_of(args.run_dir, row)
        f = raw["fields"]
        key = "%s/%s/%d" % (row["role"], row["point_id"], row["pair"])
        side = sides.setdefault(key, {}).setdefault(row["side"], {})
        if row["arm"].startswith("k"):
            side["rank_stage_ms"] = f["rank_stage_ms"]
            side["rank_wall_ms"] = row["process_wall_ms"]
        else:
            side.update({"cold_ms": f["cold_ms"], "setup_ms": f["setup_ms"], "index_ms": f["index_ms"],
                         "scan_selftest_ms": f["scan_selftest_ms"], "cold_wall_ms": row["process_wall_ms"]})
    primary = {k[len("primary/"):]: v["B"] for k, v in sorted(sides.items()) if k.startswith("primary/")}
    aa = {}
    for k, v in sorted(sides.items()):
        if k.startswith("aa/"):
            b, c = v["B"], v["Baa"]
            aa[k[len("aa/"):]] = {"rank_stage": b["rank_stage_ms"] / c["rank_stage_ms"],
                                  "cold": b["cold_ms"] / c["cold_ms"], "index": b["index_ms"] / c["index_ms"],
                                  "scan_selftest": b["scan_selftest_ms"] / c["scan_selftest_ms"]}
    prior = {
        "schema": 1,
        "sources": {"run": "https://github.com/aburan28/cryptanalysis/actions/runs/39359922687",
                    "archive": ("experiments/koblitz-n83-closure-indexlift-rep-20261020/run_github_39359922687 "
                                "(claude/n83-closure-indexlift-rep, commit 3f5dfdfa1)"),
                    "runs_jsonl_sha256": run_sha,
                    "host": "GitHub ubuntu-24.04 runner runnervmxehtw, AMD EPYC 9V74, one pinned CPU (allocation.json)"},
        "side_A_primary_pairs": primary,
        "aa_ratios_B_over_Baa": aa,
        "process_wall_ms": {arm: sorted(v) for arm, v in sorted(walls.items())},
    }
    OUT.write_text(json.dumps(prior, indent=1, sort_keys=True) + "\n")
    print(str(OUT))


if __name__ == "__main__":
    main()
