#!/usr/bin/env python3
"""Local identity test of the D4 closure base (a diagnostic before freezing; not timing evidence).

Runs the frozen field-ops producer (`ic_online_fieldops_r770`, the binary of
`../koblitz-n83-fieldops-20261104/online-b`) on Q0, with arm.py's exact
environment, and records what a base must freeze (the fields of
`protocol.json online.bases.<base>`):

* D4, cold, KIC_INDEX_CANON = lift and = lift_plant (every index key
  re-checked against lift_scan and the selected canonicalizer: an independent
  implementation of the index key): the two must give one set of digests;
* D4, rank process, three rank seeds: the same index digests, and the
  written factor-log table equal to inputs/factor_logs_n83_closure_D4.json;
* M38 (control), cold: must reproduce the fieldops protocol's frozen M38
  identity (digests, Q0 scalar, relation and probe count). That shows this
  harness reads the identity of a base the same way the frozen runs did.

Output: `inputs/local_identity.json`. The identity of D4 is a reproducibility
identity of the producer (the same code run again), not an independent proof;
the independent checks of D4 are `verify_closure.py` (header and table, pinned
oracle) and, in the run, the oracle replay of every recovered scalar.
"""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIELDOPS = HERE.parent / "koblitz-n83-fieldops-20261104"
RECONCILE = HERE.parent / "koblitz-n83-reconcile-20261014"
sys.path.insert(0, str(RECONCILE))
import arm as reconcile_arm  # noqa: E402  (the reconcile experiment's arm.py: BASE_ENV)

Q0 = json.loads((HERE.parent / "koblitz-single-target-n83-tier1-20261014" / "inputs" / "targets.json")
                .read_text())["q0"]["point"]
BASE_ENV = dict(reconcile_arm.BASE_ENV)
BASES = {"D4": (HERE / "snapshots/closure/base_n83_closure_D4.jsonl", HERE / "inputs/factor_logs_n83_closure_D4.json"),
         "M38": (HERE / "snapshots/closure/base_n83_closure_M38.jsonl", HERE / "inputs/factor_logs_n83_closure_M38.json")}


def run(binary, base, rank, canon, seed):
    header, table = BASES[base]
    with tempfile.TemporaryDirectory(prefix="k4-ident-") as folder:
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
            env["KIC_LOG_TABLE_IN"] = str(table)
        proc = subprocess.run([str(binary), str(header), str(folder / "points.jsonl"), str(seed), str(folder / "ic.jsonl")],
                              env=env, capture_output=True, text=True)
        summary = json.loads(proc.stdout.strip().splitlines()[-1])
        record = json.loads((folder / "ic.jsonl").read_text().splitlines()[0])
        logs_equal = None
        if rank:
            logs_equal = json.loads((folder / "logs.json").read_text())["logs"] == json.loads(table.read_text())["logs"]
        d = summary["index_digest"]
        return {"base": base, "kind": "rank" if rank else "cold", "index_canon": canon, "seed": seed,
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
                "rank_stage_ms": (summary.get("timing_ms") or {}).get("rank_stage"),
                "rank_attempts": summary.get("rank_attempts"), "rank_failures": summary.get("rank_failures"),
                "rank_rows_without_gain": summary.get("rank_rows_without_gain")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=HERE / "inputs" / "local_identity.json")
    args = parser.parse_args()
    runs = [run(args.binary, "D4", False, "lift", 7), run(args.binary, "D4", False, "lift_plant", 7)]
    runs += [run(args.binary, "D4", True, "lift", s) for s in (301, 302, 303)]
    runs.append(run(args.binary, "M38", False, "lift", 7))
    fo = json.loads((FIELDOPS / "protocol.json").read_text())["online"]["bases"]["M38"]
    d4 = [r for r in runs if r["base"] == "D4"]
    keys = ("base_hash", "orbit_columns", "index_orbits", "factor_base_points", "regular_states", "stored_states",
            "root_table_slots", "root_table_entries", "index_digest")
    m38 = runs[-1]
    out = {"schema": 1, "binary": str(args.binary.name),
           "host": "cloud-agent VM (diagnostic only; one process at a time)", "runs": runs,
           "checks": {
               "d4_all_exit_0_and_group_verified": all(r["exit"] == 0 and r["group_verified"] is True and
                                                        r["targets_solved"] == 1 and r["targets_failed"] == 0 for r in d4),
               "d4_one_identity_across_canonicalizers_and_rank_seeds": all(
                   all(r[k] == d4[0][k] for k in keys) for r in d4),
               "d4_q0_identical_across_cold_runs": all(
                   (r["relation"], r["probes_folded"], r["recovered_scalar"]) ==
                   (d4[0]["relation"], d4[0]["probes_folded"], d4[0]["recovered_scalar"]) for r in d4[:2]),
               "d4_plant_checked_every_root": d4[1]["index_plant_checked_inputs"] == 2 * d4[1]["stored_states"] and
                                              d4[0]["index_plant_checked_inputs"] == 0,
               "d4_rank_tables_equal_derived_table": all(r["logs_equal_table"] is True for r in d4 if r["kind"] == "rank"),
               "d4_rank_full_rank_no_failures": all(r["rank_failures"] == 0 and r["rank_rows_without_gain"] == 0
                                                    for r in d4 if r["kind"] == "rank"),
               "m38_reproduces_fieldops_frozen_identity": (
                   m38["index_digest"]["logical_states_blake3"] == fo["index_digest"]["logical_states_blake3"] and
                   m38["index_digest"]["table_map_sum64"] == fo["index_digest"]["table_map_sum64"] and
                   m38["index_digest"]["stored_states_blake3"] == fo["layout_digest"]["stored_states_blake3"] and
                   m38["index_digest"]["table_slots_blake3"] == fo["layout_digest"]["table_slots_blake3"] and
                   m38["root_table_entries"] == fo["root_table_entries"] and
                   m38["relation"] == fo["q0_identity"]["relation"] and
                   m38["probes_folded"] == fo["q0_identity"]["probes_folded"] and
                   m38["recovered_scalar"] == fo["q0_identity"]["scalar"])}}
    out["all_pass"] = all(out["checks"].values())
    args.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": out["all_pass"], "checks": out["checks"]}, sort_keys=True))
    sys.exit(0 if out["all_pass"] else 1)


if __name__ == "__main__":
    main()
