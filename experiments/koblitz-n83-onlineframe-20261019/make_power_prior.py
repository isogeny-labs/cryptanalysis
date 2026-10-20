#!/usr/bin/env python3
"""Build the power prior (`inputs/power_prior.json`) from run 39214027289.

The prior is the rank-probe experiment's archived receipt
(`../koblitz-n83-rankprobe-20261019/run_github_39214027289/panel`), the
current n = 83 baseline measured on the same kind of runner:

* per cold point (20 points, segments C1-C20): `online_ms`, `cold_ms` and
  the probe count of cR and of cP. They are two processes of the same
  online code (the rank-probe producer's S3 online loop; cR and cP differ
  only in the rank stage, which a cold process skips), so cP / cR is the
  paired online A/A noise of one point, the null of this experiment;
* per rank block (four blocks): kP's `rank_stage_ms`, for the end-to-end
  secondary's scale only.

No timing of this experiment enters the prior. The candidate's effect is a
parameter of `power_check.py`, not read from here; the local diagnostics
(`smoke/`) only motivate the expected value it reports.
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
    points, rank = {}, []
    for row in rows:
        if row.get("status") != "valid":
            continue
        if row["arm"] in ("cR", "cP") and row["segment"].startswith("C"):
            fields = raw(panel, row)["fields"]
            points.setdefault(row["point_id"], {})[row["arm"]] = {
                "online_ms": fields["online_ms"], "cold_ms": fields["cold_ms"], "probes": fields["ops"]}
        elif row["arm"] == "kP":
            rank.append(raw(panel, row)["fields"]["rank_stage_ms"])
    for unit, arms in points.items():
        if arms["cR"]["probes"] != arms["cP"]["probes"]:
            raise ValueError("cR and cP probes differ on %s" % unit)
    return {"schema": 1,
            "source": "koblitz-n83-rankprobe-20261019/run_github_39214027289 (arms cR, cP on C1-C20; kP)",
            "runs_jsonl_sha256": hashlib.sha256((panel / "runs.jsonl").read_bytes()).hexdigest(),
            "points": {u: points[u] for u in sorted(points) if {"cR", "cP"} <= set(points[u])},
            "kP_rank_stage_ms": rank}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    args = parser.parse_args()
    OUT.write_text(json.dumps(build(args.archive), sort_keys=True, separators=(",", ":")) + "\n")
    print(str(OUT))


if __name__ == "__main__":
    main()
