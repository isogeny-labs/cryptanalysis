#!/usr/bin/env python3
"""Build `inputs/power_prior.json` from the archived rank-probe run (39214027289).

Every number the cost model (`cost_model.py`) and the power check
(`power_check.py`) use comes from that one committed receipt
(`../koblitz-n83-rankprobe-20261019/run_github_39214027289/panel`), the n=83
baseline row's run, on the runner class this experiment uses:

* cP (the baseline's cold arm) per point: the setup phases (base load, normal
  basis, index build, factor-log load and verification, the Feistel
  self-test over the state vector, setup complete), the cold total, the online
  interval and its probe count;
* kP per rank block: the rank stage, its per-attempt probes (the probe law's
  check: 2,400 attempts are 2,400 one-target solves);
* rT (tuned rho rT770) per point: cold (setup + online), online and steps.

`--check` regenerates and compares.
"""

import argparse
import base64
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE.parent / "koblitz-n83-rankprobe-20261019" / "run_github_39214027289" / "panel"
OUT = HERE / "inputs" / "power_prior.json"


def raw(row):
    for line in (RUN / row["stdout_file"]).read_text().splitlines():
        if line.startswith("raw_b64="):
            return json.loads(base64.b64decode(line[len("raw_b64="):]))
    raise ValueError("no raw record in serial %d" % row["serial"])


def build():
    rows = [json.loads(line) for line in (RUN / "runs.jsonl").read_text().splitlines() if line.strip()]
    cold, rank, rho = [], [], []
    for row in rows:
        if row["status"] != "valid" or row["point_id"] == "q0":
            continue
        record = raw(row)
        fields = record["fields"]
        if row["arm"] == "cP":
            summary = next(r for r in record["records"] if r.get("kind") == "compact_orbit_dlp_summary")
            timing = summary["timing_ms"]
            cold.append({"point": row["point_id"], "base_load_ms": timing["base_load"],
                         "basis_ms": timing["normal_basis_and_selftest"], "index_ms": timing["index_build"],
                         "log_load_and_verify_ms": timing["linear_algebra"],
                         "scan_selftest_ms": summary["scan_order_selftest"]["ms"],
                         "setup_complete_ms": summary["setup_complete_ns"] / 1e6,
                         "cold_ms": summary["cold_in_process_ms"], "online_ms": fields["online_ms"],
                         "probes": fields["ops"]})
        elif row["arm"] == "kP":
            summary = next(r for r in record["records"] if r.get("kind") == "compact_orbit_dlp_summary")
            rank.append({"block": row["segment"], "rank_stage_ms": fields["rank_stage_ms"],
                         "attempt_probes": summary["rank_attempt_probes"],
                         "attempt_ns": summary["rank_attempt_ns"]})
        elif row["arm"] == "rT":
            rho.append({"point": row["point_id"], "cold_ms": (fields.get("setup_ms") or 0.0) + fields["online_ms"],
                        "online_ms": fields["online_ms"], "steps": int(fields["ops"])})
    return {"schema": 1, "source": "koblitz-n83-rankprobe-20261019 run 39214027289 (panel/runs.jsonl, raw records)",
            "runner": "GitHub ubuntu-24.04, one pinned CPU (the run's host-probe.json)",
            "orbit_columns": 600, "subgroup_order": 8569786107849059,
            "cold_cP": cold, "rank_kP": rank, "rho_rT": rho}


def text(record):
    return json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    record = text(build())
    if args.check:
        if OUT.read_text() != record:
            raise SystemExit("inputs/power_prior.json differs from the archived run")
        print("power_prior_verified=" + str(OUT))
        return
    OUT.write_text(record)
    print(str(OUT))


if __name__ == "__main__":
    main()
