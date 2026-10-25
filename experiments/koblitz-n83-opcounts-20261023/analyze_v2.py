#!/usr/bin/env python3
"""Fail-closed analysis of the complete frozen 62-run n83 panel.

The pinned v1 producer, protocol, analysis, and historical receipts stay intact.
This version requires the exact full ordered panel and publishes a band only
when all archive-identity and validity checks pass. Outputs use v2 filenames.
It cannot accept partial diagnostic runs as the complete protocol.
"""
import argparse
import json
from pathlib import Path
from opcounts import (ARCHIVE, RHO_ARM, RANK_ARMS, PAIRS, R_BITS, plan,
                      archived_rows, decode, parts, rho_charges, add, band)

def analyze(args):
    receipt_dir = args.receipt_dir.resolve()
    # Clear only this version's generated outputs before parsing any input.
    for name in ("band-v2.md", "opcounts_result-v2.json", "counts-v2.json"):
        (receipt_dir / name).unlink(missing_ok=True)
    rows = [json.loads(line) for line in (receipt_dir / "runs.jsonl").read_text().splitlines() if line]
    expected = plan()
    identity = lambda row: tuple(row.get(k) for k in
        ("serial", "arm", "point_id", "seed", "archived_serial", "block"))
    complete = (len(expected) == 62 and
                [identity(row) for row in rows] == [identity(row) for row in expected])
    archive = archived_rows()
    checks = {"complete_frozen_panel": complete, "all_runs_valid": bool(rows) and all(row["status"] == "valid" for row in rows)}
    mismatches = []
    rank, cold, rho, scalars = {}, {}, {}, {}
    for row in rows:
        record = decode(receipt_dir / row["stdout_file"])
        old_row = archive[row["archived_serial"]]
        old = decode(ARCHIVE / old_row["stdout_file"])
        if record is None or old is None or old_row["arm"] != row["arm"] or old_row["point_id"] != row["point_id"]:
            mismatches.append("%s %s: record missing or archive mismatch" % (row["arm"], row["point_id"]))
            continue
        if row["arm"] == RHO_ARM:
            charges, old_charges = rho_charges(record), rho_charges(old)
            if charges is None or charges != old_charges:
                mismatches.append("rT %s: charges differ from the archived run" % row["point_id"])
            if record["fields"].get("recovered_scalar") != old["fields"].get("recovered_scalar"):
                mismatches.append("rT %s: scalar differs from the archived run" % row["point_id"])
            rho[row["point_id"]] = charges
            scalars.setdefault(row["point_id"], set()).add(str(record["fields"].get("recovered_scalar")))
            continue
        target, summary = parts(record)
        old_target, old_summary = parts(old)
        counts = summary.get("op_counts") or {}
        if counts.get("enabled") is not True or not isinstance(target.get("op_counts"), dict):
            mismatches.append("%s %s: no op counts" % (row["arm"], row["point_id"]))
            continue
        keys = ["point_indices", "x_codes", "pinned_intermediates", "probes", "root_calls", "relation_checks",
                "skipped_symmetric_states", "recovered_scalar"]
        if row["arm"] in RANK_ARMS:
            summary_keys = ["rank_attempt_probes", "rank_relations_blake3", "rank_probes_total",
                            "rank_root_calls_total", "rank_attempts", "rank_relations", "rank_failures", "rank"]
        else:
            summary_keys = ["index_digest", "stored_states", "root_table_entries"]
        for key in keys:
            if target.get(key) != old_target.get(key):
                mismatches.append("%s %s: target %s differs from the archived run" % (row["arm"], row["point_id"], key))
        for key in summary_keys:
            if summary.get(key) != old_summary.get(key):
                mismatches.append("%s %s: %s differs from the archived run" % (row["arm"], row["point_id"], key))
        scalars.setdefault(row["point_id"], set()).add(str(target.get("recovered_scalar")))
        entry = {"phases": counts["phases"], "end_to_end": counts["end_to_end"], "target": target["op_counts"],
                 "timing_ms": summary.get("timing_ms"), "online_ms": target.get("online_ms")}
        (rank if row["arm"] in RANK_ARMS else cold).setdefault(row["arm"], {})[row["point_id"]] = entry
    checks["identical_to_archived_run"] = not mismatches
    checks["one_scalar_per_point"] = all(len(values) == 1 for values in scalars.values())
    units = {}
    for name, (rank_arm, cold_arm) in PAIRS.items():
        if rank_arm not in rank or cold_arm not in cold:
            continue
        # One rank process per arm (K1); its rank-stage counts are a
        # deterministic function of the rank seed.
        (rank_entry,) = rank[rank_arm].values()
        units[name] = {"family": "ic", "units": {}}
        for point, entry in cold[cold_arm].items():
            phases = entry["phases"]
            units[name]["units"][point] = add(rank_entry["phases"]["rank_stage"], phases["setup"],
                                              phases["linear_algebra"],
                                              phases["between_linear_algebra_and_targets"], entry["target"])
    units[RHO_ARM] = {"family": "rho", "units": {point: charges for point, charges in rho.items() if charges}}
    band_input = {"schema": "ic-band-input/v1", "r_bits": R_BITS, "reference": RHO_ARM, "arms": units,
                  "unit": "one solved target: IC = rank stage of the K1 rank process (rank seed 101) + the cold "
                          "process's setup, linear algebra (cached-table load and verification) and online "
                          "interval at that point, the stacked end-to-end cold E2E(k, c); rho = setup and solve"}
    (receipt_dir / "counts-v2.json").write_text(json.dumps(band_input, indent=2, sort_keys=True) + "\n")
    result = {"checks": checks, "mismatches": mismatches,
              "rank_phases": {arm: {p: e["phases"] for p, e in v.items()} for arm, v in rank.items()},
              "cold_setup_phases": {arm: next(iter(v.values()))["phases"]["setup"] for arm, v in cold.items()}}
    passed = all(checks.values())
    if passed and len(units) == 3 and all(arm["units"] for arm in units.values()):
        result["band"] = band.analyse(band_input, args.draws)
        result["band_frobenius_as_group"] = band.analyse(band_input, args.draws, frobenius_as_group=True)
        (receipt_dir / "band-v2.md").write_text(band.markdown(result["band"]) + "\n## Sensitivity: Frobenius at 1 GAE\n\n" +
                                             band.markdown(result["band_frobenius_as_group"]))
    result["verdict"] = "counts_identical" if passed else "counts_fail"
    (receipt_dir / "opcounts_result-v2.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verdict": result["verdict"], "checks": checks, "mismatches": mismatches[:20]}, indent=2))
    if (receipt_dir / "band-v2.md").exists():
        print((receipt_dir / "band-v2.md").read_text())
    return 0 if passed else 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt-dir", required=True, type=Path)
    parser.add_argument("--draws", type=int, default=10000)
    args = parser.parse_args()
    if args.draws < 1:
        parser.error("--draws must be positive")
    try:
        code = analyze(args)
    except (OSError, ValueError, KeyError, TypeError, IndexError, ArithmeticError) as error:
        failure = {"verdict": "counts_fail", "checks": {"analysis_completed": False},
                   "error": str(error)}
        (args.receipt_dir / "opcounts_result-v2.json").write_text(
            json.dumps(failure, indent=2) + "\n")
        print(json.dumps(failure, indent=2))
        code = 1
    raise SystemExit(code)
