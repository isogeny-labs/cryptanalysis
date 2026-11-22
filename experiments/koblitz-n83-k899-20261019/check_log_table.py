#!/usr/bin/env python3
"""Re-verify both frozen factor-log tables before any timing.

For each K in `protocol.json` `online.k`: the table digest against the
protocol, then the reconcile experiment's `verify_log_table.verify` (every
[L_j]G = R_j in the pinned pure-Python oracle, plus kind, n/a/r, base hash,
width and range) against that K's base. Then the nesting check: the K600
base is an exact prefix of the K899 base (representatives, points, labels),
so the first 600 K899 logs must equal B's K600 logs (discrete logs of fixed
points are unique mod r). Exits nonzero on any failure.
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
from verify_receipt import oracle  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    ks = json.loads((HERE / "protocol.json").read_text())["online"]["k"]
    curve = oracle()
    result = {"tables": {}}
    ok = True
    for k, spec in sorted(ks.items()):
        table = (HERE / spec["factor_log_table"]).resolve()
        if hashlib.sha256(table.read_bytes()).hexdigest() != spec["factor_log_table_sha256"]:
            raise SystemExit("K%s factor-log table digest differs from the protocol" % k)
        check = verify_log_table.verify(table, HERE / spec["base"], curve)
        result["tables"][k] = check
        ok &= check["status"] == "PASS"
    base6 = json.loads((HERE / ks["600"]["base"]).read_text())
    base9 = json.loads((HERE / ks["899"]["base"]).read_text())
    prefix = all(base9[key][:len(base6[key])] == base6[key] for key in
                 ("factor_base_representatives", "factor_base_point_coordinates", "factor_base_point_labels"))
    logs6 = json.loads((HERE / ks["600"]["factor_log_table"]).read_text())["logs"]
    logs9 = json.loads((HERE / ks["899"]["factor_log_table"]).read_text())["logs"]
    result["k600_base_is_prefix_of_k899_base"] = prefix
    result["k899_first_600_logs_equal_k600"] = logs9[:len(logs6)] == logs6
    ok &= prefix and result["k899_first_600_logs_equal_k600"]
    result["status"] = "PASS" if ok else "FAIL"
    args.out.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "prefix": prefix,
                      "first600": result["k899_first_600_logs_equal_k600"]}))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
