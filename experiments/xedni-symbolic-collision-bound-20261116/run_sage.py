"""Full p=313 group-operation replay of the frozen symbolic collision schedule."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "protocol.json").read_text())
assert (protocol["field_prime"], protocol["subgroup_order"]) == (313, 331)
E = EllipticCurve(GF(313), [-1, -2])
G = E(protocol["generator"])
assert G != E(0) and 331 * G == E(0)
constant_points = [18 * j * G for j in range(18)]
rows = []
comparison_count = 0
for w in range(331):
    Q = w * G
    target_points = [Q + i * G for i in range(18)]
    collisions = []
    for i, point in enumerate(target_points):
        for j, constant in enumerate(constant_points):
            comparison_count += 1
            if point == constant:
                collisions.append([i, j])
                assert (w + i - 18 * j) % 331 == 0
    rows.append({"w": w, "collisions": collisions,
                 "first_collision": collisions[0] if collisions else None})

result = {"schema": "xedni-symbolic-collision-result-v1", "status": "PASS",
          "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest(),
          "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          "targets": 331, "stored_forms": 36, "active_cross_pairs": 324,
          "group_equality_tests": comparison_count,
          "hit_targets": sum(bool(row["collisions"]) for row in rows),
          "collision_count": sum(len(row["collisions"]) for row in rows),
          "rows": rows}
print(json.dumps(result, sort_keys=True, indent=2))
