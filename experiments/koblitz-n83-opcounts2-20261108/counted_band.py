#!/usr/bin/env python3
"""The section 5a band with the IC side COUNTED, from a receipt plus a counting pass.

`band_model.py` (koblitz-n83-k4c400-20261107) models the IC units from the
archived counted run 39882571652 of the stacked producer. This script
replaces the model with counts of the field-ops-2 producer itself
(`ic_online_fieldops2_counted_r770`, feature op-counts, run with
KIC_OPCOUNTS=1): a counting pass, separate from every timed run.

Inputs:

* `--receipt-dir`: a receipt's panel directory (`runs.jsonl` and the stdout
  files with `raw_b64=`). Only the matched rho arm's (`--reference`, rT)
  `charges_setup_and_solve` are read from it, one unit per point, as in
  `band_model.py`.
* `--counts`: the counting pass, JSON lines, one per counted process:
  `{"arm": band arm name, "point_id", "pair", "process": "rank"|"cold",
  "summary_op_counts": <summary op_counts>, "record_op_counts": <target record
  op_counts>}` (`local_verify.py --counts-out` writes this shape).

IC unit of a (point, pair): the rank process's `rank_stage` phase plus the cold
process's `setup`, `linear_algebra` and `between_linear_algebra_and_targets`
phases and its target's online counts (the opcounts experiment's
`analyze_v2.py` unit, unchanged). A point's unit is the mean over its pairs.
The band is computed by the opcounts experiment's `band.py` (`analyse`,
unchanged): cost(w) = group ops + w x unpriced native ops at w = 0, 0.1, 1 GAE,
rho's scalar multiplications at both ends of [0, 2 (r_bits - 1)] GAE.

`--compare-model` also writes, per (point, pair), `band_model.py`'s modelled
unit for the same producer quantities (probes, attempts, K', table entries)
beside the counted one, and the counted/model ratio per kind.

Output: `counted_band.json` and `counted_band.md` in `--out-dir`.
"""

import argparse
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
K4C400 = HERE.parent / "koblitz-n83-k4c400-20261107"
sys.path.insert(0, str(K4C400))
import band_model  # noqa: E402  (k4c400's band_model.py, unchanged; it imports the opcounts band.py)

band = band_model.band
IC_KINDS = band_model.IC_KINDS
COLD_PHASES = ("setup", "linear_algebra", "between_linear_algebra_and_targets")


def add(*parts):
    keys = set().union(*parts)
    return {k: sum(p.get(k, 0) for p in parts) for k in sorted(keys)}


def ic_unit(rank, cold):
    if not (rank["summary_op_counts"] or {}).get("enabled") or not (cold["summary_op_counts"] or {}).get("enabled"):
        raise ValueError("a process of the counting pass ran without counting")
    return add(rank["summary_op_counts"]["phases"]["rank_stage"],
               *(cold["summary_op_counts"]["phases"][p] for p in COLD_PHASES), cold["record_op_counts"])


def ic_units(rows):
    """{arm: {point: unit}} with a point's unit the mean over its pairs."""
    pairs = {}
    for row in rows:
        pairs.setdefault((row["arm"], row["point_id"], row.get("pair")), {})[row["process"]] = row
    per_point = {}
    for (arm, point, _), procs in sorted(pairs.items(), key=lambda kv: str(kv[0])):
        if set(procs) != {"rank", "cold"}:
            raise ValueError("pair %s %s lacks a rank or cold process" % (arm, point))
        per_point.setdefault(arm, {}).setdefault(point, []).append(ic_unit(procs["rank"], procs["cold"]))
    return {arm: {p: {k: statistics.mean(u.get(k, 0) for u in us) for k in IC_KINDS}
                  for p, us in sorted(points.items())} for arm, points in per_point.items()}


def rho_units(panel, reference):
    rows = [json.loads(line) for line in (panel / "runs.jsonl").read_text().splitlines() if line.strip()]
    rho = {}
    for r in rows:
        if r["status"] == "valid" and r["arm"] == reference:
            charges = next(rec["outcome"]["charges_setup_and_solve"]
                           for rec in band_model.raw_of(panel, r)["records"] if "outcome" in rec)
            rho[r["point_id"]] = {k: charges[k] for k in ("canonicalizations", "failed_collisions", "group_additions",
                                                           "partition_hashes", "scalar_multiplications",
                                                           "table_inserts", "table_queries")}
    return rho


