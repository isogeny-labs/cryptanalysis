#!/usr/bin/env python3
"""Local exactness diagnostic (cloud-agent VM; never timing evidence).

Runs the index-lift producer directly, with `arm.py`'s environment:

* `cold`: Q0 with the verified cached table, one process per index mode
  (`selected` = cP, `lift` = cPI, `lift` + `KIC_SCAN_SELFTEST=sampled` =
  cPIT, `lift_plant` = cPIX), concurrently;
* `rank`: rank seed 301 on point s000 of the rank-probe panel (the inputs
  of run 39214027289's block K1) with `selected` (kP) and `lift` (kPI),
  concurrently, compared with the archived kP row of that block.

Writes `exactness_<what>_local.json` next to this file: per process the
index digests (B's and the two layout digests), counters, relation, scalar,
probe count, rank digests, and whether the written factor-log table equals
B's; times are recorded as diagnostics only.
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
BASE = EXP / "snapshots/r770/experiments/koblitz-single-target-n83-20261006/base_n83_K600.jsonl"
LOG_TABLE = (EXP.parent / "koblitz-single-target-n83-tier1-20261014/tier1_github_38523707244/precompute/"
             "factor_logs_n83_K600.json")
Q0 = json.loads((EXP.parent / "koblitz-single-target-n83-tier1-20261014/inputs/targets.json").read_text())["q0"]["point"]
RP_TARGETS = EXP.parent / "koblitz-n83-rankprobe-20261019/inputs/cold_targets.json"
ENV = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "RAYON_NUM_THREADS": "1", "KIC_THREADS": "1",
       "KIC_RHO_THREADS": "1", "OMP_NUM_THREADS": "1", "KIC_RANK_THREADS": "1", "KIC_TARGET_THREADS": "1",
       "KIC_INDEX_DIGEST": "1", "KIC_ROOT_TABLE": "compact", "KIC_STATE_FOLD": "1", "KIC_FOLD_PLANT": "0",
       "KIC_TARGET_CANON": "lift", "KIC_SCAN_ORDER": "feistel", "KIC_PROBE_PIPELINE": "prefetch"}
COLD = {"cP": ("selected", "full"), "cPI": ("lift", "full"), "cPIT": ("lift", "sampled"),
        "cPIX": ("lift_plant", "full")}
RANK = {"kP": "selected", "kPI": "lift"}


def rows(text):
    out = []
    for line in text.splitlines():
        if line.strip().startswith("{"):
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def launch(binary, folder, name, point, seed, extra):
    work = folder / name
    work.mkdir()
    (work / "points.jsonl").write_text(json.dumps([str(v) for v in point]) + "\n")
    env = dict(ENV, **extra)
    if "KIC_LOG_TABLE_OUT" in env:
        env["KIC_LOG_TABLE_OUT"] = str(work / "factor_logs.json")
    proc = subprocess.Popen([str(binary), str(BASE), str(work / "points.jsonl"), str(seed), str(work / "ic.jsonl")],
                            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return work, proc


def summarize(work, proc, rank):
    stdout, stderr = proc.communicate()
    summary = (rows(stdout) or [{}])[-1]
    record = (rows((work / "ic.jsonl").read_text()) or [{}])[0] if (work / "ic.jsonl").exists() else {}
    out = {"returncode": proc.returncode, "stderr_tail": stderr[-600:],
           "index_canonicalizer": summary.get("index_canonicalizer"),
           "index_plant_checked_inputs": summary.get("index_plant_checked_inputs"),
           "scan_order_selftest": summary.get("scan_order_selftest"),
           "stored_states": summary.get("stored_states"), "root_table_entries": summary.get("root_table_entries"),
           "index_digest": summary.get("index_digest"),
           "relation": record.get("point_indices"), "scalar": record.get("recovered_scalar"),
           "probes": record.get("probes"), "group_verified": record.get("group_verified"),
           "diagnostic_ms": {"index_build": (summary.get("timing_ms") or {}).get("index_build"),
                             "setup_complete": summary.get("setup_complete_ns", 0) / 1e6,
                             "online": record.get("online_ms"),
                             "rank_stage": (summary.get("timing_ms") or {}).get("rank_stage")}}
    if rank:
        archived = json.loads(LOG_TABLE.read_text())["logs"]
        produced = json.loads((work / "factor_logs.json").read_text())["logs"] if (work / "factor_logs.json").exists() else None
        out.update({"rank": summary.get("rank"), "rank_attempts": summary.get("rank_attempts"),
                    "rank_relations_blake3": summary.get("rank_relations_blake3"),
                    "rank_attempt_probes": summary.get("rank_attempt_probes"),
                    "rank_root_calls_total": summary.get("rank_root_calls_total"),
                    "rank_padd": {k[len("rank_padd_"):]: v for k, v in summary.items() if k.startswith("rank_padd_")},
                    "rank_frame": {k[len("rank_frame_"):]: v for k, v in summary.items() if k.startswith("rank_frame_")},
                    "logs_equal_B": produced == archived})
    return out


def archived_kp_k1():
    """The archived kP row of block K1 of run 39214027289 (from the extracted panel)."""
    panel = Path(os.environ.get("RP_PANEL", ""))
    for line in (panel / "runs.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row["arm"] == "kP" and row["segment"] == "K1":
            text = (panel / row["stdout_file"]).read_text()
            raw = json.loads(base64.b64decode([l[8:] for l in text.splitlines() if l.startswith("raw_b64=")][0]))
            summary = next(r for r in raw["records"] if r.get("kind") == "compact_orbit_dlp_summary")
            target = raw["records"][0]
            return {"rank_relations_blake3": summary["rank_relations_blake3"],
                    "rank_attempt_probes": summary["rank_attempt_probes"],
                    "rank_root_calls_total": summary["rank_root_calls_total"],
                    "rank_padd": {k[len("rank_padd_"):]: v for k, v in summary.items() if k.startswith("rank_padd_")},
                    "relation": target.get("point_indices"), "scalar": target.get("recovered_scalar"),
                    "probes": target.get("probes"), "seed": row["seed"], "point": row["command"]}
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("what", choices=("cold", "rank"))
    parser.add_argument("--binary", required=True, type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="n83-indexlift-smoke-") as tmp:
        folder = Path(tmp)
        jobs = {}
        if args.what == "cold":
            for arm, (canon, selftest) in COLD.items():
                jobs[arm] = launch(args.binary, folder, arm, Q0, 7,
                                   {"KIC_INDEX_CANON": canon, "KIC_SCAN_SELFTEST": selftest,
                                    "KIC_LOG_TABLE_IN": str(LOG_TABLE)})
        else:
            point = json.loads(RP_TARGETS.read_text())["points"][0]["point"]
            for arm, canon in RANK.items():
                jobs[arm] = launch(args.binary, folder, arm, point, 301,
                                   {"KIC_INDEX_CANON": canon, "KIC_SCAN_SELFTEST": "full",
                                    "KIC_LOG_TABLE_OUT": "x", "KIC_RANK_CANON": "lift", "KIC_RANK_ORDER": "feistel",
                                    "KIC_RANK_PROBE": "target", "KIC_RANK_SOLVE": "frame"})
        result = {arm: summarize(work, proc, args.what == "rank") for arm, (work, proc) in jobs.items()}
    out = {"what": args.what, "host": "cloud-agent VM (diagnostic only; processes ran concurrently)",
           "processes": result}
    keys = ("stored_states_blake3", "table_slots_blake3", "logical_states_blake3", "table_map_sum64",
            "table_map_xor64", "table_entries")
    out["one_index_digest_set"] = len({json.dumps([(p["index_digest"] or {}).get(k) for k in keys])
                                       for p in result.values()}) == 1
    out["one_relation_scalar_probes"] = len({json.dumps([p["relation"], p["scalar"], p["probes"]])
                                             for p in result.values()}) == 1
    if args.what == "rank":
        archived = archived_kp_k1()
        out["archived_kP_K1"] = {k: v for k, v in (archived or {}).items() if k != "rank_attempt_probes"}
        out["equal_to_archived_kP_K1"] = {
            arm: {k: p[k] == archived[k] for k in ("rank_relations_blake3", "rank_attempt_probes",
                                                   "rank_root_calls_total", "rank_padd", "relation", "scalar",
                                                   "probes")} for arm, p in result.items()} if archived else None
        for p in result.values():
            p["rank_attempt_probes_total"] = sum(p.pop("rank_attempt_probes") or [])
    path = HERE / ("exactness_%s_local.json" % args.what)
    path.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "processes"}, sort_keys=True))


if __name__ == "__main__":
    sys.exit(main())
