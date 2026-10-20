#!/usr/bin/env python3
"""Build the power prior (`inputs/power_prior.json`) from run 39214027289.

The prior is the rank-probe experiment's archived receipt
(`../koblitz-n83-rankprobe-20261019/run_github_39214027289/panel`), the
K600 baseline of this experiment measured on the same kind of runner:

* per rank block (rank seeds 301-304): the per-attempt ns and probes of kP
  (the rank-probe rank stage, this experiment's kP600) and of its A/A
  process kPaa (same attempts, same probes), and each stage's non-attempt
  time;
* per cold point (20 points): cold_ms of cP and of cR, two processes of the
  same cold code (the cold A/A pair), and of cPI.

No timing of this experiment enters the prior. The K899 cost ratios are
parameters of `power_check.py` (from the diagnostic run, `inputs/k899_identity.json`).
"""

import argparse
import base64
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE.parent / "koblitz-n83-rankprobe-20261019" / "run_github_39214027289" / "panel"
OUT = HERE / "inputs" / "power_prior.json"


def raw(panel, row):
    for line in (panel / row["stdout_file"]).read_text().splitlines():
        if line.startswith("raw_b64="):
            return json.loads(base64.b64decode(line[len("raw_b64="):]))
    raise ValueError("no raw record for serial %d" % row["serial"])


def build(panel):
    rows = [json.loads(line) for line in (panel / "runs.jsonl").read_text().splitlines() if line.strip()]
    blocks, cold = {}, {}
    for row in rows:
        if row.get("status") != "valid":
            continue
        if row["arm"] in ("kP", "kPaa"):
            record = raw(panel, row)
            summary = next(r for r in record["records"] if r.get("kind") == "compact_orbit_dlp_summary")
            attempts = summary["rank_attempt_ns"]
            stage = summary["timing_ms"]["rank_stage"]
            blocks.setdefault(str(row["seed"]), {})[row["arm"]] = {
                "attempt_ns": attempts, "attempt_probes": summary["rank_attempt_probes"],
                "rank_stage_ms": stage, "non_attempt_ms": stage - sum(attempts) / 1e6}
        elif row["arm"] in ("cP", "cR", "cPI") and row["segment"].startswith("C"):
            cold.setdefault(row["point_id"], {})[row["arm"]] = raw(panel, row)["fields"]["cold_ms"]
    for seed, block in blocks.items():
        if block["kP"]["attempt_probes"] != block["kPaa"]["attempt_probes"]:
            raise ValueError("kP and kPaa attempts differ in block %s" % seed)
    return {"schema": 1,
            "source": "koblitz-n83-rankprobe-20261019/run_github_39214027289 (arms kP, kPaa, cP, cR, cPI)",
            "runs_jsonl_sha256": hashlib.sha256((panel / "runs.jsonl").read_bytes()).hexdigest(),
            "rank_blocks": {seed: {"kP_attempt_ns": b["kP"]["attempt_ns"], "kPaa_attempt_ns": b["kPaa"]["attempt_ns"],
                                   "kP_attempt_probes": b["kP"]["attempt_probes"],
                                   "kP_non_attempt_ms": b["kP"]["non_attempt_ms"],
                                   "kPaa_non_attempt_ms": b["kPaa"]["non_attempt_ms"]}
                            for seed, b in sorted(blocks.items())},
            "cold_ms": {u: cold[u] for u in sorted(cold) if {"cP", "cR", "cPI"} <= set(cold[u])}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    args = parser.parse_args()
    OUT.write_text(json.dumps(build(args.archive), sort_keys=True, separators=(",", ":")) + "\n")
    print(str(OUT))


if __name__ == "__main__":
    main()
