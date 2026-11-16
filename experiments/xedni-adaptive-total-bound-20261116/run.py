"""Replay exact controls against the adaptive stage and bucket-sum bounds."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
protocol = json.loads((ROOT / "protocol.json").read_text())
assert protocol["schema"] == "xedni-adaptive-total-bound-protocol-v1"


def read_control(spec):
    path = ROOT.parent.parent / spec["artifact"]
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == spec["sha256"]
    return json.loads(data)


z7 = read_control(protocol["controls"]["z7_exhaustive_execution_result"])
z101 = read_control(protocol["controls"]["z101_fixed_bucket_result"])
assert z7["status"] == z101["status"] == "PASS"
stage_rows = []
for k_text, row in sorted(z7["by_length"].items(), key=lambda x: int(x[0])):
    k = int(k_text)
    lhs = max(7 - k * k, 0) * row["first_hit"]
    rhs = k * row["live"]
    assert lhs <= rhs
    stage_rows.append({"k": k, "first_hit": row["first_hit"],
                       "live": row["live"], "left_bound": lhs,
                       "right_bound": rhs, "bound_holds": True})
bucket_sums = []
for k in range(2, 6):
    rows = [row for row in z101["rows"] if row["k"] == k]
    assert len(rows) == 3
    lhs = sum(int(row["left_bound"]) for row in rows)
    rhs = sum(int(row["right_bound"]) for row in rows)
    assert lhs <= rhs
    bucket_sums.append({"k": k, "buckets": len(rows),
                        "left_bound": str(lhs), "right_bound": str(rhs),
                        "bound_holds": True})
result = {"schema": "xedni-adaptive-total-bound-result-v1", "status": "PASS",
          "z7_stage_rows": stage_rows, "z101_fixed_bucket_sums": bucket_sums,
          "frozen_z101_buckets": len(z101["rows"])}
(ROOT / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": "PASS", "z7_stages": len(stage_rows),
                  "z101_buckets": len(z101["rows"])}, sort_keys=True))
