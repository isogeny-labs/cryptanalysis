"""Independent Sage replay of all noncyclic coordinates and one-target runs."""

import json
from pathlib import Path
from sage.all import EllipticCurve, GF

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "protocol.json").read_text())
source = json.loads((HERE / protocol["fiber_source"]).read_text())
coords = json.loads((HERE / "prepared-coordinates.json").read_text())
public = json.loads((HERE / "public.json").read_text())
fixture = json.loads((HERE / "fixture.json").read_text())
result = json.loads((HERE / "result.json").read_text())
E = EllipticCurve(GF(941), [0, -1, 1, -10, -20])
A, B = E(32, 685), E(43, 695)
Q = E(*public["point"])
assert E.cardinality() == 900 and A.order() == 180 and B.order() == 60
assert len({a*A + b*B for a in range(180) for b in range(60)}) == 900
points = [E(*r["point"]) for r in source["source_records"]["2"]]
assert len(points) == len(coords) == 112
assert all(a*A + b*B == p for (a, b), p in zip(coords, points))
subgroup = {k*A for k in range(180)}
assert len(subgroup.intersection(points)) == result["target_subgroup_prepared_points"] == 23
assert public["point"] == fixture["point"] == list(result["public_point"])
assert fixture["scalar"] * A == Q
assert all(row["status"] == "verified" and row["scalar"] * A == Q for row in result["runs"])
assert all(row["scalar"] == fixture["scalar"] for row in result["runs"])
for row in result["runs"]:
    if row["arm"] == "connector":
        assert Q + row["shift"] * A in points
audit = {"schema": "x011-p941-one-target-audit-v1", "status": "verified",
         "curve_order": int(E.cardinality()), "generator_orders": [int(A.order()), int(B.order())],
         "pair_span": 900, "prepared_coordinates_replayed": len(coords),
         "subgroup_fiber_points": 23, "public_point": public["point"],
         "fixture_scalar": fixture["scalar"], "run_count": len(result["runs"])}
(HERE / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
print(json.dumps(audit, indent=2))
