#!/usr/bin/env python3
"""Run one frozen arm of the n=83 index-build experiment (one process, one point).

`koblitz-n83-closure-indexlift-20261019`'s `arm.py` (PR #997, on main) with
two changes for `koblitz-n83-indexbuild-20261020`, marked in the code:

* the summary's `index_build_pipeline` must equal the arm's: absent (None)
  for the row's producer `ic_online_closure_indexlift_r770`, the derived
  pipeline name for `ic_online_indexbuild_r770`. A row therefore names the
  index build it ran, apart from its binary digest;
* the planted index check: an arm with `index_canon = lift_plant` must have
  checked every index root against the selected canonicalizer
  (`index_plant_checked_inputs` = 2 x stored states); every other arm must
  have checked none (0, the parent's gate).

The rest is the parent's text:

`run_schedule.py` launches this wrapper pinned to the execution CPU; the
producer inherits the affinity and a clean, whitelisted environment. The
producer's own clocks are the metrics; the wrapper's start-up, input writing
and checks are outside them. The raw producer output is printed
base64-encoded so the stdout file is the archived receipt; the last line
carries `online_ms=`, `verified=1`, the arm's fields and the SHA-256 of the
raw record.

`koblitz-n83-closure-20261019`'s `arm.py` (commit 3761fd260) with the
index-lift producer's runtime options and gates added:

* every IC arm runs the closure + index-lift producer (`online/`: the
  index-lift producer with the closure's four replacements; on B's header it
  is the index-lift producer) with the arm's `index_canon`
  (`KIC_INDEX_CANON`; `lift` in every arm of this experiment, the index-lift
  row's index build) and `scan_selftest` (`KIC_SCAN_SELFTEST=full`, the
  default);
* besides the closure wrapper's per-base checks (base hash, columns, orbits
  in the root index, logical and stored states, slots, root entries,
  logical-state blake3 and table-map digests), every IC process must
  reproduce its base's frozen LAYOUT digests (`stored_states_blake3`,
  `table_slots_blake3`; index-lift's gate: B's values from the index-lift
  protocol for K600, the local layout test's for M38 and M10), check no
  index root against the selected canonicalizer
  (`index_plant_checked_inputs` 0) and record the full scan self-test.

Every IC arm also runs lift_scan target keys (`KIC_TARGET_CANON=lift`), the
Feistel order, the prefetch pipeline, the 16-byte compact table over the
folded index and `KIC_INDEX_DIGEST=1` (digests after the target, outside
every timed interval). Kinds:

* `ic_cold`: ONE public point in a fresh process with the base's verified
  cached factor-log table: cold = setup (process start to setup complete:
  base, normal basis, root index, log-table load and verification, Feistel
  self-tests) + the one-target online interval.
* `ic_rank`: the same producer with NO cached table: the rank stage runs in
  process (`KIC_RANK_SOLVE` = the arm's `rank_solve`, `frame` or
  `frame_plant`; rank seed = the run seed), writes its factor-log table
  (`KIC_LOG_TABLE_OUT`), which must equal the base's frozen, independently
  verified table log for log, then solves one public point.
* `rho_tuned`: A's configured rho worker (Fold/64/DP6) through the reconcile
  experiment's own runner function, unchanged, on one point.
"""

import argparse
import base64
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECONCILE = HERE.parent / "koblitz-n83-reconcile-20261014"
sys.path.insert(0, str(RECONCILE))
import arm as reconcile_arm  # noqa: E402  (the reconcile experiment's arm.py)

PHASES = ("target_query_ms", "target_pdp_ms", "target_relation_check_ms",
          "target_descent_ms", "target_recovery_check_ms")
BASE_ENV = dict(reconcile_arm.BASE_ENV)


def protocol():
    return json.loads((HERE / "protocol.json").read_text())


