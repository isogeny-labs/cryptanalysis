#!/usr/bin/env python3
"""Local diagnostic of R1: alternating fresh pinned processes of side A and side B.

LOCAL DIAGNOSTIC, never evidence: it runs on whatever machine runs it (a shared
cloud-agent VM in the session that wrote it), pinned to one CPU, to size the
power check (`power_check.py` reads `inputs/local_profile.json`) and to compare
the two producers' identities before the Tier 1 run.

A = `target-a/release/ic_online_fieldops_r770` (the row), B =
`target-b/release/ic_online_fieldops2_r770` (R1), built from `online/` and
`online-b/` (both with +pclmulqdq). Cold rounds run `run_cold.sh` (M38, cached
log table, arm.py's ic_cold environment, Q0-independent first panel point,
seed 7), rank rounds `run_rank.sh` (rank seed 1501), each round A then B, one
fresh process each. Stages: index build `timing_ms.index_build`, scan self-test
`scan_order_selftest.ms`, online `timing_ms.target_median` (the cold
process's one target), rank stage `timing_ms.rank_stage`.

Identities compared between A and B on every round: the whole `index_digest`
record and `base_hash`, and on rank rounds the relation digest, the
per-attempt probe vector, the root calls and the table-map digests it
carries. B's `field_ops_pipeline` is not in the stdout summary, so it is not
compared here (the Tier 1 verifier gates it).

Writes `inputs/local_profile.json` (`modelled` = B / A stage factors, the
four the power check reads) and `profile/raw/`.
"""

import argparse
import json
import statistics
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
BIN = {"A": HERE / "target-a/release/ic_online_fieldops_r770", "B": HERE / "target-b/release/ic_online_fieldops2_r770"}
RAW = HERE / "profile" / "raw"
OUT = HERE / "inputs" / "local_profile.json"


def run(script, side, seed, tag, cpu):
    out = RAW / tag
    proc = subprocess.run(["sh", str(HERE / "profile" / script), str(BIN[side]), str(seed), str(out),
                           "taskset", "-c", str(cpu)], capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit("%s failed: %s" % (tag, proc.stderr[-400:]))
    summary = json.loads(Path(str(out) + ".stdout.jsonl").read_text().splitlines()[-1])
    return summary


def stages(s):
    t = s["timing_ms"]
    return {"index_build": t["index_build"], "scan_selftest": s["scan_order_selftest"]["ms"],
            "online": t["target_median"], "rank_stage": t["rank_stage"], "process_total": t["process_total"]}


def identity(s):
    return {"base_hash": s["base_hash"], "index_digest": {k: v for k, v in s["index_digest"].items() if k != "accounting"},
            "rank_relations_blake3": s["rank_relations_blake3"], "rank_attempt_probes": s["rank_attempt_probes"],
            "rank_root_calls_total": s["rank_root_calls_total"], "stored_states": s["stored_states"],
            "root_table_slots": s["root_table_slots"], "scan_order_selftest_bijection": s["scan_order_selftest"]["bijection"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cold-rounds", type=int, default=4)
    parser.add_argument("--rank-rounds", type=int, default=3)
    parser.add_argument("--cpu", type=int, default=2)
    args = parser.parse_args()
    RAW.mkdir(exist_ok=True)
    cold, rank, same = {"A": [], "B": []}, {"A": [], "B": []}, {"cold": True, "rank": True}
    for kind, script, seed, rounds, store in (("cold", "run_cold.sh", 7, args.cold_rounds, cold),
                                              ("rank", "run_rank.sh", 1501, args.rank_rounds, rank)):
        for n in range(1, rounds + 1):
            pair = {}
            for side in ("A", "B"):
                pair[side] = run(script, side, seed, "r1-%s-%s-%d" % (kind, side, n), args.cpu)
                store[side].append(stages(pair[side]))
                print(kind, n, side, json.dumps(store[side][-1]), flush=True)
            if identity(pair["A"]) != identity(pair["B"]):
                same[kind] = False
                print("IDENTITY DIFFERS", kind, n, flush=True)

    def mean(rows, key):
        return statistics.mean(r[key] for r in rows)

    means = {"cold_process": {s: mean(cold[s], "process_total") for s in "AB"}}
    for key, store in (("index_build", cold), ("scan_selftest", cold), ("online", cold), ("rank_stage", rank)):
        means[key] = {s: mean(store[s], key) for s in "AB"}
    factors = {"index_build_factor": means["index_build"]["B"] / means["index_build"]["A"],
               "selftest_factor": means["scan_selftest"]["B"] / means["scan_selftest"]["A"],
               "rank_stage_factor": means["rank_stage"]["B"] / means["rank_stage"]["A"],
               "online_factor": means["online"]["B"] / means["online"]["A"]}
    record = {"label": ("LOCAL DIAGNOSTIC: shared cloud-agent VM, one pinned CPU (taskset -c %d); ranks and sizes "
                        "only, not evidence" % args.cpu),
              "source": ("profile/run_local_profile.py: A = ic_online_fieldops_r770 (online/), B = "
                         "ic_online_fieldops2_r770 (online-b/), both +pclmulqdq, fresh process each, alternating A "
                         "then B; cold %d rounds (seed 7), rank %d rounds (rank seed 1501); raw summaries in "
                         "profile/raw/" % (args.cold_rounds, args.rank_rounds)),
              "identities": {"cold_layout_and_index_digests_equal_A_B": same["cold"],
                             "rank_relations_probes_roots_equal_A_B": same["rank"]},
              "means_ms": means, "modelled": factors,
              "rounds": {"cold": cold, "rank": rank},
              "notes": ["online is timing_ms.target_median of the cold process (one target); the Tier 1 rows use "
                        "the target record's online_ms."]}
    OUT.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"modelled": factors, "identities": record["identities"]}, sort_keys=True))
    return 0 if all(same.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
