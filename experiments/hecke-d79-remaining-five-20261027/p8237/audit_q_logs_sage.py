"""Check the Fq relation kernel against actual projected class-point logs."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
POST = json.loads((HERE / "post_inputs.json").read_text())
raw = (ROOT / POST["class_receipt"]).read_bytes()
assert hashlib.sha256(raw).hexdigest() == POST["class_receipt_sha256"]
DATA = json.loads(raw)
ANALYSIS = json.loads((HERE / "analysis.json").read_text())
AUDIT = json.loads((HERE / "audit.json").read_text())
assert AUDIT["status"] == "PASS"


def rows(items, key):
    return [{int(i): int(x) for i, x in item[key].items()}
            for item in items]


def main():
    p, n, q = DATA["p"], DATA["curve_order"], DATA["largest_prime_factor"]
    assert (p, n, q) == (8237, 8255, 127)
    E = EllipticCurve(GF(p), [0, -1, 1, -10, -20])
    assert int(E.cardinality()) == n
    points = [E(x, y) for x, y in DATA["class_points"]]
    H = next((n//q)*P for P in points if (n//q)*P != E(0))
    assert H != E(0) and q*H == E(0)
    table = {}
    Q = E(0)
    for k in range(q):
        assert Q not in table
        table[Q] = k
        Q += H
    assert Q == E(0) and len(table) == q
    logs = [table[(n//q)*P] for P in points]
    base = rows(DATA["base_rows"], "row")
    direct = rows(ANALYSIS["direct"]["candidates"], "row")
    hecke = rows(ANALYSIS["hecke"]["candidates"], "row")
    for r in base + direct + hecke:
        assert sum(v*logs[i] for i, v in r.items()) % q == 0
    out = {"schema": "hecke-d79-p8237-q-log-audit-v1", "status": "PASS",
           "p": p, "curve_order": n, "subgroup_order": q,
           "generator": [int(H[0]), int(H[1])],
           "class_point_logs": logs, "nonzero_class_log_count": sum(k != 0 for k in logs),
           "annihilated_rows": {"base": len(base), "direct": len(direct),
                                 "hecke_trace": len(hecke)},
           "producer_sha256": POST["class_receipt_sha256"]}
    (HERE / "q-log-audit.json").write_text(json.dumps(out, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"status": out["status"], "rows": out["annihilated_rows"]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
