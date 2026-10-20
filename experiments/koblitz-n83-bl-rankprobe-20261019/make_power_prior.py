#!/usr/bin/env python3
"""Build `inputs/power_prior.json` for `power_check.py` from two archived runs.

* IC online: the 20 fresh points of the rank-probe run (run 39214027289,
  `../koblitz-n83-rankprobe-20261019/run_github_39214027289/panel/runs.jsonl`,
  arm `cP`): `online_ms` per point. Also its `rT` online times, its kP rank
  stages and the cP cold times, for the runtime estimate.
* BL online: the BL-arm run (run 38689817618, branch `claude/n83-bl-arm`,
  `experiments/koblitz-n83-bl-arm-20261014/run_github_38689817618/panel/runs.jsonl`,
  arm `bl`): `online_ms` and walk steps of its 20 rows, at B's budget of
  549.85 s (3.0348e9 covered points).

The BL rows are rescaled to this experiment's budget with the BL arm's frozen
random-mapping model (`bl_tools.predict_online_steps`): the budget here is the
rank-probe producer's rank stage + setup_total, taken from the rank-probe
run's kP rows (mean 159.1 s), so the covered count scales by that over
549.85 s, at B's measured ns per step. This is a model-based prior for sizing
only; nothing here is a measurement of this experiment.

Run with the two `runs.jsonl` paths (the BL-arm run is on an unmerged branch:
`git show origin/claude/n83-bl-arm:<path> > file`). The output records both
files' SHA-256.
"""

import argparse
import hashlib
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BL_DIR = HERE.parent / "koblitz-n83-bl-arm-20261014"
sys.path.insert(0, str(BL_DIR))
import bl_tools as bt  # noqa: E402  (the BL arm's frozen model)

R = 8569786107849059
AUTOMORPHISMS = 166
LANES, DP = 64, 6
B_COVERED = 3034824772
B_PRECOMPUTE_MS = 549847.988403


def jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rankprobe-runs", required=True, type=Path)
    parser.add_argument("--bl-runs", required=True, type=Path)
    parser.add_argument("--kp-rank-stage-plus-setup-ms", required=True, type=float,
                        help="mean timing_ms.rank_stage + setup_total of the rank-probe run's kP rows")
    args = parser.parse_args()
    rp = jsonl(args.rankprobe_runs)
    bl = jsonl(args.bl_runs)
    ic_online = [float(r["fields"]["online_ms"]) for r in rp if r["arm"] == "cP" and r["point_id"] != "q0"]
    rho_online = [float(r["fields"]["online_ms"]) for r in rp if r["arm"] == "rT"]
    cold_wall = [r["process_wall_ms"] for r in rp if r["arm"] == "cP" and r["point_id"] != "q0"]
    rank_wall = [r["process_wall_ms"] for r in rp if r["arm"] == "kP"]
    bl_rows = [r for r in bl if r["arm"] == "bl"]
    bl_online = [float(r["fields"]["online_ms"]) for r in bl_rows]
    bl_steps = [int(r["fields"]["ops"]) for r in bl_rows]
    bl_wall = [r["process_wall_ms"] for r in bl_rows]
    budget = args.kp_rank_stage_plus_setup_ms
    covered = B_COVERED * budget / B_PRECOMPUTE_MS
    model_b = bt.predict_online_steps(R, AUTOMORPHISMS, LANES, DP, B_COVERED)
    model_here = bt.predict_online_steps(R, AUTOMORPHISMS, LANES, DP, covered)
    scale = model_here / model_b
    prior = {
        "schema": 1,
        "class": "model-based sizing prior, not a measurement of this experiment",
        "sources": {"rankprobe_runs_sha256": hashlib.sha256(args.rankprobe_runs.read_bytes()).hexdigest(),
                    "rankprobe_run": "39214027289 (koblitz-n83-rankprobe-20261019/run_github_39214027289)",
                    "bl_runs_sha256": hashlib.sha256(args.bl_runs.read_bytes()).hexdigest(),
                    "bl_run": "38689817618 (claude/n83-bl-arm, koblitz-n83-bl-arm-20261014/run_github_38689817618)"},
        "ic_online_ms": ic_online,
        "rho_online_ms": rho_online,
        "bl_online_ms_at_b_budget": bl_online,
        "bl_steps_at_b_budget": bl_steps,
        "bl_scale": {"budget_ms_assumed": budget, "b_precompute_ms": B_PRECOMPUTE_MS, "b_covered": B_COVERED,
                     "covered_assumed": covered, "model_online_steps_b": model_b,
                     "model_online_steps_here": model_here, "factor": scale,
                     "rule": "BL online time here = B's row x factor (same ns per step, model ratio of steps)"},
        "bl_online_ms_scaled": [v * scale for v in bl_online],
        "runtime_ms": {"cP_process_wall_mean": statistics.mean(cold_wall),
                       "kP_process_wall_mean": statistics.mean(rank_wall),
                       "bl_process_wall_mean_at_b_table": statistics.mean(bl_wall),
                       "rT_online_mean": statistics.mean(rho_online)},
    }
    out = HERE / "inputs" / "power_prior.json"
    out.write_text(json.dumps(prior, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"out": str(out), "ic_points": len(ic_online), "bl_rows": len(bl_online),
                      "scale": scale}, sort_keys=True))


if __name__ == "__main__":
    main()
