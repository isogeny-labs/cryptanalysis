#!/usr/bin/env python3
"""Build the power prior (`inputs/power_prior.json`) from the parent's archived Tier 1 run.

Source: `../koblitz-n83-closure-indexlift-20261019/run_github_39335956567/`
(PR #997, run 39335956567, the run this experiment replicates). Its
`panel/runs.jsonl` and every row's raw producer record (`raw_b64=` in
`panel/runs/<serial>.stdout.txt`) are read. Each raw record's SHA-256 must
equal the wrapper's `raw_result_sha256`, and only rows that the parent's
verifier counted as valid are used.

Per cold point (s000..s019) it keeps the cold time (`cold_in_process_ms`)
of cPI, cM38I and cM38Iaa and the process wall of every arm. Per rank block
(K1..K16) it keeps, for kPI, kM38I, kM38Iaa and kM38IX: the rank stage, the
per-attempt nanoseconds and probes, the non-attempt time (rank stage minus
the sum of the attempts) and the process wall. Nothing here is a result of
this experiment. The prior only sizes the design (`power_check.py`).

`--run-dir` points at a copy of the archived run directory (the default is
its path on origin/main).
"""

import argparse
import base64
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE.parent / "koblitz-n83-closure-indexlift-20261019" / "run_github_39335956567"
OUT = HERE / "inputs" / "power_prior.json"
COLD = ("cPI", "cM38I", "cM38Iaa")
RANK = ("kPI", "kM38I", "kM38Iaa", "kM38IX")


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
    parser.add_argument("--run-dir", type=Path, default=RUN)
    args = parser.parse_args()
    rows = [json.loads(line) for line in (args.run_dir / "panel" / "runs.jsonl").read_text().splitlines() if line]
    cold, blocks, walls = {}, {}, {}
    for row in rows:
        if row["status"] != "valid":
            continue
        walls.setdefault(row["arm"], []).append(row["process_wall_ms"])
        if row["segment"].startswith("C") and row["arm"] in COLD:
            raw = raw_of(args.run_dir, row)
            cold.setdefault(row["point_id"], {})[row["arm"]] = raw["fields"]["cold_ms"]
        elif row["segment"].startswith("K") and row["arm"] in RANK:
            raw = raw_of(args.run_dir, row)
            summary = next(r for r in raw["records"] if r.get("kind") == "compact_orbit_dlp_summary")
            stage = raw["fields"]["rank_stage_ms"]
            ns = summary["rank_attempt_ns"]
            blocks.setdefault(row["segment"], {})[row["arm"]] = {
                "rank_stage_ms": stage, "attempt_ns": ns, "attempt_probes": summary["rank_attempt_probes"],
                "non_attempt_ms": stage - sum(ns) / 1e6, "process_wall_ms": row["process_wall_ms"],
                "seed": row["seed"]}
    run_sha = hashlib.sha256((args.run_dir / "panel" / "runs.jsonl").read_bytes()).hexdigest()
    prior = {
        "schema": 1,
        "sources": {"run": "https://github.com/aburan28/cryptanalysis/actions/runs/39335956567",
                    "archive": "experiments/koblitz-n83-closure-indexlift-20261019/run_github_39335956567",
                    "runs_jsonl_sha256": run_sha,
                    "host": "GitHub ubuntu-24.04 runner, AMD EPYC 7763, one pinned CPU (the parent's allocation.json)"},
        "cold_ms": dict(sorted(cold.items())),
        "rank_blocks": dict(sorted(blocks.items(), key=lambda kv: int(kv[0][1:]))),
        "process_wall_ms": {arm: sorted(v) for arm, v in sorted(walls.items())},
    }
    OUT.write_text(json.dumps(prior, indent=1, sort_keys=True) + "\n")
    print(str(OUT))


if __name__ == "__main__":
    main()
