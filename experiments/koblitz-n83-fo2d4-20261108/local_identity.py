#!/usr/bin/env python3
"""Local identity test: both producers on the frozen D4 base (a diagnostic before freezing; not timing evidence).

Runs the field-ops producer (`ic_online_fieldops_r770`, side A) and the field-ops-2
producer (`ic_online_fieldops2_r770`, R1, side B) on Q0 with arm.py's exact
environment, on the D4 closure base, and requires that every process of BOTH
binaries reproduces the D4 identity that `koblitz-n83-k4c400-20261107` froze (its
`protocol.json online.bases.D4`; that identity was reproduced by every process
of the archived Tier 1 run 42425640847):

* cold, KIC_INDEX_CANON = lift and = lift_plant (every index key re-checked
  against lift_scan), each binary: base hash, counts, index and layout digests,
  Q0 relation, probe count and scalar equal the frozen identity;
* rank process, rank seeds 301-302, each binary: the same index digests, the
  written factor-log table equal to inputs/factor_logs_n83_closure_D4.json, and the
  rank relations digest, probe vector and root calls equal between the two binaries;
* each binary names its own `field_ops_pipeline`.

Output: `inputs/local_identity.json`. This is a reproducibility check of R1 on a base
it was not built for, not independent proof.
"""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
K4 = HERE.parent / "koblitz-n83-k4c400-20261107"
RECONCILE = HERE.parent / "koblitz-n83-reconcile-20261014"
sys.path.insert(0, str(RECONCILE))
import arm as reconcile_arm  # noqa: E402  (the reconcile experiment's arm.py: BASE_ENV)

Q0 = json.loads((HERE.parent / "koblitz-single-target-n83-tier1-20261014" / "inputs" / "targets.json")
                .read_text())["q0"]["point"]
BASE_ENV = dict(reconcile_arm.BASE_ENV)
HEADER = HERE / "snapshots/closure/base_n83_closure_D4.jsonl"
TABLE = HERE / "inputs/factor_logs_n83_closure_D4.json"


