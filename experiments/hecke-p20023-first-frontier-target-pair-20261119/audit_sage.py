"""Independent accepted-Sage replay of prepared logs and both target arms."""

import json
from hashlib import sha256
from pathlib import Path
from sage.all import EllipticCurve, GF

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "protocol.json").read_text())
pre_run = json.loads((HERE / "pre-run.json").read_text())
assert sha256((HERE / "protocol.json").read_bytes()).hexdigest() == pre_run["protocol_sha256"]
assert sha256((HERE / "public.json").read_bytes()).hexdigest() == pre_run["public_sha256"]
fresh = json.loads((HERE / protocol["fresh_source"]).read_text())
solved = json.loads((HERE / protocol["solved_table"]).read_text())
public = json.loads((HERE / "public.json").read_text())
fixture = json.loads((HERE / "fixture.json").read_text())
result = json.loads((HERE / "result.json").read_text())
assert result["protocol_sha256"] == pre_run["protocol_sha256"]
assert result["public_sha256"] == pre_run["public_sha256"]
E = EllipticCurve(GF(20023), [0, -1, 1, -10, -20])
G = 5 * E(1, 8630)
Q = E(*public["point"])
assert G.order() == 4021 and E.cardinality() == 20105
reps = fresh["column_representatives"]
logs = solved["logs_by_column"]
assert len(reps) == len(logs) == 1760
projected = [5 * E(*rep) for rep in reps]
assert len(set(projected)) == 1760
assert all(int(log) * G == p for log, p in zip(logs, projected))
assert Q not in projected
assert public["point"] == fixture["point"] == list(result["public_point"])
assert fixture["scalar"] * G == Q
assert fixture["scalar"] == int.from_bytes(
    sha256(f"{protocol['target_seed']}:{fixture['counter']}".encode()).digest(), "big") % 4021
for counter in range(fixture["counter"]):
    candidate = int.from_bytes(sha256(f"{protocol['target_seed']}:{counter}".encode()).digest(), "big") % 4021
    assert candidate == 0 or candidate * G in projected
assert all(row["status"] == "verified" and row["scalar"] * G == Q for row in result["runs"])
assert all(row["scalar"] == fixture["scalar"] for row in result["runs"])
for row in result["runs"]:
    if row["arm"] == "connector":
        assert Q + row["shift"] * G in projected
        assert all(Q + k * G not in projected for k in range(row["shift"]))
audit = {"schema": "hecke-p20023-first-frontier-target-pair-audit-v1",
         "status": "verified", "curve_order": int(E.cardinality()),
         "subgroup_order": int(G.order()), "prepared_logs_replayed": len(logs),
         "public_point": public["point"], "fixture_scalar": fixture["scalar"],
         "run_count": len(result["runs"])}
(HERE / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
print(json.dumps(audit, indent=2))
