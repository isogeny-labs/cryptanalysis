#!/usr/bin/env python3
"""Run bounded, read-only SQL against the local LMFDB curve index."""

import argparse
import json
from pathlib import Path
import re

import duckdb

ROOT = Path(__file__).resolve().parent
TABLES = ("ec_q", "ec_nf", "g2c", "av_fq")


def json_value(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--table", choices=TABLES, default="ec_q",
                        help="table for --label, --conductor, --schema, or --metadata")
    command = parser.add_mutually_exclusive_group(required=True)
    command.add_argument("--label", help="LMFDB or Cremona curve label")
    command.add_argument("--conductor", type=int, help="exact conductor over Q")
    command.add_argument("--sql", help="one SELECT or WITH query using completed local views")
    command.add_argument("--list", action="store_true", help="list completed local indexes")
    command.add_argument("--schema", action="store_true", help="show local columns")
    command.add_argument("--metadata", action="store_true", help="show provenance")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    manifests = {}
    for table in TABLES:
        manifest_path = args.dataset_dir / f"{table}_manifest.json"
        parquet_path = args.dataset_dir / f"{table}.parquet"
        if manifest_path.exists() and parquet_path.exists():
            candidate = json.loads(manifest_path.read_text())
            if candidate.get("complete") is True:
                manifests[table] = candidate
    if args.list:
        print(json.dumps({table: {"source": item["source"], "row_count": item["row_count"],
                                  "ended_utc": item["ended_utc"]}
                          for table, item in manifests.items()}, indent=2))
        return
    if args.table not in manifests and args.sql is None:
        parser.error(f"local {args.table} index is not complete; see README.md")
    manifest = manifests.get(args.table)
    if args.metadata:
        print(json.dumps(manifest, indent=2))
        return
    if not 1 <= args.limit <= 10_000:
        parser.error("--limit must be between 1 and 10000")

    con = duckdb.connect(database=":memory:")
    for table in manifests:
        con.read_parquet(str(args.dataset_dir / f"{table}.parquet")).create_view(table)
    if args.schema:
        result = con.execute(f"DESCRIBE {args.table}")
    elif args.label is not None:
        if args.table == "ec_q":
            result = con.execute(
                "SELECT * FROM ec_q WHERE lmfdb_label = ? OR clabel = ? LIMIT ?",
                [args.label, args.label, args.limit],
            )
        else:
            result = con.execute(
                f"SELECT * FROM {args.table} WHERE label = ? LIMIT ?",
                [args.label, args.limit],
            )
    elif args.conductor is not None:
        conductor_column = {"ec_q": "conductor", "ec_nf": "conductor_norm", "g2c": "cond"}.get(args.table)
        if conductor_column is None:
            parser.error("--conductor is not defined for av_fq; use --sql with q or p")
        result = con.execute(
            f"SELECT * FROM {args.table} WHERE {conductor_column} = ? LIMIT ?",
            [args.conductor, args.limit],
        )
    else:
        sql = args.sql.strip().removesuffix(";").strip()
        if not re.match(r"(?is)^(SELECT|WITH)\b", sql) or ";" in sql:
            parser.error("--sql accepts one SELECT or WITH query")
        result = con.execute(f"SELECT * FROM ({sql}) AS result LIMIT ?", [args.limit])

    names = [item[0] for item in result.description]
    rows = [dict(zip(names, map(json_value, row))) for row in result.fetchall()]
    print(json.dumps({
        "selected_table": args.table if args.sql is None else None,
        "available_datasets": {
            table: {"source": item["source"], "started_utc": item["started_utc"],
                    "ended_utc": item["ended_utc"], "row_count": item["row_count"]}
            for table, item in manifests.items()
        },
        "returned_rows": len(rows),
        "rows": rows,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
