"""Independent modular collision census and result-integrity check."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "protocol.json").read_text())
result = json.loads((HERE / "result.json").read_text())
assert result["protocol_sha256"] == hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest()
assert result["source_sha256"] == hashlib.sha256((HERE / "run_sage.py").read_bytes()).hexdigest()
assert result["status"] == "PASS"
q = protocol["subgroup_order"]
assert q == 331 and len(result["rows"]) == q
candidates = {(18 * j - i) % q for i in range(18) for j in range(18)}
assert len(candidates) == 324
collisions = 0
for w, row in enumerate(result["rows"]):
    expected = [[i, j] for i in range(18) for j in range(18)
                if (w + i - 18 * j) % q == 0]
    assert row == {"w": w, "collisions": expected,
                   "first_collision": expected[0] if expected else None}
    collisions += len(expected)
assert result["stored_forms"] == 36
assert result["active_cross_pairs"] == len(candidates) == 324
assert result["group_equality_tests"] == q * 324
assert result["collision_count"] == collisions == 324
assert result["hit_targets"] == len(candidates) == 324
print(json.dumps({"schema": "xedni-symbolic-collision-audit-v1", "status": "PASS",
                  "result_sha256": hashlib.sha256((HERE / "result.json").read_bytes()).hexdigest(),
                  "targets": q, "hit_targets": 324, "collisions": collisions,
                  "group_equality_tests": q * 324}, sort_keys=True))
