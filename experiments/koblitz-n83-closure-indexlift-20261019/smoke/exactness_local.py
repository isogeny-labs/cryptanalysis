#!/usr/bin/env python3
"""Local exactness diagnostic (cloud-agent VM; never timing evidence).

Runs the closure + index-lift producer directly, with `arm.py`'s
environment, two processes at a time:

* `cold`: Q0 with each base's verified cached table, one process per base
  (K600, M38, M10) and index canonicalizer (`selected`, `lift`). Required:
  - K600, both canonicalizers: B's logical-state and table-map digests, the
    index-lift protocol's frozen layout digests (`d8cfe443...`,
    `5f53764e...`) and B's archived Q0 identity (1,987,852 probes): the
    composed producer is the index-lift producer on B's header;
  - M38 and M10: the closure protocol's frozen logical-state and table-map
    digests, root entries and Q0 identity, with both canonicalizers; and one
    layout digest pair per base across the two canonicalizers (these pairs
    are frozen into `protocol.json`, `online.bases.<base>.layout_digest`).
* `rank`: two archived Tier 1 rank processes reproduced with
  `KIC_INDEX_CANON=lift`:
  - kM38 of the closure run 39305259093, block K1 (rank seed 801, point s000
    of `closure-cold-v1`), on the M38 header;
  - kPI of the index-lift run 39290913632, block K1 (rank seed 401, point
    s000 of `indexlift-cold-v1`), on B's header;
  each compared field by field with the archived row (relation digest,
  per-attempt probe vector, root-call total, point-addition counters, frame
  builds, target relation, scalar, probes, index and layout digests where
  archived) and its written table with the base's frozen verified table.

Writes `../inputs/local_layout_test.json` (cold: a frozen input of
`make_protocol.py`, which takes each closure base's layout digests from it)
or `exactness_rank_local.json` next to this file (rank); times are
diagnostics only.
"""

import argparse
import base64
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
CLOSURE_PROTOCOL = json.loads((EXP / "inputs/parent_closure_protocol.json").read_text())
INDEXLIFT_PROTOCOL = json.loads((EXP.parent / "koblitz-n83-indexlift-20261019/protocol.json").read_text())
B_LOG_TABLE = (EXP.parent / "koblitz-single-target-n83-tier1-20261014/tier1_github_38523707244/precompute/"
               "factor_logs_n83_K600.json")
BASES = {
    "K600": (EXP / "snapshots/r770/experiments/koblitz-single-target-n83-20261006/base_n83_K600.jsonl", B_LOG_TABLE),
    "M38": (EXP / "snapshots/closure/base_n83_closure_M38.jsonl", EXP / "inputs/factor_logs_n83_closure_M38.json"),
    "M10": (EXP / "snapshots/closure/base_n83_closure_M10.jsonl", EXP / "inputs/factor_logs_n83_closure_M10.json"),
}
Q0 = json.loads((EXP.parent / "koblitz-single-target-n83-tier1-20261014/inputs/targets.json").read_text())["q0"]["point"]
ENV = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "RAYON_NUM_THREADS": "1", "KIC_THREADS": "1",
       "KIC_RHO_THREADS": "1", "OMP_NUM_THREADS": "1", "KIC_RANK_THREADS": "1", "KIC_TARGET_THREADS": "1",
       "KIC_INDEX_DIGEST": "1", "KIC_ROOT_TABLE": "compact", "KIC_STATE_FOLD": "1", "KIC_FOLD_PLANT": "0",
       "KIC_SCAN_SELFTEST": "full", "KIC_TARGET_CANON": "lift", "KIC_SCAN_ORDER": "feistel",
       "KIC_PROBE_PIPELINE": "prefetch"}
RANK_ENV = {"KIC_RANK_CANON": "lift", "KIC_RANK_ORDER": "feistel", "KIC_RANK_PROBE": "target",
            "KIC_RANK_SOLVE": "frame"}
DIGEST_KEYS = ("logical_states_blake3", "table_map_sum64", "table_map_xor64", "table_entries")
LAYOUT_KEYS = ("stored_states_blake3", "table_slots_blake3")


def rows(text):
    out = []
    for line in text.splitlines():
        if line.strip().startswith("{"):
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def launch(binary, folder, name, base, point, seed, extra):
    work = folder / name
    work.mkdir()
    (work / "points.jsonl").write_text(json.dumps([str(v) for v in point]) + "\n")
    env = dict(ENV, **extra)
    if "KIC_LOG_TABLE_OUT" in env:
        env["KIC_LOG_TABLE_OUT"] = str(work / "factor_logs.json")
    proc = subprocess.Popen([str(binary), str(BASES[base][0]), str(work / "points.jsonl"), str(seed),
                             str(work / "ic.jsonl")], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True)
    return work, proc