def check(summary, record, spec, arm, point, rank):
    issues = []
    table = summary.get("factor_log_table") or {}
    want_source = "in_process_rank" if rank else "verified_cache"
    if (summary.get("base_hash") != spec["base_hash"] or summary.get("targets_solved") != 1 or
            summary.get("targets_failed") != 0 or table.get("source") != want_source or
            table.get("verified_columns") != spec["orbit_columns"] or
            summary.get("orbit_columns") != spec["orbit_columns"]):
        issues.append("ic setup is not the expected factor-log source on the frozen base")
    if summary.get("index_orbits") != spec["index_orbits"] or \
            summary.get("factor_base_points") != spec["factor_base_points"]:
        issues.append("orbits in the root index or base points differ from the base")
    closure = summary.get("closure")
    if (closure or {}).get("norm_cap") != spec.get("norm_cap"):
        issues.append("closure block differs from the base")
    if summary.get("regular_states") != spec["regular_states"]:
        issues.append("logical state count differs from 83 * orbits^2")
    if summary.get("stored_states") != spec["stored_states_folded"] or summary.get("state_fold") is not True:
        issues.append("stored state count or fold flag differs from the base")
    if summary.get("fold_plant") is not False:
        issues.append("planted fold flag was on")
    if summary.get("index_canonicalizer") != arm["index_canon"]:
        issues.append("index canonicalizer differs from the arm")
    # koblitz-n83-indexbuild-20261020: the planted index check runs in the lift_plant arm only, on every root.
    plant_checks = 2 * spec["stored_states_folded"] if arm["index_canon"] == "lift_plant" else 0
    if summary.get("index_plant_checked_inputs") != plant_checks:
        issues.append("index roots checked against the selected canonicalizer differ from the arm "
                      "(%s, want %d)" % (summary.get("index_plant_checked_inputs"), plant_checks))
    # koblitz-n83-indexbuild-20261020: the index build the producer reports must be the arm's.
    if summary.get("index_build_pipeline") != arm.get("index_build_pipeline"):
        issues.append("index build pipeline differs from the arm")
    if (summary.get("scan_order_selftest") or {}).get("mode") != arm["scan_selftest"]:
        issues.append("scan-order self-test mode differs from the arm")
    if summary.get("root_table") != arm["table"] or summary.get("root_table_slots") != spec["root_table_slots"]:
        issues.append("root-table layout or slot count differs from the arm")
    if summary.get("root_bloom_enabled") is not False:
        issues.append("KIC_ROOT_BLOOM was on")
    if summary.get("root_table_entries") != spec["root_table_entries"]:
        issues.append("root table entries differ from the base's frozen index")
    digest = summary.get("index_digest") or {}
    for key in ("logical_states_blake3", "table_map_sum64", "table_map_xor64", "table_entries"):
        if digest.get(key) != spec["index_digest"][key]:
            issues.append("index digest %s differs from the base's frozen index" % key)
    for key in ("stored_states_blake3", "table_slots_blake3"):
        if digest.get(key) != spec["layout_digest"][key]:
            issues.append("layout digest %s differs from the base's frozen layout" % key)
    if (summary.get("target_canonicalizer"), summary.get("scan_order"), summary.get("probe_pipeline")) != \
            ("lift", "feistel", "prefetch"):
        issues.append("ic ran another target canonicalizer, order or probe pipeline")
    if summary.get("scan_start_override") is not None:
        issues.append("ic ran a start override")
    if (summary.get("scan_order_selftest") or {}).get("bijection") is not True:
        issues.append("feistel self-test missing or failed")
    if summary.get("sparse_canonical_enabled") is not False:
        issues.append("index build did not use the pipeline's full scan")
    if rank:
        if summary.get("rank") != spec["orbit_columns"]:
            issues.append("rank stage did not reach full rank")
        if summary.get("rank_failures") != 0 or summary.get("rank_attempts") != summary.get("rank_relations"):
            issues.append("rank stage had attempts without a relation")
        if (summary.get("rank_canonicalizer"), summary.get("rank_order"), summary.get("rank_probe")) != \
                (arm["rank_canon"], arm["rank_order"], arm["rank_probe"]):
            issues.append("rank stage ran another canonicalizer, order or probe loop")
        if len(summary.get("rank_attempt_ns") or []) != summary.get("rank_attempts") or \
                len(summary.get("rank_attempt_probes") or []) != summary.get("rank_attempts"):
            issues.append("rank attempt records incomplete")
        if summary.get("rank_solve") != arm["rank_solve"]:
            issues.append("rank stage ran another partner-root solve")
        counters = ("rank_padd_fallback_states", "rank_padd_irregular_inputs", "rank_padd_resolved_hits",
                    "rank_padd_swapped_pairs", "rank_padd_plant_checked_inputs", "rank_frame_builds",
                    "rank_frame_plant_checked_inputs")
        if any(not isinstance(summary.get(key), int) for key in counters):
            issues.append("rank-cut or frame counters missing")
        elif summary["rank_padd_plant_checked_inputs"] != 0:
            issues.append("the rank-cut planted check ran")
        elif summary["rank_frame_builds"] != summary.get("rank_attempts"):
            issues.append("the frame loop did not build exactly one frame per attempt")
        elif arm["rank_solve"] == "frame" and summary["rank_frame_plant_checked_inputs"] != 0:
            issues.append("the planted check ran outside the planted arm")
        elif arm["rank_solve"] == "frame_plant" and summary["rank_frame_plant_checked_inputs"] <= 0:
            issues.append("the planted arm checked no input")
    if record.get("group_verified") is not True or not reconcile_arm.same(record.get("target"), point):
        issues.append("ic record not verified on the supplied point")
    if record.get("root_table") != arm["table"] or record.get("probe_pipeline") != "prefetch":
        issues.append("target record ran another layout or pipeline")
    online = float(record.get("online_ms") or 0.0)
    phase_sum = sum(float(record.get(name) or 0.0) for name in PHASES)
    if record and abs(phase_sum - online) > 1e-3 * max(1.0, online):
        issues.append("ic five phases do not sum to the online interval")
    if record and not summary.get("setup_complete_ns", 0) < record.get("online_start_ns", 0):
        issues.append("ic setup did not finish before the online interval")
    if record.get("fold_audit_probes") != 0:
        issues.append("audit probes outside the planted arm")
    if record.get("planted_rejected_found") not in (0, None):
        issues.append("a filter-rejected key was found")
    return issues


