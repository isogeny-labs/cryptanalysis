#!/usr/bin/env python3
"""Rerun the stacked n=83 rank block K1 and the cold panel with native work counted (PROTOCOL.md).

Every run goes through `koblitz-n83-stacked-20261016`'s own
`run_schedule.one()` and `arm.py`, unchanged (pinned process, clean
environment, Tier 1 counters and noise gate, factor-log check against B's
archived table, index digests against B's index). The only change is the IC
binary: the counted producer `ic_online_stacked_counted_r770` (this
experiment's `make_counted_source.py`, built with `--features op-counts`)
in place of `ic_online_stacked_r770`. The tuned rho `rho_tuned_r770` is the
stacked build's, unchanged; it already emits its charges.

Order, one pinned CPU, one fresh process per run:

  K1: kS, kP at K1 point s000, rank seed 101 (archived: run 38862448935
      serials 42 and 43)
  C:  for each of the 20 cold points s000..s019, in order: cS, cP, rT, with
      the stacked schedule's seeds (IC 7, rho 870000 + i)

`analyze` gates every row against the archived run (identical relations,
probes, root calls, rank-attempt probes, rank relations digest, scalars and
rho charges), builds the band input (`counts.json`) and applies `band.py`.
Nothing is re-run.
"""

import argparse
import base64
import copy
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
STACKED = REPO / "experiments" / "koblitz-n83-stacked-20261016"
ARCHIVE = STACKED / "run_github_38862448935" / "panel"
sys.path.insert(0, str(STACKED))
sys.path.insert(0, str(HERE))
import run_schedule  # noqa: E402  (the stacked experiment's runner, unchanged)
import band  # noqa: E402

COUNTED = "ic_online_stacked_counted_r770"
RANK_ARMS = ("kS", "kP")
COLD_ARMS = ("cS", "cP")
RHO_ARM = "rT"
PAIRS = {"S": ("kS", "cS"), "P": ("kP", "cP")}
R_BITS = 53  # r = 8569786107849059 < 2^53


def stacked_inputs():
    protocol = json.loads((STACKED / "protocol.json").read_text())
    schedule = json.loads((STACKED / "schedule.json").read_text())
    runs = [run for segment in schedule["segments"] for run in segment["runs"]]
    k1 = {run["arm"]: run for segment in schedule["segments"] if segment["id"] == "K1" for run in segment["runs"]}
    assert k1["kS"]["serial"] == 42 and k1["kP"]["serial"] == 43 and k1["kS"]["seed"] == 101
    points = sorted({run["point_id"] for run in runs if run["point_id"].startswith("s")})
    cold = {}
    for run in runs:
        if run["arm"] in COLD_ARMS + (RHO_ARM,) and run["point_id"] in points:
            cold[(run["arm"], run["point_id"])] = run
    return protocol, k1, points, cold


def counted_protocol(protocol):
    patched = copy.deepcopy(protocol)
    for name in RANK_ARMS + COLD_ARMS:
        assert patched["arms"][name]["binary"] == "ic_online_stacked_r770"
        patched["arms"][name]["binary"] = COUNTED
    return patched


def plan(points_limit=None, arms=None):
    _, k1, points, cold = stacked_inputs()
    points = points[:points_limit] if points_limit else points
    keep = set(arms) if arms else set(RANK_ARMS + COLD_ARMS + (RHO_ARM,))
    out = []
    for arm in RANK_ARMS:
        if arm not in keep:
            continue
        source = k1[arm]
        out.append({"arm": arm, "point_id": source["point_id"], "point": source["point"], "seed": source["seed"],
                    "archived_serial": source["serial"], "block": "K1"})
    for point in points:
        for arm in COLD_ARMS + (RHO_ARM,):
            if arm not in keep:
                continue
            source = cold[(arm, point)]
            out.append({"arm": arm, "point_id": point, "point": source["point"], "seed": source["seed"],
                        "archived_serial": source["serial"], "block": "C"})
    for serial, run in enumerate(out, start=1):
        run.update(serial=serial, slice=None)
    return out


