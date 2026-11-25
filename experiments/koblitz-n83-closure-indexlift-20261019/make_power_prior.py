#!/usr/bin/env python3
"""Build the power prior (`inputs/power_prior.json`) from the two parents' Tier 1 runs.

No timing of this experiment enters the prior. Sources (archived receipts,
same runner class):

* the closure run 39305259093 (`koblitz-n83-closure-20261019`,
  `run_github_39305259093/panel`, selected index build):
  - per rank block: the per-attempt ns and probes and the non-attempt time
    of kP (600 attempts on B's K600 header, blocks K1, K5, K9, K13: the
    baseline rank loop), kM38 and its A/A kM38aa (16 attempts, the 16
    blocks), and kM10 (60 attempts, 8 blocks);
  - per cold point: cold_ms of cP, cM38, cM38aa and cM10.
* the index-lift run 39290913632 (`koblitz-n83-indexlift-20261019`,
  `run_github_39290913632/panel`): per cold point, cold_ms of cP (selected
  index build) and cPI (lift_scan index build). Their ratio is the
  index-lift cold factor that `power_check.py` applies to every cold arm of
  this design (all arms here build the index with lift_scan; the rank stage
  does not depend on the index canonicalizer, which the layout gate makes
  byte identical).

The candidate's effect is a parameter of `power_check.py`, not read from
here.
"""

import argparse
import base64
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLOSURE = HERE.parent / "koblitz-n83-closure-20261019" / "run_github_39305259093" / "panel"
INDEXLIFT = HERE.parent / "koblitz-n83-indexlift-20261019" / "run_github_39290913632" / "panel"
OUT = HERE / "inputs" / "power_prior.json"


def raw(panel, row):
    for line in (panel / row["stdout_file"]).read_text().splitlines():
        if line.startswith("raw_b64="):
            return json.loads(base64.b64decode(line[len("raw_b64="):]))
    raise ValueError("no raw record for serial %d" % row["serial"])


def rows(panel):
    return [json.loads(line) for line in (panel / "runs.jsonl").read_text().splitlines() if line.strip()]


def summary(record):
    return next(r for r in record["records"] if r.get("kind") == "compact_orbit_dlp_summary")


def build(closure, indexlift):
    blocks, cold, lift = {}, {}, {}
    for row in rows(closure):
        if row.get("status") != "valid":
            raise ValueError("closure run has a row that is not valid: %d" % row["serial"])
        if row["arm"] in ("kP", "kM38", "kM38aa", "kM10"):
            s = summary(raw(closure, row))
            stage = s["timing_ms"]["rank_stage"]
            blocks.setdefault(row["segment"], {})[row["arm"]] = {
                "attempt_ns": s["rank_attempt_ns"], "attempt_probes": s["rank_attempt_probes"],
                "non_attempt_ms": stage - sum(s["rank_attempt_ns"]) / 1e6, "rank_stage_ms": stage}
        elif row["arm"] in ("cP", "cM38", "cM38aa", "cM10") and row["segment"].startswith("C"):
            cold.setdefault(row["point_id"], {})[row["arm"]] = raw(closure, row)["fields"]["cold_ms"]
    for row in rows(indexlift):
        if row.get("status") == "valid" and row["arm"] in ("cP", "cPI") and row["segment"].startswith("C"):
            lift.setdefault(row["point_id"], {})[row["arm"]] = raw(indexlift, row)["fields"]["cold_ms"]
    for segment, block in blocks.items():
        if "kM38aa" in block and block["kM38"]["attempt_probes"] != block["kM38aa"]["attempt_probes"]:
            raise ValueError("kM38 and kM38aa attempts differ in block %s" % segment)
    return {"schema": 1,
            "sources": {
                "closure": {"run": 39305259093, "archive": "koblitz-n83-closure-20261019/run_github_39305259093/panel",
                            "arms": ["kP", "kM38", "kM38aa", "kM10", "cP", "cM38", "cM38aa", "cM10"],
                            "runs_jsonl_sha256": hashlib.sha256((closure / "runs.jsonl").read_bytes()).hexdigest()},
                "indexlift": {"run": 39290913632,
                              "archive": "koblitz-n83-indexlift-20261019/run_github_39290913632/panel",
                              "arms": ["cP", "cPI"],
                              "runs_jsonl_sha256": hashlib.sha256((indexlift / "runs.jsonl").read_bytes()).hexdigest()}},
            "rank_blocks": {segment: block for segment, block in sorted(blocks.items())},
            "cold_ms": {u: cold[u] for u in sorted(cold)},
            "indexlift_cold_ms": {u: lift[u] for u in sorted(lift) if {"cP", "cPI"} <= set(lift[u])}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--closure-archive", type=Path, default=CLOSURE)
    parser.add_argument("--indexlift-archive", type=Path, default=INDEXLIFT)
    args = parser.parse_args()
    OUT.write_text(json.dumps(build(args.closure_archive, args.indexlift_archive), sort_keys=True,
                              separators=(",", ":")) + "\n")
    print(str(OUT))


if __name__ == "__main__":
    main()
