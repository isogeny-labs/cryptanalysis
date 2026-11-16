"""Independent Sage replay of every constructed tangent lift."""
import hashlib
import json
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
protocol = json.loads((HERE / "protocol.json").read_text())
registry_path = ROOT / "xedni-crt-band-panel-20261115" / "result.json"
assert hashlib.sha256(registry_path.read_bytes()).hexdigest() == protocol["source_registry_sha256"]
registry = {r["field_prime"]: r for r in json.loads(registry_path.read_text())["fields"]}
result = json.loads((HERE / "result.json").read_text())
assert hashlib.sha256((HERE / "rows.jsonl").read_bytes()).hexdigest() == result["rows_sha256"]

counts = Counter()
for line in (HERE / "rows.jsonl").open():
    row = json.loads(line)
    p = row["field_prime"]
    q = row["subgroup_order"]
    field = registry[p]
    assert q == field["subgroup_order"]
    finite = EllipticCurve(GF(p), [-1, -2])
    G = finite(*field["generator"])
    assert q*G == finite(0)
    target = row["fixture_scalar"]*G
    t1,t2 = row["offsets"]
    U,V = target-t1*G, target-t2*G
    assert [int(U[0]),int(U[1])] == row["U"]
    assert [int(V[0]),int(V[1])] == row["V"]
    assert bool(2*U == V) == row["public_relation_diagnostic"]

    rational = EllipticCurve(QQ, [row["A"], row["B"]])
    P = rational(row["x"], row["y"])
    R = rational(*row["R"])
    assert 2*P == R
    assert rational.discriminant() == row["discriminant"]
    assert row["A"] % p == p-1 and row["B"] % p == p-2
    assert int(rational.discriminant()) % p != 0
    reduced_P = finite(GF(p)(P[0]), GF(p)(P[1]))
    reduced_R = finite(GF(p)(R[0]), GF(p)(R[1]))
    assert reduced_P == U and reduced_R == 2*U
    matches = reduced_R == V
    assert matches == row["matches_V"] == row["public_relation_diagnostic"]
    if matches:
        assert row["derived_scalar"]*G == target
        counts["matching_scalar_replay"] += 1
    counts["constructed_verified"] += 1
    counts["matches_V"] += int(matches)
    counts["nonmatching_V"] += int(not matches)

assert counts["constructed_verified"] == 512
assert counts["matches_V"] == 10 and counts["nonmatching_V"] == 502
audit = {"schema": "xedni-constructive-doubling-lift-sage-audit-v1",
         "status": "PASS", "counts": dict(sorted(counts.items())),
         "constructed_rows_sha256": result["rows_sha256"]}
(HERE / "audit-sage.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
print(json.dumps(audit, indent=2, sort_keys=True))