def ic(args, point, folder, rank):
    arm = protocol()["arms"][args.arm]
    spec = protocol()["online"]["bases"][arm["base"]]
    target = folder / "points.jsonl"
    target.write_text(json.dumps([str(v) for v in point], separators=(",", ":")) + "\n")
    out = folder / "ic.jsonl"
    env = dict(BASE_ENV, KIC_RANK_THREADS="1", KIC_TARGET_THREADS="1", KIC_INDEX_DIGEST="1",
               KIC_ROOT_TABLE=arm["table"], KIC_STATE_FOLD="1", KIC_FOLD_PLANT="0",
               KIC_INDEX_CANON=arm["index_canon"], KIC_SCAN_SELFTEST=arm["scan_selftest"],
               KIC_TARGET_CANON="lift", KIC_SCAN_ORDER="feistel", KIC_PROBE_PIPELINE="prefetch")
    logs_out = folder / "factor_logs.json"
    if rank:
        env.update(KIC_LOG_TABLE_OUT=str(logs_out), KIC_RANK_CANON=arm["rank_canon"],
                   KIC_RANK_ORDER=arm["rank_order"], KIC_RANK_PROBE=arm["rank_probe"],
                   KIC_RANK_SOLVE=arm["rank_solve"])
    else:
        env["KIC_LOG_TABLE_IN"] = str(args.log_table)
    proc = subprocess.run([str(args.binary), str(args.base), str(target), str(args.seed), str(out)],
                          env=env, capture_output=True, text=True)
    records = reconcile_arm.rows(out.read_text()) if out.exists() else []
    summary = (reconcile_arm.rows(proc.stdout) or [{}])[-1]
    record = records[0] if records else {}
    issues = []
    if proc.returncode != 0:
        issues.append("ic exit %d" % proc.returncode)
    if len(records) != 1:
        issues.append("ic emitted %d target records for one point" % len(records))
    issues += check(summary, record, spec, arm, point, rank)
    logs_equal = None
    if rank:
        archived = json.loads(Path(args.log_table).read_text())["logs"]
        produced = json.loads(logs_out.read_text())["logs"] if logs_out.exists() else None
        logs_equal = produced == archived
        if not logs_equal:
            issues.append("rank-stage factor logs differ from the base's frozen verified table")
    timing = summary.get("timing_ms") or {}
    fields = {"online_ms": float(record.get("online_ms") or 0.0),
              "setup_ms": summary.get("setup_complete_ns", 0) / 1e6,
              "cold_ms": summary.get("cold_in_process_ms"),
              "rank_stage_ms": timing.get("rank_stage"),
              "index_ms": timing.get("index_build"),
              "filter_build_ms": summary.get("root_filter_build_ms"),
              "scan_selftest_ms": (summary.get("scan_order_selftest") or {}).get("ms"),
              "index_plant_checked_inputs": summary.get("index_plant_checked_inputs"),
              "index_canonicalizer": summary.get("index_canonicalizer"),
              "index_build_pipeline": summary.get("index_build_pipeline"),
              "layout_digest": {key: (summary.get("index_digest") or {}).get(key)
                                for key in ("stored_states_blake3", "table_slots_blake3")},
              "peak_rss_bytes": summary.get("peak_rss_bytes"),
              "ops": record.get("probes"), "ops_unit": "root_index_probes",
              "recovered_scalar": record.get("recovered_scalar"),
              "relation": record.get("point_indices"),
              "skipped_states": record.get("skipped_symmetric_states"),
              "audit_probes": record.get("fold_audit_probes"),
              "filter_passes": record.get("filter_passes"),
              "base": arm["base"],
              "rank_relations_blake3": summary.get("rank_relations_blake3") if rank else None,
              "rank_rows_without_gain": summary.get("rank_rows_without_gain") if rank else None,
              "root_table_entries": summary.get("root_table_entries"),
              "rank_root_calls_total": summary.get("rank_root_calls_total") if rank else None,
              "rank_solve": summary.get("rank_solve") if rank else None,
              "rank_padd": ({key[len("rank_padd_"):]: summary.get(key) for key in summary
                             if key.startswith("rank_padd_")} if rank else None),
              "rank_frame": ({key[len("rank_frame_"):]: summary.get(key) for key in summary
                              if key.startswith("rank_frame_")} if rank else None),
              "logs_equal_archived": logs_equal}
    raw = records + [summary]
    if rank and logs_out.exists():
        raw.append({"factor_log_table_written_sha256": hashlib.sha256(logs_out.read_bytes()).hexdigest()})
    return proc, raw, issues, fields


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--kind", required=True, choices=("ic_cold", "ic_rank", "rho_tuned"))
    parser.add_argument("--panel", required=True, help="unit id")
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--point", required=True, help="x,y decimal")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--base", type=Path)
    parser.add_argument("--log-table", type=Path)
    args = parser.parse_args()
    point = [int(v) for v in args.point.split(",")]
    with tempfile.TemporaryDirectory(prefix="n83-cli-arm-") as folder:
        if args.kind == "rho_tuned":
            proc, raw, issues, fields = reconcile_arm.rho_strong_g(args, point, Path(folder))
            fields.setdefault("relation", None)
        else:
            proc, raw, issues, fields = ic(args, point, Path(folder), args.kind == "ic_rank")
    raw_bytes = json.dumps({"arm": args.arm, "kind": args.kind, "panel": args.panel,
                            "point": [str(v) for v in point], "seed": args.seed,
                            "returncode": proc.returncode, "records": raw,
                            "stderr_tail": proc.stderr[-4000:], "issues": issues, "fields": fields},
                           sort_keys=True, separators=(",", ":")).encode()
    print("raw_b64=" + base64.b64encode(raw_bytes).decode())
    verified = not issues and fields.get("recovered_scalar") is not None
    line = {"online_ms": "%.6f" % fields["online_ms"], "verified": "1" if verified else "0",
            "arm": args.arm, "panel": args.panel, "target_sha256": reconcile_arm.target_sha256(point),
            "recovered_scalar": str(fields.get("recovered_scalar")),
            "ops": str(fields.get("ops")), "ops_unit": fields.get("ops_unit"),
            "setup_ms": "%.6f" % float(fields.get("setup_ms") or 0.0),
            "raw_result_sha256": hashlib.sha256(raw_bytes).hexdigest(), "issues": str(len(issues))}
    print(" ".join("%s=%s" % item for item in line.items()))
    for issue in issues:
        print("issue: " + issue, file=sys.stderr)
    sys.exit(0 if verified else 1)


if __name__ == "__main__":
    main()