def execute(args):
    protocol, _, _, _ = stacked_inputs()
    if run_schedule.sha256(args.log_table) != protocol["online"]["factor_log_table_sha256"]:
        raise SystemExit("factor-log table differs from the protocol's")
    patched = counted_protocol(protocol)
    receipt_dir = args.receipt_dir.resolve()
    (receipt_dir / "runs").mkdir(parents=True, exist_ok=False)
    cgroup = run_schedule.ib.current_cgroup()
    runs = plan(args.points, args.arms.split(",") if args.arms else None)
    start = {"cpu": args.cpu, "host": run_schedule.ib.host_probe(), "cgroup": str(cgroup),
             "driver_sha256": run_schedule.sha256(Path(__file__)),
             "band_sha256": run_schedule.sha256(HERE / "band.py"),
             "stacked_protocol_sha256": run_schedule.sha256(STACKED / "protocol.json"),
             "stacked_schedule_sha256": run_schedule.sha256(STACKED / "schedule.json"),
             "arm_wrapper_sha256": run_schedule.sha256(STACKED / "arm.py"),
             "runner_sha256": run_schedule.sha256(STACKED / "run_schedule.py"),
             "binaries_sha256": {name: run_schedule.sha256(args.bin_dir / name)
                                 for name in (COUNTED, "rho_tuned_r770")},
             "points_limit": args.points, "arms_subset": args.arms,
             "order": [[run["serial"], run["arm"], run["point_id"], run["seed"]] for run in runs]}
    (receipt_dir / "runner_start.json").write_text(json.dumps(start, indent=2, sort_keys=True) + "\n")
    with (receipt_dir / "runs.jsonl").open("w") as ledger:
        for run in runs:
            row = run_schedule.one(patched, run, args, receipt_dir, cgroup)
            row.update(block=run["block"], archived_serial=run["archived_serial"])
            ledger.write(json.dumps(row, sort_keys=True) + "\n")
            ledger.flush()
            os.fsync(ledger.fileno())
            print(json.dumps({"serial": run["serial"], "arm": run["arm"], "point": run["point_id"],
                              "status": row["status"], "issues": row["issues"],
                              "wall_ms": row["process_wall_ms"]}), flush=True)


def decode(stdout_path):
    text = Path(stdout_path).read_text()
    lines = [line for line in text.splitlines() if line.startswith("raw_b64=")]
    if len(lines) != 1:
        return None
    raw = base64.b64decode(lines[0][len("raw_b64="):])
    fields = dict(word.split("=", 1) for word in text.splitlines()[-1].split() if "=" in word)
    if fields.get("raw_result_sha256") != hashlib.sha256(raw).hexdigest():
        return None
    return json.loads(raw)


def parts(record):
    targets = [r for r in record["records"] if r.get("kind") == "compact_orbit_dlp_target"]
    summaries = [r for r in record["records"] if r.get("kind") == "compact_orbit_dlp_summary"]
    return (targets[0] if targets else {}), (summaries[0] if summaries else {})


def archived_rows():
    rows = [json.loads(line) for line in (ARCHIVE / "runs.jsonl").read_text().splitlines() if line]
    return {row["serial"]: row for row in rows}


def rho_charges(record):
    for item in record["records"]:
        outcome = item.get("outcome") or {}
        if "charges_setup_and_solve" in outcome:
            return outcome["charges_setup_and_solve"]
    return None


def add(*counts):
    total = {}
    for count in counts:
        for key, value in count.items():
            total[key] = total.get(key, 0) + value
    return total


def analyze(args):
    receipt_dir = args.receipt_dir.resolve()
    rows = [json.loads(line) for line in (receipt_dir / "runs.jsonl").read_text().splitlines() if line]
    archive = archived_rows()
    checks = {"all_runs_valid": bool(rows) and all(row["status"] == "valid" for row in rows)}
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
    (receipt_dir / "counts.json").write_text(json.dumps(band_input, indent=2, sort_keys=True) + "\n")
    result = {"checks": checks, "mismatches": mismatches,
              "rank_phases": {arm: {p: e["phases"] for p, e in v.items()} for arm, v in rank.items()},
              "cold_setup_phases": {arm: next(iter(v.values()))["phases"]["setup"] for arm, v in cold.items()}}
    passed = all(checks.values())
    if len(units) > 1 and all(arm["units"] for arm in units.values()):
        result["band"] = band.analyse(band_input, args.draws)
        result["band_frobenius_as_group"] = band.analyse(band_input, args.draws, frobenius_as_group=True)
        (receipt_dir / "band.md").write_text(band.markdown(result["band"]) + "\n## Sensitivity: Frobenius at 1 GAE\n\n" +
                                             band.markdown(result["band_frobenius_as_group"]))
    result["verdict"] = "counts_identical" if passed else "counts_fail"
    (receipt_dir / "opcounts_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verdict": result["verdict"], "checks": checks, "mismatches": mismatches[:20]}, indent=2))
    if (receipt_dir / "band.md").exists():
        print((receipt_dir / "band.md").read_text())
    return 0 if passed else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    run = sub.add_parser("run")
    run.add_argument("--bin-dir", required=True, type=Path)
    run.add_argument("--log-table", required=True, type=Path)
    run.add_argument("--receipt-dir", required=True, type=Path)
    run.add_argument("--cpu", required=True, type=int)
    run.add_argument("--python", type=Path, default=Path(sys.executable))
    run.add_argument("--points", type=int, help="smoke only: the first k cold points (the workflow passes none)")
    run.add_argument("--arms", help="smoke only: comma-separated subset of kS,kP,cS,cP,rT (the workflow passes none)")
    check = sub.add_parser("analyze")
    check.add_argument("--receipt-dir", required=True, type=Path)
    check.add_argument("--draws", type=int, default=10000)
    args = parser.parse_args()
    if args.mode == "run":
        args.bin_dir = args.bin_dir.resolve(strict=True)
        args.log_table = args.log_table.resolve(strict=True)
        execute(args)
        return 0
    return analyze(args)


if __name__ == "__main__":
    sys.exit(main())
