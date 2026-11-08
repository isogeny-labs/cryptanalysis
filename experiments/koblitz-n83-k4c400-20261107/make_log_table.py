#!/usr/bin/env python3
"""Derive the D4 closure base's factor-log table from the M38 table, deterministically.

The D4 header (`make_closure_base.py --columns 4 --norm 165`, the fieldops
experiment's builder, run unchanged) takes as its K' = 4 column
representatives B's first four K600 representatives R_0..R_3. The M38 header
(K' = 16) takes B's first sixteen, so R_0..R_3 are the same four points and
their logs are the first four logs of `inputs/factor_logs_n83_closure_M38.json`.
The D4 table is that table truncated to four logs with the D4 header's
`base_hash` and `orbit_columns`. Nothing is ranked or computed here; the
table is checked independently by `verify_closure.py --table` (every
[L_c]G = R_c and [w L_c]G = P in the pinned oracle) and by every rank process
of the run (its own produced table must equal this one log for log).

`--check` regenerates and requires byte identity with
`inputs/factor_logs_n83_closure_D4.json`.
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
M38_TABLE = HERE / "inputs" / "factor_logs_n83_closure_M38.json"
D4_HEADER = HERE / "snapshots" / "closure" / "base_n83_closure_D4.jsonl"
OUT = HERE / "inputs" / "factor_logs_n83_closure_D4.json"
COLUMNS = 4


def derive():
    source = json.loads(M38_TABLE.read_text())
    header = json.loads(D4_HEADER.read_bytes().split(b"\n", 1)[0])
    if header["orbit_columns"] != COLUMNS:
        raise ValueError("the D4 header does not have %d columns" % COLUMNS)
    table = {key: source[key] for key in ("a", "kind", "log_definition", "n", "schema_version", "subgroup_order")}
    table.update({
        "base_hash": header["base_hash"],
        "logs": source["logs"][:COLUMNS],
        "orbit_columns": COLUMNS,
        "provenance": {"derived": "first %d logs of the M38 table (same column representatives: B's K600 first K')"
                                  % COLUMNS,
                       "source_table": "inputs/factor_logs_n83_closure_M38.json",
                       "source_base_hash": source["base_hash"],
                       "checked_by": "verify_closure.py --base --table --planted in the pinned oracle, and "
                                     "every rank process (produced table equals this one)"},
    })
    return json.dumps(table, indent=1, sort_keys=True) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = derive()
    if args.check:
        if OUT.read_text() != text:
            sys.exit("inputs/factor_logs_n83_closure_D4.json differs from the derived table")
        print("table_verified=" + str(OUT))
        return
    OUT.write_text(text)
    print(str(OUT))


if __name__ == "__main__":
    main()
