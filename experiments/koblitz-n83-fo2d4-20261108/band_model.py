#!/usr/bin/env python3
"""The AGENTS.md section 5a band for the K'=4 / 400-orbit experiment: rho counted, IC modelled.

Frozen before any timing (its SHA-256 is in `protocol.json`). It runs the
opcounts experiment's `band.py` UNCHANGED (`analyse`: cost(w) = group ops + w x
unpriced native ops at w = 0, 0.1, 1 GAE, rho's undecomposed scalar
multiplications priced at both ends of 0 and 2 (r_bits - 1) GAE, a paired
bootstrap over points, two arms ranked only where the order holds at every
weight and at both ends) on units built here.

What is counted and what is not. The matched rho (`rT`) is COUNTED in this
run: every rT process's raw record carries `charges_setup_and_solve`
(group_additions, canonicalizations, partition_hashes, table_queries,
table_inserts, failed_collisions, scalar_multiplications), one unit per point.
The field-ops producer, which both IC sides run, emits NO operation counts
(the opcounts experiment's counted producer is the stacked one, and its note
says the counters are not ported). The IC units are therefore a MODEL:

* constants from the archived counted run 39882571652 (stacked producer,
  `../koblitz-n83-opcounts-20261023/run_github_39882571652/analysis_v2/
  counts-v2.json`, SHA-256 pinned below), arm S, mean over its 20 units: every
  kind in PROBE_KINDS per root-index probe, every kind in ATTEMPT_KINDS per
  relation attempt (relation_lifts = K + 1: K rank attempts and the target),
  `la_mulmods` and `la_row_eliminations` by (K'/600)^3 and ^2;
* applied to THIS run's measured quantities of each side and point: the sum
  of the side's rank-attempt probe counts (rank process), the target's
  root-index probes (`ops` of the cold process), the number of rank attempts,
  and K' of the base; `root_index_inserts` = the base's exact table entries.
  The unit of a point is the mean over that point's primary pairs.

So the IC cost is a derived estimate: the stacked producer's per-probe and
per-attempt composition carried to the closure bases and to the field-ops
producer (which computes the same values: the probes, keys and relations are
the exact ones, gated), with the probes and attempts measured. The linear
algebra and factor-base construction are not charged beyond la_*; the
intervals carry no model uncertainty. It is labelled a model band wherever
it is quoted.

`--receipt-dir` is the panel directory of a receipt; `--sides` maps band arm
names to protocol side names (default A -> A, B -> B). Output: `band_model.json`
and `band_model.md` in `--out-dir`.
"""

import argparse
import base64
import hashlib
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OPCOUNTS = HERE.parent / "koblitz-n83-opcounts-20261023"
COUNTS = OPCOUNTS / "run_github_39882571652" / "analysis_v2" / "counts-v2.json"
COUNTS_SHA256 = "981c664ca715acb3c5d77586534466357bf854e64d17eb3288402a28cb1de464"
sys.path.insert(0, str(OPCOUNTS))
import band  # noqa: E402  (the opcounts experiment's band.py, unchanged)

PROBE_KINDS = ("canonicalizations", "root_index_probes", "s3_root_solves", "s3_root_solves_library", "frobenius_x",
               "fold_rotations", "field_half_trace", "field_mul", "field_sqr", "field_inv")
ATTEMPT_KINDS = ("ec_add", "ec_double", "ec_add_trivial", "ec_scalar_mul", "ec_frobenius", "ec_lift_x",
                 "relation_lifts", "descent_mulmods", "root_filter_inserts", "root_filter_queries", "la_inversions")
K_STACKED = 600
IC_KINDS = PROBE_KINDS + ATTEMPT_KINDS + ("la_mulmods", "la_row_eliminations", "root_index_inserts")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def constants():
    if sha256(COUNTS) != COUNTS_SHA256:
        raise SystemExit("counts-v2.json differs from its pinned digest")
    units = json.loads(COUNTS.read_text())["arms"]["S"]["units"]
    mean = {k: statistics.mean(u[k] for u in units.values()) for k in next(iter(units.values()))}
    probes = mean["root_index_probes"]
    attempts = mean["relation_lifts"]
    return {"per_probe": {k: mean[k] / probes for k in PROBE_KINDS},
            "per_attempt": {k: mean[k] / attempts for k in ATTEMPT_KINDS},
            "la_mulmods_at_600": mean["la_mulmods"], "la_row_eliminations_at_600": mean["la_row_eliminations"],
            "stacked_mean_probes": probes, "stacked_mean_attempts": attempts, "units": len(units)}


