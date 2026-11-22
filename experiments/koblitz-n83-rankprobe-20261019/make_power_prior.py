#!/usr/bin/env python3
"""Build the power prior (`inputs/power_prior.json`) from run 38891404048.

The prior is the rank-cut experiment's archived receipt
(`../koblitz-n83-rankcut-20261016/run_github_38891404048/panel`), the
baseline of this experiment measured on the same kind of runner:

* per rank block (rank seeds 201-204): the per-attempt ns of kR (the
  rank-cut loop, `KIC_RANK_SOLVE=padd`, this experiment's baseline rank arm)
  and of its A/A process kRaa. Both ran the same attempts with the same
  probes, so kRaa_i / kR_i is the paired timing noise of one attempt; the
  stage's non-attempt time;
* per cold point (20 points): cold_ms of cR and of cS, two processes of the
  same cold code (the rank-cut producer's cold path, this experiment's
  baseline cold arm), i.e. the cold A/A pair.

No timing of this experiment enters the prior. The candidate's effect is a
parameter of `power_check.py`, not read from here; the local profile
(`smoke/`, a diagnostic) only motivates the expected value it reports.
"""

import argparse
import base64
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE.parent / "koblitz-n83-rankcut-20261016" / "run_github_38891404048" / "panel"
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
        if row["arm"] in ("kR", "kRaa"):
            record = raw(panel, row)
            summary = next(r for r in record["records"] if r.get("kind") == "compact_orbit_dlp_summary")
            attempts = summary["rank_attempt_ns"]
            stage = summary["timing_ms"]["rank_stage"]
            blocks.setdefault(str(row["seed"]), {})[row["arm"]] = {
                "attempt_ns": attempts, "attempt_probes": summary["rank_attempt_probes"],
                "rank_stage_ms": stage, "non_attempt_ms": stage - sum(attempts) / 1e6}
        elif row["arm"] in ("cR", "cS") and row["segment"].startswith("C"):
            cold.setdefault(row["point_id"], {})[row["arm"]] = raw(panel, row)["fields"]["cold_ms"]
    for seed, block in blocks.items():
        if block["kR"]["attempt_probes"] != block["kRaa"]["attempt_probes"]:
            raise ValueError("kR and kRaa attempts differ in block %s" % seed)
    return {"schema": 1,
            "source": "koblitz-n83-rankcut-20261016/run_github_38891404048 (arms kR, kRaa, cR, cS)",
            "runs_jsonl_sha256": hashlib.sha256((panel / "runs.jsonl").read_bytes()).hexdigest(),
            "rank_blocks": {seed: {"kR_attempt_ns": b["kR"]["attempt_ns"], "kRaa_attempt_ns": b["kRaa"]["attempt_ns"],
                                   "kR_non_attempt_ms": b["kR"]["non_attempt_ms"],
                                   "kRaa_non_attempt_ms": b["kRaa"]["non_attempt_ms"]}
                            for seed, b in sorted(blocks.items())},
            "cold_ms": {u: cold[u] for u in sorted(cold) if {"cR", "cS"} <= set(cold[u])}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ARCHIVE,
                        help="the archived panel directory (default: the rank-cut experiment's)")
    args = parser.parse_args()
    OUT.write_text(json.dumps(build(args.archive), sort_keys=True, separators=(",", ":")) + "\n")
    print(str(OUT))


if __name__ == "__main__":
    main()
