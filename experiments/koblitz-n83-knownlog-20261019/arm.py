#!/usr/bin/env python3
"""Run one known-log arm of the n=83 known-log reference (one point, fresh processes).

`run_schedule.py` launches this wrapper pinned to the execution CPU; both
child processes inherit the affinity and a clean, whitelisted environment.
The baseline arms (cP, kP) and the tuned rho (rT) do not come here: they run
`../koblitz-n83-rankprobe-20261019/arm.py` unchanged, so the IC baseline in
this session is the rank-probe producer exactly as the baseline row measured
it. This wrapper handles only the known-log kinds:

* `ic_knownlog`: cold, nothing cached.
  1. The generator (`knownlog_base`, `knownlog/`) builds the base of the
     arm's K seeded scalar orbits and its factor-log table in a fresh
     process; its own clock (main start .. both files written and synced)
     is `gen_ms`. Both files must hash to the protocol's frozen digests,
     which `check_knownlog.py` verified independently before timing.
  2. The rank-probe producer (the baseline's binary, unchanged) reads that
     header as its retained base and the table through `KIC_LOG_TABLE_IN`:
     it skips the rank stage, checks the table against the base and
     verifies every [L_j]G = R_j before any target work (charged to setup),
     builds the index, then solves the one public point. Its own clock
     (process start .. recovery check) is `cold_ms`.
  The arm's end-to-end cold cost is `e2e_ms = gen_ms + cold_ms`: base and
  log-table generation, base load, index build, log verification,
  self-tests and the one-target online interval. Process launch and this
  wrapper's checks are outside it, as for every other arm.
* `ic_knownlog_planted`: the planted control. The same generation, then one
  log of the table is moved off by one (column `planted_column`) before the
  producer reads it. The producer must refuse it (nonzero exit, the panic
  "factor log <j> does not map G to its representative") and recover no
  scalar. `verified=1` here means the corruption was detected.

The raw output is printed base64-encoded, so the stdout file is the archived
receipt; the last line carries `online_ms=`, `verified=1` and the arm's fields.
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
import arm as reconcile_arm  # noqa: E402  (the reconcile experiment's arm.py: env, parsing)

PHASES = ("target_query_ms", "target_pdp_ms", "target_relation_check_ms",
          "target_descent_ms", "target_recovery_check_ms")
BASE_ENV = dict(reconcile_arm.BASE_ENV)
R = 8569786107849059


def protocol():
    return json.loads((HERE / "protocol.json").read_text())


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def states(k):
    regular = 83 * k * k
    stored = (regular + k) // 2
    slots = 1 << (4 * stored - 1).bit_length()
    return regular, stored, slots


def generate(args, columns, seed, folder):
    header, table = folder / "base.jsonl", folder / "factor_logs.json"
    proc = subprocess.run([str(args.gen_binary), str(columns), str(seed), str(header), str(table)],
                          env=dict(BASE_ENV), capture_output=True, text=True)
    record = (reconcile_arm.rows(proc.stdout) or [{}])[-1]
    return proc, record, header, table


def check(summary, record, base, arm, point):
    k = arm["columns"]
    regular, stored, slots = states(k)
    issues = []
    table = summary.get("factor_log_table") or {}
    if (summary.get("base_hash") != base["base_hash"] or summary.get("targets_solved") != 1 or
            summary.get("targets_failed") != 0 or table.get("source") != "verified_cache" or
            table.get("verified_columns") != k or table.get("rank_stage_skipped") is not True):
        issues.append("ic setup is not the verified known-log table on the generated base")
    if summary.get("orbit_columns") != k or summary.get("factor_base_points") != 166 * k:
        issues.append("orbit columns or base points differ from the arm")
    if summary.get("base_source") != "retained_header":
        issues.append("producer did not read the generated base header")
    if summary.get("regular_states") != regular or summary.get("stored_states") != stored or \
            summary.get("state_fold") is not True:
        issues.append("logical or stored state count or fold flag differs from 83 K^2")
    if summary.get("fold_plant") is not False or summary.get("index_canonicalizer") != "selected":
        issues.append("planted fold or index canonicalizer differs from the baseline's cold path")
    if summary.get("root_table") != "compact" or summary.get("root_table_slots") != slots:
        issues.append("root-table layout or slot count differs")
    if summary.get("root_bloom_enabled") is not False:
        issues.append("KIC_ROOT_BLOOM was on")
    if summary.get("root_table_entries") != base["root_table_entries"]:
        issues.append("root table entries differ from the frozen index of this base")
    digest = summary.get("index_digest") or {}
    for key in ("logical_states_blake3", "table_map_sum64", "table_map_xor64", "table_entries"):
        if digest.get(key) != base["index_digest"][key]:
            issues.append("index digest %s differs from the frozen index of this base" % key)
    if (summary.get("target_canonicalizer"), summary.get("scan_order"), summary.get("probe_pipeline")) != \
            ("lift", "feistel", "prefetch"):
        issues.append("ic ran another target canonicalizer, order or probe pipeline")
    if summary.get("scan_start_override") is not None:
        issues.append("ic ran a start override")
    if (summary.get("scan_order_selftest") or {}).get("bijection") is not True:
        issues.append("feistel self-test missing or failed")
    if summary.get("sparse_canonical_enabled") is not False:
        issues.append("index build did not use the pipeline's full scan")
    if summary.get("rank_attempts") not in (0, None) or summary.get("rank_relations") not in (0, None):
        issues.append("a rank stage ran")
    if record.get("group_verified") is not True or not reconcile_arm.same(record.get("target"), point):
        issues.append("ic record not verified on the supplied point")
    if record.get("root_table") != "compact" or record.get("probe_pipeline") != "prefetch":
        issues.append("target record ran another layout or pipeline")
    online = float(record.get("online_ms") or 0.0)
    phase_sum = sum(float(record.get(name) or 0.0) for name in PHASES)
    if record and abs(phase_sum - online) > 1e-3 * max(1.0, online):
        issues.append("ic five phases do not sum to the online interval")
    if record and not summary.get("setup_complete_ns", 0) < record.get("online_start_ns", 0):
        issues.append("ic setup did not finish before the online interval")
    if record.get("fold_audit_probes") != 0 or record.get("planted_rejected_found") not in (0, None):
        issues.append("audit probes or planted keys in a cold arm")
    return issues


def producer_env(table):
    return dict(BASE_ENV, KIC_RANK_THREADS="1", KIC_TARGET_THREADS="1", KIC_INDEX_DIGEST="1",
                KIC_ROOT_TABLE="compact", KIC_STATE_FOLD="1", KIC_FOLD_PLANT="0", KIC_INDEX_CANON="selected",
                KIC_TARGET_CANON="lift", KIC_SCAN_ORDER="feistel", KIC_PROBE_PIPELINE="prefetch",
                KIC_LOG_TABLE_IN=str(table))


def knownlog(args, point, folder, planted):
    spec = protocol()
    arm = spec["arms"][args.arm]
    base = spec["knownlog"]["bases"][str(arm["columns"])]
    issues = []
    gen_proc, gen, header, table = generate(args, arm["columns"], spec["knownlog"]["base_seed"], folder)
    if gen_proc.returncode != 0 or gen.get("kind") != "knownlog_base_generation":
        issues.append("generator exit %d or no generation record" % gen_proc.returncode)
    digests = {"base_sha256": sha256(header) if header.exists() else None,
               "log_table_sha256": sha256(table) if table.exists() else None}
    if digests["base_sha256"] != base["base_sha256"] or digests["log_table_sha256"] != base["log_table_sha256"] \
            or gen.get("base_hash") != base["base_hash"]:
        issues.append("generated base or log table differs from the independently verified frozen files")
    if planted:
        logs = json.loads(table.read_text())
        column = spec["knownlog"]["planted_column"]
        logs["logs"][column] = str((int(logs["logs"][column]) + 1) % R)
        table = folder / "factor_logs_planted.json"
        table.write_text(json.dumps(logs, separators=(",", ":")) + "\n")
    target = folder / "points.jsonl"
    target.write_text(json.dumps([str(v) for v in point], separators=(",", ":")) + "\n")
    out = folder / "ic.jsonl"
    proc = subprocess.run([str(args.binary), str(header), str(target), str(args.seed), str(out)],
                          env=producer_env(table), capture_output=True, text=True)
    records = reconcile_arm.rows(out.read_text()) if out.exists() else []
    summary = (reconcile_arm.rows(proc.stdout) or [{}])[-1]
    record = records[0] if records else {}
    gen_ms = float(gen.get("gen_ms") or 0.0)
    if planted:
        expected = "factor log %d does not map G to its representative" % spec["knownlog"]["planted_column"]
        refused = proc.returncode != 0 and expected in proc.stderr and not records
        if not refused:
            issues.append("the producer did not refuse the planted factor-log table")
        fields = {"online_ms": 0.0, "gen_ms": gen_ms, "planted_refused": refused,
                  "producer_returncode": proc.returncode, "recovered_scalar": None, "relation": None,
                  "ops": None, "ops_unit": "root_index_probes", **digests}
        return proc, [gen] + records + [summary], issues, fields
    if proc.returncode != 0:
        issues.append("ic exit %d" % proc.returncode)
    if len(records) != 1:
        issues.append("ic emitted %d target records for one point" % len(records))
    issues += check(summary, record, base, arm, point)
    timing = summary.get("timing_ms") or {}
    cold = summary.get("cold_in_process_ms")
    fields = {"online_ms": float(record.get("online_ms") or 0.0),
              "gen_ms": gen_ms, "gen_phases_ms": gen.get("phases_ms"),
              "cold_ms": cold, "e2e_ms": (gen_ms + cold) if isinstance(cold, (int, float)) else None,
              "setup_ms": summary.get("setup_complete_ns", 0) / 1e6,
              "base_load_ms": timing.get("base_load"), "index_ms": timing.get("index_build"),
              "log_verify_ms": timing.get("linear_algebra"),
              "scan_selftest_ms": (summary.get("scan_order_selftest") or {}).get("ms"),
              "rank_stage_ms": timing.get("rank_stage"),
              "peak_rss_bytes": summary.get("peak_rss_bytes"),
              "ops": record.get("probes"), "ops_unit": "root_index_probes",
              "recovered_scalar": record.get("recovered_scalar"),
              "relation": record.get("point_indices"),
              "orbit_columns": arm["columns"], **digests}
    return proc, [gen] + records + [summary], issues, fields


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--kind", required=True, choices=("ic_knownlog", "ic_knownlog_planted"))
    parser.add_argument("--panel", required=True, help="unit id")
    parser.add_argument("--binary", required=True, type=Path, help="the rank-probe producer")
    parser.add_argument("--gen-binary", required=True, type=Path, help="knownlog_base")
    parser.add_argument("--point", required=True, help="x,y decimal")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    point = [int(v) for v in args.point.split(",")]
    with tempfile.TemporaryDirectory(prefix="n83-knownlog-arm-") as folder:
        proc, raw, issues, fields = knownlog(args, point, Path(folder), args.kind == "ic_knownlog_planted")
    raw_bytes = json.dumps({"arm": args.arm, "kind": args.kind, "panel": args.panel,
                            "point": [str(v) for v in point], "seed": args.seed,
                            "returncode": proc.returncode, "records": raw,
                            "stderr_tail": proc.stderr[-4000:], "issues": issues, "fields": fields},
                           sort_keys=True, separators=(",", ":")).encode()
    print("raw_b64=" + base64.b64encode(raw_bytes).decode())
    if args.kind == "ic_knownlog_planted":
        verified = not issues and fields.get("planted_refused") is True
    else:
        verified = not issues and fields.get("recovered_scalar") is not None
    line = {"online_ms": "%.6f" % fields["online_ms"], "verified": "1" if verified else "0",
            "arm": args.arm, "panel": args.panel, "target_sha256": reconcile_arm.target_sha256(point),
            "recovered_scalar": str(fields.get("recovered_scalar")),
            "ops": str(fields.get("ops")), "ops_unit": fields.get("ops_unit"),
            "gen_ms": "%.6f" % float(fields.get("gen_ms") or 0.0),
            "e2e_ms": "%.6f" % float(fields.get("e2e_ms") or 0.0),
            "raw_result_sha256": hashlib.sha256(raw_bytes).hexdigest(), "issues": str(len(issues))}
    print(" ".join("%s=%s" % item for item in line.items()))
    for issue in issues:
        print("issue: " + issue, file=sys.stderr)
    sys.exit(0 if verified else 1)


if __name__ == "__main__":
    main()
