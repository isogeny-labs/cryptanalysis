#!/usr/bin/env python3
"""Local exactness (and diagnostic timing) of the rank stage: parent vs rank-finder producer.

Runs both binaries, alternating, as fresh pinned processes with `arm.py`'s
rank-arm environment (KIC_RANK_CANON=lift, KIC_RANK_ORDER=feistel,
KIC_RANK_PROBE=target, KIC_RANK_SOLVE=frame or frame_plant, compact table,
folded lift index, full self-test, no cached table) on one base, for each
seed, and one public point. Per seed it requires the two processes to agree
on every rank-stage identity (relation digest, per-attempt probe vector,
root calls, probes, counters, rows without gain), on the written factor-log
table (and that it equals the base's frozen table), on the layout and
index digests and on the target's relation, probes and scalar. Timings are
diagnostics of a shared cloud-agent VM only.
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
BASE_ENV = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "RAYON_NUM_THREADS": "1",
            "KIC_THREADS": "1", "KIC_RHO_THREADS": "1", "OMP_NUM_THREADS": "1"}
IDENTITY = ("rank_relations_blake3", "rank_attempt_probes", "rank_root_calls_total", "rank_probes_total",
            "rank_rows_without_gain", "rank_attempts", "rank_relations", "rank_failures",
            "rank_padd_fallback_states", "rank_padd_irregular_inputs", "rank_padd_resolved_hits",
            "rank_padd_swapped_pairs", "rank_padd_plant_checked_inputs", "rank_frame_builds",
            "rank_skipped_symmetric_states", "index_digest", "root_table_entries", "stored_states",
            "regular_states")
TARGET = ("point_indices", "probes", "recovered_scalar", "filter_passes", "skipped_symmetric_states")


def rows(text):
    out = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def run(binary, base, point, seed, solve, cpu, folder):
    target = folder / "points.jsonl"
    target.write_text(json.dumps([str(v) for v in point], separators=(",", ":")) + "\n")
    out = folder / "ic.jsonl"
    logs = folder / "factor_logs.json"
    for path in (out, logs):
        if path.exists():
            path.unlink()
    env = dict(BASE_ENV, KIC_RANK_THREADS="1", KIC_TARGET_THREADS="1", KIC_INDEX_DIGEST="1",
               KIC_ROOT_TABLE="compact", KIC_STATE_FOLD="1", KIC_FOLD_PLANT="0", KIC_INDEX_CANON="lift",
               KIC_SCAN_SELFTEST="full", KIC_TARGET_CANON="lift", KIC_SCAN_ORDER="feistel",
               KIC_PROBE_PIPELINE="prefetch", KIC_LOG_TABLE_OUT=str(logs), KIC_RANK_CANON="lift",
               KIC_RANK_ORDER="feistel", KIC_RANK_PROBE="target", KIC_RANK_SOLVE=solve)
    proc = subprocess.run(["taskset", "-c", str(cpu), str(binary), str(base), str(target), str(seed), str(out)],
                          env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit("%s exit %d: %s" % (binary, proc.returncode, proc.stderr[-2000:]))
    summary = rows(proc.stdout)[-1]
    record = rows(out.read_text())[0]
    return summary, record, json.loads(logs.read_text())["logs"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--derived", type=Path, required=True)
    parser.add_argument("--base-name", required=True)
    parser.add_argument("--seeds", required=True, help="comma-separated rank seeds")
    parser.add_argument("--solve", default="frame")
    parser.add_argument("--cpu", type=int, default=3)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads((HERE / "protocol.json").read_text())
    base = protocol["online"]["bases"][args.base_name]
    frozen = json.loads((HERE / base["factor_log_table"]).read_text())["logs"]
    point = [int(v) for v in json.loads((HERE / "inputs" / "cold_targets.json").read_text())["points"][0]["point"]]
    results = []
    with tempfile.TemporaryDirectory(prefix="n83-rf-exact-") as folder:
        folder = Path(folder)
        for k, seed in enumerate(int(s) for s in args.seeds.split(",")):
            order = [("parent", args.parent), ("derived", args.derived)]
            if k % 2:
                order.reverse()
            got = {}
            for side, binary in order:
                summary, record, logs = run(binary, HERE / base["path"], point, seed, args.solve, args.cpu, folder)
                got[side] = {"identity": {key: summary.get(key) for key in IDENTITY},
                             "target": {key: record.get(key) for key in TARGET},
                             "logs_equal_frozen": logs == frozen,
                             "rank_probe_pipeline": summary.get("rank_probe_pipeline"),
                             "rank_frame_plant_checked_inputs": summary.get("rank_frame_plant_checked_inputs"),
                             "rank_stage_ms": summary["timing_ms"]["rank_stage"],
                             "index_build_ms": summary["timing_ms"]["index_build"],
                             "cold_in_process_ms": summary.get("cold_in_process_ms"),
                             "rank_attempt_ns": summary.get("rank_attempt_ns")}
            same = got["parent"]["identity"] == got["derived"]["identity"] and \
                got["parent"]["target"] == got["derived"]["target"]
            entry = {"seed": seed, "base": args.base_name, "solve": args.solve, "order": [s for s, _ in order],
                     "identical": same, "logs_equal_frozen": [got[s]["logs_equal_frozen"] for s in ("parent", "derived")],
                     "layout_digest_frozen": all(
                         (got[s]["identity"]["index_digest"] or {}).get(key) == base["layout_digest"][key]
                         for s in ("parent", "derived") for key in ("stored_states_blake3", "table_slots_blake3")),
                     "sides": got}
            results.append(entry)
            print(json.dumps({key: entry[key] for key in ("seed", "base", "identical", "logs_equal_frozen",
                                                            "layout_digest_frozen")},
                             separators=(",", ":")),
                  "rank_ms parent %.1f derived %.1f" % (got["parent"]["rank_stage_ms"], got["derived"]["rank_stage_ms"]),
                  flush=True)
            args.out.write_text(json.dumps(results, indent=1, sort_keys=True) + "\n")
    ok = all(e["identical"] and all(e["logs_equal_frozen"]) and e["layout_digest_frozen"] for e in results)
    print("all_identical=%s" % ok)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
