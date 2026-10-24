"""Recompute producer ranks and target membership with Sage GF(2) matrices."""
import hashlib
import json
import time
from pathlib import Path

from sage.all import GF, matrix

HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg = json.loads((HERE / "audit_protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_TRIPLE_X_RANK_AUDIT"
for name, item in cfg["sources"].items():
    assert sha(item["path"]) == item["sha256"], name
result = json.loads((HERE / "result_v2.json").read_text())
sets = json.loads((HERE / "x_sets_v2.json").read_text())
assert result["x_sets_sha256"] == sha(HERE / "x_sets_v2.json")
started = time.monotonic()
rows_checked = target_checks = 0
for field, n in (("n41", 41), ("n131", 131)):
    values = set()
    assert len(sets[field]) == len(result[field]["rows"])
    for index, local in enumerate(sets[field]):
        assert len(local) == 32 and len(set(local)) == 32
        assert all(0 <= value < (1 << n) for value in local)
        values.update(local)
        ordered = sorted(values)
        base = ordered[0]
        bits = lambda value: [(value >> j) & 1 for j in range(n)]
        mat = matrix(GF(2), [bits(value ^ base) for value in ordered[1:]])
        actual_rank = mat.rank()
        row = result[field]["rows"][index]
        assert row["first_family_count"] == index + 1
        assert row["distinct_x"] == len(values)
        assert row["affine_rank"] == actual_rank
        assert row["affine_codimension"] == n - actual_rank
        for name, x in result[field]["residual_x"].items():
            augmented = mat.stack(matrix(GF(2), [bits(x ^ base)]))
            accepted = augmented.rank() == actual_rank
            assert row["target_checks"][name] == {
                "exact_x_member": x in values,
                "affine_hull_contains": accepted}
            target_checks += 1
        rows_checked += 1
out = {"status": "PASS_INDEPENDENT_TRIPLE_X_RANK_AUDIT",
       "candidate_id": None,
       "rows_checked": rows_checked, "target_checks": target_checks,
       "wall_seconds": time.monotonic() - started,
       "producer_result_sha256": sha(HERE / "result_v2.json"),
       "protocol_sha256": sha(HERE / "audit_protocol.json")}
(HERE / "audit_result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(json.dumps(out, sort_keys=True))