def model_comparison(rows, protocol):
    """band_model's modelled unit for the same producer quantities, beside the counted unit."""
    const = band_model.constants()
    pairs = {}
    for row in rows:
        pairs.setdefault((row["arm"], row["point_id"], row.get("pair")), {})[row["process"]] = row
    out = []
    for (arm, point, pair), procs in sorted(pairs.items(), key=lambda kv: str(kv[0])):
        spec = protocol["online"]["bases"][procs["rank"]["base"]]
        rank_probes, attempts = procs["rank"]["rank_probes"], procs["rank"]["rank_attempts"]
        online = procs["cold"]["online_probes"]
        model = band_model.ic_unit(const, rank_probes + online, attempts + 1, spec["orbit_columns"],
                                   spec["root_table_entries"])
        counted = ic_unit(procs["rank"], procs["cold"])
        split = band.analyse({"schema": "ic-band-input/v1", "r_bits": 53, "reference": "x", "arms": {
            "x": {"family": "ic", "units": {"u": {k: counted.get(k, 0) for k in IC_KINDS}}},
            "m": {"family": "ic", "units": {"u": model}}}}, 1, seed=1)["arms"]
        out.append({
            "arm": arm, "point_id": point, "pair": pair, "base": procs["rank"]["base"],
            "producer_quantities": {"rank_probes": rank_probes, "rank_attempts": attempts, "online_probes": online,
                                    "k_prime": spec["orbit_columns"], "root_table_entries": spec["root_table_entries"]},
            "counted": {k: counted.get(k, 0) for k in IC_KINDS},
            "model": model,
            "counted_over_model": {k: (counted.get(k, 0) / model[k] if model[k] else None) for k in IC_KINDS},
            "group_ops": {"counted": split["x"]["mean_group_ops"], "model": split["m"]["mean_group_ops"]},
            "unpriced_native_ops": {"counted": split["x"]["mean_unpriced_native_ops"],
                                    "model": split["m"]["mean_unpriced_native_ops"]},
        })
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt-dir", type=Path, help="panel directory of a receipt (rho units)")
    parser.add_argument("--counts", type=Path, required=True, help="counting pass, JSON lines")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--reference", default="rT")
    parser.add_argument("--draws", type=int, default=10000)
    parser.add_argument("--protocol", type=Path, default=K4C400 / "protocol.json")
    parser.add_argument("--compare-model", action="store_true")
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text())
    rows = [json.loads(line) for line in args.counts.read_text().splitlines() if line.strip()]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    result = {"schema": "ic-counted-band/v1", "counts_file": str(args.counts)}
    if args.compare_model:
        result["model_comparison"] = model_comparison(rows, protocol)
    text = ""
    if args.receipt_dir:
        data = {"schema": "ic-band-input/v1", "r_bits": 53, "reference": args.reference, "arms": {}}
        for arm, units in ic_units(rows).items():
            data["arms"][arm] = {"family": "ic", "units": units}
        data["arms"][args.reference] = {"family": "rho", "units": rho_units(args.receipt_dir, args.reference)}
        points = set.intersection(*(set(a["units"]) for a in data["arms"].values()))
        for a in data["arms"].values():
            a["units"] = {p: u for p, u in a["units"].items() if p in points}
        band_result = band.analyse(data, args.draws, seed=protocol["bootstrap"]["seed"])
        band_result["label"] = ("COUNTED band: rho counted in the receipt; IC counted by the field-ops-2 counting "
                                "pass (ic_online_fieldops2_counted_r770, KIC_OPCOUNTS=1), not modelled")
        result["band"] = band_result
        text = "**" + band_result["label"] + "**\n\n" + band.markdown(band_result)
    elif not args.compare_model:
        raise SystemExit("nothing to do: give --receipt-dir and/or --compare-model")
    (args.out_dir / "counted_band.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if args.compare_model:
        lines = ["| base | point | kind | counted | model | counted/model |", "|---|---|---|---:|---:|---:|"]
        for c in result["model_comparison"]:
            for k in IC_KINDS:
                ratio = c["counted_over_model"][k]
                lines.append("| %s | %s | %s | %d | %.4g | %s |" % (c["base"], c["point_id"], k, c["counted"][k],
                                                                    c["model"][k],
                                                                    "-" if ratio is None else "%.3f" % ratio))
            for name in ("group_ops", "unpriced_native_ops"):
                v = c[name]
                lines.append("| %s | %s | **%s** | %d | %.4g | %.3f |" % (c["base"], c["point_id"], name, v["counted"],
                                                                         v["model"], v["counted"] / v["model"]))
        text += "\n## Counted vs modelled IC units\n\n" + "\n".join(lines) + "\n"
    (args.out_dir / "counted_band.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
