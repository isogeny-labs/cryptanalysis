#!/usr/bin/env python3
"""Build the power prior (`inputs/power_prior.json`) from the k4c400 run (D4, one binary).

Source: run 42425640847, `koblitz-n83-k4c400-20261107` (on main, archived as
`run_github_42425640847/`, `panel/runs.jsonl` hydrated by `tools/artifacts/artifacts.py pull`;
its SHA-256 is checked against the archive's `.artifacts.json`). It ran the field-ops
producer on the D4 base (arms kD4FO, cD4FO) in 60 alternating primary pairs (its side B) and
40 A/A pairs (B against Baa: the SAME arm twice, same point and rank seed, so identical work)
on one GitHub runner. That is exactly the work of this experiment's two sides, so:

* the A/A pairs give the NOISE of a ratio of two processes that do identical work (the
  noise a true effect has to rise above), per pair: E2E, cold and rank-stage ratios;
* the primary B-side pairs give the SIZES (rank stage, cold, online, index build) and the
  process wall of each kind of run, for the runtime estimate.

Each raw record's SHA-256 must equal the wrapper's `raw_result_sha256`; only valid rows are used.
Nothing here is a result of this experiment.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "inputs" / "power_prior.json"
RUN_DIR = HERE.parent / "koblitz-n83-k4c400-20261107" / "run_github_42425640847"
RUNS_SHA256 = "572c25dfc46712ad73a2037ecec62798f8aa144c91a4f360d2bbf16206a75a05"


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
    parser.add_argument("--run-dir", type=Path, default=RUN_DIR)
    args = parser.parse_args()
    runs_path = args.run_dir / "panel" / "runs.jsonl"
    run_sha = hashlib.sha256(runs_path.read_bytes()).hexdigest()
    if run_sha != RUNS_SHA256:
        raise SystemExit("runs.jsonl differs from the pinned archive: " + run_sha)
    allocation = json.loads((args.run_dir / "allocation.json").read_text())
    rows = [json.loads(line) for line in runs_path.read_text().splitlines() if line]
    sides, walls = {}, {}
    for row in rows:
        if row["status"] != "valid":
            continue
        walls.setdefault(row["arm"], []).append(row["process_wall_ms"])
        if row.get("role") not in ("primary", "aa"):
            continue
        f = raw_of(args.run_dir, row)["fields"]
        key = "%s/%s/%d" % (row["role"], row["point_id"], row["pair"])
        side = sides.setdefault(key, {}).setdefault(row["side"], {})
        if row["arm"].startswith("k"):
            side["rank_stage_ms"] = f["rank_stage_ms"]
            side["rank_wall_ms"] = row["process_wall_ms"]
        else:
            side.update({"cold_ms": f["cold_ms"], "online_ms": f["online_ms"], "index_ms": f["index_ms"],
                         "scan_selftest_ms": f["scan_selftest_ms"], "cold_wall_ms": row["process_wall_ms"]})
    primary = {k[len("primary/"):]: v["B"] for k, v in sorted(sides.items()) if k.startswith("primary/")}
    aa = {k[len("aa/"):]: {"B": v["B"], "Baa": v["Baa"]} for k, v in sorted(sides.items()) if k.startswith("aa/")}
    prior = {
        "schema": 1,
        "sources": {"run": "https://github.com/isogeny-labs/cryptanalysis/actions/runs/42425640847",
                    "archive": "experiments/koblitz-n83-k4c400-20261107/run_github_42425640847 (on main)",
                    "runs_jsonl_sha256": run_sha,
                    "host": "GitHub ubuntu-24.04 runner %s, %s, one pinned CPU (allocation.json)" % (
                        allocation["runner_name"], allocation["observed_cpu_model"])},
        "d4_primary_pairs": primary,
        "d4_aa_pairs": aa,
        "process_wall_ms": {arm: sorted(v) for arm, v in sorted(walls.items())},
    }
    OUT.write_text(json.dumps(prior, indent=1, sort_keys=True) + "\n")
    print(str(OUT))


if __name__ == "__main__":
    main()