def summarize(work, proc, base, rank):
    stdout, stderr = proc.communicate()
    summary = (rows(stdout) or [{}])[-1]
    record = (rows((work / "ic.jsonl").read_text()) or [{}])[0] if (work / "ic.jsonl").exists() else {}
    out = {"base": base, "returncode": proc.returncode, "stderr_tail": stderr[-600:],
           "index_canonicalizer": summary.get("index_canonicalizer"),
           "index_plant_checked_inputs": summary.get("index_plant_checked_inputs"),
           "scan_order_selftest": summary.get("scan_order_selftest"),
           "index_orbits": summary.get("index_orbits"), "orbit_columns": summary.get("orbit_columns"),
           "closure": summary.get("closure"), "base_hash": summary.get("base_hash"),
           "stored_states": summary.get("stored_states"), "regular_states": summary.get("regular_states"),
           "root_table_entries": summary.get("root_table_entries"),
           "root_table_slots": summary.get("root_table_slots"),
           "index_digest": {k: v for k, v in (summary.get("index_digest") or {}).items() if k != "accounting"},
           "relation": record.get("point_indices"), "scalar": record.get("recovered_scalar"),
           "probes": record.get("probes"), "group_verified": record.get("group_verified"),
           "diagnostic_ms": {"index_build": (summary.get("timing_ms") or {}).get("index_build"),
                             "setup_complete": summary.get("setup_complete_ns", 0) / 1e6,
                             "online": record.get("online_ms"), "cold": summary.get("cold_in_process_ms"),
                             "rank_stage": (summary.get("timing_ms") or {}).get("rank_stage")}}
    if rank:
        frozen = json.loads(BASES[base][1].read_text())["logs"]
        produced = (json.loads((work / "factor_logs.json").read_text())["logs"]
                    if (work / "factor_logs.json").exists() else None)
        out.update({"rank": summary.get("rank"), "rank_attempts": summary.get("rank_attempts"),
                    "rank_failures": summary.get("rank_failures"),
                    "rank_rows_without_gain": summary.get("rank_rows_without_gain"),
                    "rank_relations_blake3": summary.get("rank_relations_blake3"),
                    "rank_attempt_probes": summary.get("rank_attempt_probes"),
                    "rank_root_calls_total": summary.get("rank_root_calls_total"),
                    "rank_padd": {k[len("rank_padd_"):]: v for k, v in summary.items() if k.startswith("rank_padd_")},
                    "rank_frame": {k[len("rank_frame_"):]: v for k, v in summary.items()
                                   if k.startswith("rank_frame_")},
                    "logs_equal_frozen_table": produced == frozen})
    return out


