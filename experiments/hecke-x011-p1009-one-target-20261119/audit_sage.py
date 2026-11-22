"""Independent Sage replay of public point, fixture, and reported logs."""

import json
from pathlib import Path
from sage.all import EllipticCurve, GF

here = Path(__file__).resolve().parent
protocol = json.loads((here / "protocol.json").read_text())
fixture = json.loads((here / "fixture.json").read_text())
public = json.loads((here / "public.json").read_text())
result = json.loads((here / "result.json").read_text())
curve = EllipticCurve(GF(1009), [0, -1, 1, -10, -20])
G = curve(2, 155)
Q = curve(*public["point"])
assert curve.cardinality() == 1020 and G.order() == 1020
assert list(public["point"]) == fixture["point"] == list(result["public_point"])
assert fixture["scalar"] * G == Q
assert all(row["status"] == "verified" and row["scalar"] * G == Q for row in result["runs"])
assert all(row["scalar"] == fixture["scalar"] for row in result["runs"])
source = json.loads((here / protocol["fiber_source"]).read_text())
logs = json.loads((here / "prepared-logs.json").read_text())
assert len(logs) == len(source["source_records"]) == 84
for point, log in zip(source["source_records"], logs):
    assert log * G == curve(*point["point"])
for row in result["runs"]:
    if row["arm"] == "connector":
        shifted = Q + row["shift"] * G
        assert shifted in [curve(*p["point"]) for p in source["source_records"]]
audit = {"schema": "x011-p1009-one-target-audit-v1", "status": "verified",
         "curve_order": int(curve.cardinality()), "generator_order": int(G.order()),
         "public_point": public["point"], "fixture_scalar": fixture["scalar"],
         "run_count": len(result["runs"]), "prepared_logs_replayed": len(logs)}
(here / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
print(json.dumps(audit, indent=2))
