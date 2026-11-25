#!/usr/bin/env python3
"""Freeze the K899 identity from a diagnostic output directory (before any Tier 1 timing).

Reads `diag.json` and `factor_logs_n83_K899.json` written by `run_diag.py`
and writes `../inputs/k899_identity.json` and `../inputs/factor_logs_n83_K899.json`:

* `k899`: the structural facts every K899 process must reproduce (base
  hash and file digest, 899 columns, logical and stored states, slot count,
  root-table entries, the index digests, the Q0 relation, probes and
  scalar) and the factor-log table (oracle-verified by the diagnostic and
  re-verified by `check_log_table.py` in every Tier 1 job);
* `diagnostic`: the go/no-go numbers and the K899 / K600 cost ratios the
  power check uses (`--where runner|local` labels them).

Every structural field must agree across every K899 process of the
diagnostic, or this script stops.
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
BASE899 = EXP.parent / "n83-compact-orbit-k899-20261012/runs/K899/base.jsonl"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("diag_dir", type=Path)
    parser.add_argument("--where", required=True, choices=("runner", "local"))
    parser.add_argument("--run-url", required=True)
    args = parser.parse_args()
    diag = json.loads((args.diag_dir / "diag.json").read_text())
    if not diag["go"]:
        raise SystemExit("diagnostic is no-go: %s" % json.dumps(diag["gates"]))
    rows = {r["tag"]: r for r in diag["rows"] if "skipped" not in r}
    k9 = [r for r in rows.values() if r["K"] == 899]
    keys = ("base_hash", "orbit_columns", "regular_states", "stored_states", "root_table_slots",
            "root_table_entries")
    for key in keys:
        if len({json.dumps(r[key]) for r in k9}) != 1:
            raise SystemExit("K899 processes disagree on " + key)
    digests = {json.dumps({k: r["index_digest"][k] for k in ("logical_states_blake3", "table_map_sum64",
                                                            "table_map_xor64", "table_entries")}, sort_keys=True)
               for r in k9}
    if len(digests) != 1:
        raise SystemExit("K899 processes disagree on the index digest")
    targets = {json.dumps([r["target"]["relation"], r["target"]["probes"], r["target"]["recovered_scalar"]])
               for r in k9}
    if len(targets) != 1:
        raise SystemExit("K899 processes disagree on the Q0 relation, probes or scalar")
    first = k9[0]
    table_src = args.diag_dir / "factor_logs_n83_K899.json"
    table_dst = EXP / "inputs" / "factor_logs_n83_K899.json"
    shutil.copyfile(table_src, table_dst)
    if sha256(table_dst) != diag["checks"]["k899_table_sha256"]:
        raise SystemExit("copied table differs from the diagnostic's")
    d = diag["derived"]
    cold600 = (rows["cP600_a"]["cold_in_process_ms"] + rows["cP600_b"]["cold_in_process_ms"]) / 2
    cold899 = (rows["cP899_a"]["cold_in_process_ms"] + rows["cP899_b"]["cold_in_process_ms"]) / 2
    rank600, rank899 = d["rank_stage_ms_K600"], d["rank_stage_ms_K899"]
    att600 = rank600 / rows["kP600"]["rank"]["attempts"]
    att899 = rank899 / rows["kP899"]["rank"]["attempts"]
    identity = {
        "schema": 1,
        "source": {"run_url": args.run_url, "where": args.where, "diag_json_sha256": sha256(args.diag_dir / "diag.json"),
                   "script": "diag/run_diag.py", "rank_seed": diag["seed"]},
        "k899": {
            "base": "../n83-compact-orbit-k899-20261012/runs/K899/base.jsonl",
            "base_file_sha256": sha256(BASE899),
            "base_hash": first["base_hash"], "orbit_columns": first["orbit_columns"],
            "regular_states": first["regular_states"], "stored_states_folded": first["stored_states"],
            "root_table_slots_folded": first["root_table_slots"], "root_table_entries": first["root_table_entries"],
            "index_digest": dict(json.loads(next(iter(digests))), logical_states=first["regular_states"],
                                 source="diagnostic %s (every K899 process of it agrees)" % args.run_url),
            "q0_identity": {"relation": first["target"]["relation"], "probes_folded": first["target"]["probes"],
                            "scalar": str(first["target"]["recovered_scalar"]),
                            "source": "diagnostic %s, cP899 and kP899 on Q0" % args.run_url},
            "factor_log_table": "inputs/factor_logs_n83_K899.json",
            "factor_log_table_sha256": sha256(table_dst),
            "factor_log_table_oracle_status": diag["checks"]["k899_table_oracle"]["status"],
            "first_600_logs_equal_B_K600": diag["checks"]["k899_first600_equal_B_K600"],
        },
        "diagnostic": {
            "where": args.where, "run_url": args.run_url, "gates": diag["gates"], "derived": d,
            "cold_ms": {"K600": cold600, "K899": cold899}, "rank_stage_ms": {"K600": rank600, "K899": rank899},
            "cold_ratio_K899_over_K600": cold899 / cold600,
            "per_attempt_ratio_K899_over_K600": att899 / att600,
            "predicted_e2e_ratio": (rank600 + cold600) / (rank899 + cold899),
            "process_wall_s": {t: r["process_wall_s"] for t, r in rows.items()},
            "peak_rss_bytes": {t: r["peak_rss_bytes"] for t, r in rows.items()},
            "law": {t: {"probes_mean": r["rank"]["probes_mean"], "law_mean": r["rank"]["law_mean"],
                        "ratio": r["rank"]["probes_mean_over_law"]} for t, r in rows.items() if r.get("rank")},
            "note": "one process per rank arm, one rank seed: a go/no-go diagnostic and the power check's input, "
                    "not timing evidence",
        },
    }
    (EXP / "inputs" / "k899_identity.json").write_text(json.dumps(identity, indent=1, sort_keys=True) + "\n")
    print(json.dumps(identity["diagnostic"]["derived"], indent=1))


if __name__ == "__main__":
    main()
