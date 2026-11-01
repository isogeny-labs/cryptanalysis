#!/usr/bin/env python3
"""Re-verify every factor-log table and closure base before any timing.

* B's archived K600 table: the reconcile experiment's
  `verify_log_table.verify` (every [L_j]G = R_j in the pinned pure-Python
  oracle, plus kind, n/a/r, base hash, width and range) against this
  experiment's restored snapshot and B's header, with the table digest
  checked against `protocol.json` (as in the rank-probe run).
* each closure base (M38, M10): `verify_closure.py` on its regenerated
  header and its committed table, with the planted corruptions, both
  digests checked against `protocol.json`, and its logs equal to B's
  archived logs of the same representatives R_0..R_{K'-1}.

Writes one JSON file; exits nonzero on any failure.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "koblitz-n83-reconcile-20261014"))
sys.path.insert(0, str(HERE))
import verify_log_table  # noqa: E402
import verify_closure  # noqa: E402
from verify_receipt import oracle  # noqa: E402


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    bases = json.loads((HERE / "protocol.json").read_text())["online"]["bases"]
    curve = oracle()
    out = {}
    k600 = bases["K600"]
    table = HERE / k600["factor_log_table"]
    if sha256(table) != k600["factor_log_table_sha256"]:
        raise SystemExit("B's factor-log table digest differs from the protocol")
    out["K600"] = verify_log_table.verify(table, HERE / k600["path"], curve)
    b_logs = json.loads(table.read_text())["logs"]
    for name in ("M38", "M10"):
        spec = bases[name]
        if sha256(HERE / spec["path"]) != spec["header_sha256"]:
            raise SystemExit("closure header %s differs from the protocol" % name)
        if sha256(HERE / spec["factor_log_table"]) != spec["factor_log_table_sha256"]:
            raise SystemExit("closure table %s differs from the protocol" % name)
        result = verify_closure.run(HERE / spec["path"], HERE / spec["factor_log_table"], planted=True, curve=curve)
        logs = json.loads((HERE / spec["factor_log_table"]).read_text())["logs"]
        result["logs_equal_B_first_columns"] = logs == b_logs[:spec["orbit_columns"]]
        if not result["logs_equal_B_first_columns"]:
            result["status"] = "FAIL"
        out[name] = result
    out["status"] = "PASS" if all(v["status"] == "PASS" for v in out.values() if isinstance(v, dict)) else "FAIL"
    args.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"status": out["status"], **{k: v["status"] for k, v in out.items() if isinstance(v, dict)}}))
    sys.exit(0 if out["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