def run(binary, rank, canon, seed):
    with tempfile.TemporaryDirectory(prefix="fo2d4-ident-") as folder:
        folder = Path(folder)
        (folder / "points.jsonl").write_text(json.dumps([str(v) for v in Q0], separators=(",", ":")) + "\n")
        env = dict(BASE_ENV, KIC_RANK_THREADS="1", KIC_TARGET_THREADS="1", KIC_INDEX_DIGEST="1",
                   KIC_ROOT_TABLE="compact", KIC_STATE_FOLD="1", KIC_FOLD_PLANT="0", KIC_INDEX_CANON=canon,
                   KIC_SCAN_SELFTEST="full", KIC_TARGET_CANON="lift", KIC_SCAN_ORDER="feistel",
                   KIC_PROBE_PIPELINE="prefetch")
        if rank:
            env.update(KIC_LOG_TABLE_OUT=str(folder / "logs.json"), KIC_RANK_CANON="lift", KIC_RANK_ORDER="feistel",
                       KIC_RANK_PROBE="target", KIC_RANK_SOLVE="frame")
        else:
            env["KIC_LOG_TABLE_IN"] = str(TABLE)
        proc = subprocess.run([str(binary), str(HEADER), str(folder / "points.jsonl"), str(seed), str(folder / "ic.jsonl")],
                              env=env, capture_output=True, text=True)
        summary = json.loads(proc.stdout.strip().splitlines()[-1])
        record = json.loads((folder / "ic.jsonl").read_text().splitlines()[0])
        logs_equal = None
        if rank:
            logs_equal = json.loads((folder / "logs.json").read_text())["logs"] == json.loads(TABLE.read_text())["logs"]
        d = summary["index_digest"]
        return {"binary": binary.name, "kind": "rank" if rank else "cold", "index_canon": canon, "seed": seed,
                "exit": proc.returncode, "group_verified": record.get("group_verified"),
                "targets_solved": summary.get("targets_solved"), "targets_failed": summary.get("targets_failed"),
                "base_hash": summary["base_hash"], "orbit_columns": summary["orbit_columns"],
                "index_orbits": summary["index_orbits"], "factor_base_points": summary["factor_base_points"],
                "regular_states": summary["regular_states"], "stored_states": summary["stored_states"],
                "root_table_slots": summary["root_table_slots"], "root_table_entries": summary["root_table_entries"],
                "index_plant_checked_inputs": summary["index_plant_checked_inputs"],
                "field_ops_pipeline": summary.get("field_ops_pipeline"),
                "index_digest": {k: d[k] for k in ("logical_states_blake3", "table_map_sum64", "table_map_xor64",
                                                   "table_entries", "stored_states_blake3", "table_slots_blake3")},
                "relation": record.get("point_indices"), "probes_folded": record.get("probes"),
                "recovered_scalar": str(record.get("recovered_scalar")),
                "logs_equal_table": logs_equal,
                "log_table_input_blake3": (summary.get("factor_log_table") or {}).get("input_blake3"),
                "closure": {k: (summary.get("closure") or {}).get(k) for k in
                            ("columns", "orbits", "orbits_per_column", "norm_cap", "source_base_hash")},
                "closure_multipliers_sha256": hashlib.sha256(json.dumps(
                    (summary.get("closure") or {}).get("multipliers"), separators=(",", ":")).encode()).hexdigest(),
                "rank_relations_blake3": summary.get("rank_relations_blake3") if rank else None,
                "rank_attempt_probes": summary.get("rank_attempt_probes") if rank else None,
                "rank_root_calls_total": summary.get("rank_root_calls_total") if rank else None,
                "rank_stage_ms": (summary.get("timing_ms") or {}).get("rank_stage"),
                "index_ms": (summary.get("timing_ms") or {}).get("index_build"),
                "rank_attempts": summary.get("rank_attempts"), "rank_failures": summary.get("rank_failures"),
                "rank_rows_without_gain": summary.get("rank_rows_without_gain")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary-a", type=Path, required=True)
    parser.add_argument("--binary-b", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=HERE / "inputs" / "local_identity.json")
    args = parser.parse_args()
    frozen = json.loads((K4 / "protocol.json").read_text())["online"]["bases"]["D4"]
    runs = []
    for binary in (args.binary_a, args.binary_b):
        runs += [run(binary, False, "lift", 7), run(binary, False, "lift_plant", 7)]
        runs += [run(binary, True, "lift", s) for s in (301, 302)]
    keys = ("base_hash", "orbit_columns", "index_orbits", "factor_base_points", "regular_states",
            "root_table_slots", "root_table_entries")
    want_digest = dict({k: frozen["index_digest"][k] for k in ("logical_states_blake3", "table_map_sum64",
                                                              "table_map_xor64", "table_entries")},
                       **{k: frozen["layout_digest"][k] for k in ("stored_states_blake3", "table_slots_blake3")})
    cold = [r for r in runs if r["kind"] == "cold"]
    rank = [r for r in runs if r["kind"] == "rank"]
    a_bin, b_bin = args.binary_a.name, args.binary_b.name
    checks = {
        "all_exit_0_and_group_verified": all(r["exit"] == 0 and r["group_verified"] is True and
                                              r["targets_solved"] == 1 and r["targets_failed"] == 0 for r in runs),
        "every_process_equals_frozen_d4_counts": all(
            all(r[k] == frozen[k] for k in keys) and r["stored_states"] == frozen["stored_states_folded"] for r in runs),
        "every_process_equals_frozen_d4_index_and_layout_digests": all(r["index_digest"] == want_digest for r in runs),
        "cold_q0_equals_frozen_identity": all(
            r["relation"] == frozen["q0_identity"]["relation"] and r["probes_folded"] == frozen["q0_identity"]["probes_folded"]
            and r["recovered_scalar"] == frozen["q0_identity"]["scalar"] for r in cold),
        "cold_table_digest_and_closure_shape_equal_frozen": all(
            r["log_table_input_blake3"] == frozen["log_table_input_blake3"] and
            r["closure_multipliers_sha256"] == frozen["closure_multipliers_sha256"] and
            r["closure"]["orbits_per_column"] == frozen["orbits_per_column"] for r in cold),
        "plant_checked_every_root": all(
            r["index_plant_checked_inputs"] == (2 * r["stored_states"] if r["index_canon"] == "lift_plant" else 0)
            for r in cold),
        "rank_tables_equal_derived_table": all(r["logs_equal_table"] is True for r in rank),
        "rank_full_rank_no_failures": all(r["rank_failures"] == 0 and r["rank_rows_without_gain"] == 0 for r in rank),
        "rank_work_identical_across_binaries": all(
            len({(json.dumps(r["rank_attempt_probes"]), r["rank_relations_blake3"], r["rank_root_calls_total"])
                 for r in rank if r["seed"] == s}) == 1 for s in (301, 302)),
        "pipelines_name_their_binary": all(
            (r["field_ops_pipeline"] or "").endswith("+n83_const_reduce_shift") == (r["binary"] == b_bin) and
            r["field_ops_pipeline"] for r in runs)}
    out = {"schema": 1, "binary_a": a_bin, "binary_b": b_bin, "frozen_identity_source": "koblitz-n83-k4c400-20261107 protocol.json online.bases.D4",
           "host": "cloud-agent VM (diagnostic only; one process at a time)", "runs": runs, "checks": checks,
           "all_pass": all(checks.values())}
    args.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": out["all_pass"], "checks": checks}, sort_keys=True))
    sys.exit(0 if out["all_pass"] else 1)


if __name__ == "__main__":
    main()