def archived_row(panel, arm, segment):
    for line in (panel / "runs.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row["arm"] == arm and row["segment"] == segment:
            text = (panel / row["stdout_file"]).read_text()
            raw = json.loads(base64.b64decode([l[8:] for l in text.splitlines() if l.startswith("raw_b64=")][0]))
            summary = next(r for r in raw["records"] if r.get("kind") == "compact_orbit_dlp_summary")
            target = raw["records"][0]
            return {"rank_relations_blake3": summary["rank_relations_blake3"],
                    "rank_attempt_probes": summary["rank_attempt_probes"],
                    "rank_root_calls_total": summary["rank_root_calls_total"],
                    "rank_padd": {k[len("rank_padd_"):]: v for k, v in summary.items() if k.startswith("rank_padd_")},
                    "rank_frame": {k[len("rank_frame_"):]: v for k, v in summary.items()
                                   if k.startswith("rank_frame_")},
                    "index_digest": {k: v for k, v in (summary.get("index_digest") or {}).items()
                                     if k != "accounting"},
                    "relation": target.get("point_indices"), "scalar": target.get("recovered_scalar"),
                    "probes": target.get("probes"), "seed": row["seed"], "point": raw["point"],
                    "panel": raw["panel"]}
    raise ValueError("no archived %s row in %s" % (arm, segment))


def run_pairs(jobs, binary, folder):
    """jobs: [(name, base, point, seed, extra, rank)], two at a time."""
    result = {}
    for i in range(0, len(jobs), 2):
        launched = [(name, base, rank, launch(binary, folder, name, base, point, seed, extra))
                    for name, base, point, seed, extra, rank in jobs[i:i + 2]]
        for name, base, rank, (work, proc) in launched:
            result[name] = summarize(work, proc, base, rank)
    return result


def cold(binary, folder):
    jobs = [("%s_%s" % (base, canon), base, Q0, 7, {"KIC_INDEX_CANON": canon, "KIC_LOG_TABLE_IN": str(BASES[base][1])},
             False) for base in BASES for canon in ("selected", "lift")]
    result = run_pairs(jobs, binary, folder)
    k600 = INDEXLIFT_PROTOCOL["online"]
    checks, layout = {}, {}
    for base in BASES:
        spec = k600 if base == "K600" else CLOSURE_PROTOCOL["online"]["bases"][base]
        want_q0 = k600["q0_identity"] if base == "K600" else spec["q0_identity"]
        procs = [result["%s_%s" % (base, c)] for c in ("selected", "lift")]
        checks[base] = {
            "exit_0_and_group_verified": all(p["returncode"] == 0 and p["group_verified"] is True for p in procs),
            "index_canonicalizers": [p["index_canonicalizer"] for p in procs] == ["selected", "lift"],
            "no_planted_index_check": all(p["index_plant_checked_inputs"] == 0 for p in procs),
            "index_digest_equals_frozen_parent": all(p["index_digest"].get(k) == spec["index_digest"][k]
                                                     for p in procs for k in DIGEST_KEYS),
            "root_table_entries_equal_frozen_parent": all(p["root_table_entries"] == spec["root_table_entries"]
                                                          for p in procs),
            "q0_equals_frozen_parent": all(p["relation"] == want_q0["relation"] and str(p["scalar"]) == want_q0["scalar"]
                                           and p["probes"] == want_q0["probes_folded"] for p in procs),
            "one_layout_across_canonicalizers": len({json.dumps([p["index_digest"].get(k) for k in LAYOUT_KEYS])
                                                     for p in procs}) == 1,
        }
        if base == "K600":
            checks[base]["layout_equals_indexlift_frozen"] = all(
                p["index_digest"].get(k) == k600["layout_digest"][k] for p in procs for k in LAYOUT_KEYS)
        layout[base] = {k: procs[1]["index_digest"].get(k) for k in LAYOUT_KEYS}
    return result, checks, layout


def rank(binary, folder, closure_panel, indexlift_panel):
    archived = {"M38": archived_row(closure_panel, "kM38", "K1"), "K600": archived_row(indexlift_panel, "kPI", "K1")}
    jobs = []
    for base, row in archived.items():
        jobs.append(("rank_%s" % base, base, [int(v) for v in row["point"]], row["seed"],
                     dict(RANK_ENV, KIC_INDEX_CANON="lift", KIC_LOG_TABLE_OUT="x"), True))
    result = run_pairs(jobs, binary, folder)
    checks = {}
    for base, row in archived.items():
        p = result["rank_%s" % base]
        fields = ("rank_relations_blake3", "rank_attempt_probes", "rank_root_calls_total", "rank_padd",
                  "rank_frame", "relation", "scalar", "probes")
        eq = {k: p[k] == row[k] for k in fields}
        eq["index_digest_archived_keys"] = all(p["index_digest"].get(k) == v for k, v in row["index_digest"].items())
        eq["logs_equal_frozen_table"] = p["logs_equal_frozen_table"]
        eq["full_rank_no_failures"] = (p["rank"] == p["orbit_columns"] and p["rank_failures"] == 0 and
                                       p["rank_rows_without_gain"] == 0)
        checks[base] = {"archived": {"run": 39305259093 if base == "M38" else 39290913632,
                                     "arm": "kM38" if base == "M38" else "kPI", "segment": "K1",
                                     "seed": row["seed"], "panel": row["panel"]},
                        "equal": eq}
        p["rank_attempt_probes_total"] = sum(p.pop("rank_attempt_probes") or [])
    return result, checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("what", choices=("cold", "rank"))
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--closure-panel", type=Path, help="rank: run 39305259093's panel directory")
    parser.add_argument("--indexlift-panel", type=Path,
                        default=EXP.parent / "koblitz-n83-indexlift-20261019/run_github_39290913632/panel")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="n83-cli-smoke-") as tmp:
        folder = Path(tmp)
        if args.what == "cold":
            result, checks, layout = cold(args.binary, folder)
            out = {"layout_digest_lift": layout}
        else:
            result, checks = rank(args.binary, folder, args.closure_panel, args.indexlift_panel)
            out = {}
    out.update({"what": args.what, "host": "cloud-agent VM (diagnostic only; two processes at a time)",
                "processes": result, "checks": checks,
                "all_pass": all(v is True for c in checks.values()
                                for v in (c["equal"].values() if "equal" in c else c.values()))})
    path = (EXP / "inputs" / "local_layout_test.json") if args.what == "cold" else HERE / "exactness_rank_local.json"
    path.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "processes"}, sort_keys=True))


if __name__ == "__main__":
    sys.exit(main())