def raw_of(panel, row):
    lines = (panel / row["stdout_file"]).read_text().splitlines()
    encoded = next(line[len("raw_b64="):] for line in lines if line.startswith("raw_b64="))
    return json.loads(base64.b64decode(encoded, validate=True))


def ic_unit(const, probes, attempts, k_prime, entries):
    unit = {k: const["per_probe"][k] * probes for k in PROBE_KINDS}
    unit.update({k: const["per_attempt"][k] * attempts for k in ATTEMPT_KINDS})
    unit["la_mulmods"] = const["la_mulmods_at_600"] * (k_prime / K_STACKED) ** 3
    unit["la_row_eliminations"] = const["la_row_eliminations_at_600"] * (k_prime / K_STACKED) ** 2
    unit["root_index_inserts"] = entries
    return unit


def build_input(panel, protocol, sides, reference="rT"):
    const = constants()
    rows = [json.loads(line) for line in (panel / "runs.jsonl").read_text().splitlines() if line.strip()]
    valid = [r for r in rows if r["status"] == "valid"]
    out = {"schema": "ic-band-input/v1", "r_bits": 53, "reference": reference, "arms": {}}
    pairs = {}
    for r in valid:
        if r.get("role") != "primary":
            continue
        arm = protocol["arms"][r["arm"]]
        raw = raw_of(panel, r)
        entry = pairs.setdefault((r["point_id"], r["pair"], r["side"]), {})
        summary = next(rec for rec in raw["records"] if rec.get("kind") == "compact_orbit_dlp_summary")
        if arm["kind"] == "ic_rank":
            entry["rank_probes"] = sum(summary["rank_attempt_probes"])
            entry["attempts"] = len(summary["rank_attempt_probes"])
            entry["base"] = arm["base"]
        else:
            entry["online_probes"] = raw["fields"]["ops"]
    for name, side in sides.items():
        per_point = {}
        for (point, pair, label), e in pairs.items():
            if label != side or not {"rank_probes", "online_probes"} <= set(e):
                continue
            spec = protocol["online"]["bases"][e["base"]]
            per_point.setdefault(point, []).append(ic_unit(
                const, e["rank_probes"] + e["online_probes"], e["attempts"] + 1, spec["orbit_columns"],
                spec["root_table_entries"]))
        out["arms"][name] = {"family": "ic", "units": {
            p: {k: statistics.mean(u[k] for u in us) for k in IC_KINDS} for p, us in sorted(per_point.items())}}
    rho = {}
    for r in valid:
        if r["arm"] == reference:
            charges = next(rec["outcome"]["charges_setup_and_solve"] for rec in raw_of(panel, r)["records"]
                           if "outcome" in rec)
            rho[r["point_id"]] = {k: charges[k] for k in ("canonicalizations", "failed_collisions", "group_additions",
                                                           "partition_hashes", "scalar_multiplications",
                                                           "table_inserts", "table_queries")}
    out["arms"][reference] = {"family": "rho", "units": rho}
    return out, const


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--sides", default="A=A,B=B", help="band arm = protocol side, comma separated")
    parser.add_argument("--draws", type=int, default=10000)
    parser.add_argument("--protocol", type=Path, default=HERE / "protocol.json")
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text())
    sides = dict(item.split("=") for item in args.sides.split(","))
    data, const = build_input(args.receipt_dir, protocol, sides)
    result = band.analyse(data, args.draws, seed=protocol["bootstrap"]["seed"])
    result["label"] = ("MODEL band: rho counted in this run; IC units modelled from the archived counted run "
                       "39882571652 (see band_model.py); not a counted run of the field-ops producer")
    result["model_constants"] = const
    result["counts_sha256"] = COUNTS_SHA256
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "band_model.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    text = band.markdown(result)
    text = "**" + result["label"] + "**\n\n" + text
    (args.out_dir / "band_model.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
