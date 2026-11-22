"""Read-only custody and decision audit for triple-x prefix capacity."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda name: json.loads((HERE / name).read_text())
first = read("failure_v1.json")
assert first["status"] == "PRODUCER_FAILURE_WRONG_POSITIVE_TARGET"
assert first["exit_code"] == 1
assert first["protocol_sha256"] == sha(HERE / "protocol.json")
assert first["producer_sha256"] == sha(HERE / "run_sage.py")
freeze_fail = read("freeze_failure_v2.json")
assert freeze_fail["status"] == "PRE_RUN_FREEZE_FAILURE_MISSING_SOURCE"
assert freeze_fail["protocol_written"] is False
for name in ("protocol.json", "protocol_v2.json", "audit_protocol.json"):
    cfg = read(name)
    for source, item in cfg["sources"].items():
        assert sha(item["path"]) == item["sha256"], (name, source)
result = read("result_v2.json")
audit = read("audit_result.json")
assert result["status"] == "PASS_TRIPLE_X_PREFIX_CAPACITY"
assert result["candidate_id"] is None
assert result["protocol_sha256"] == sha(HERE / "protocol_v2.json")
assert result["x_sets_sha256"] == sha(HERE / "x_sets_v2.json")
assert audit["status"] == "PASS_INDEPENDENT_TRIPLE_X_RANK_AUDIT"
assert audit["rows_checked"] == 13 and audit["target_checks"] == 23
assert audit["producer_result_sha256"] == sha(HERE / "result_v2.json")
assert audit["protocol_sha256"] == sha(HERE / "audit_protocol.json")
assert [row["affine_rank"] for row in result["n41"]["rows"]] == [31, 41, 41, 41, 41, 41, 41, 41]
assert [row["affine_rank"] for row in result["n131"]["rows"]] == [31, 63, 95, 127, 131]
assert result["n131"]["rows"][0]["target_checks"]["constructed"]["exact_x_member"]
for row in result["n131"]["rows"][:4]:
    assert not row["target_checks"]["public"]["affine_hull_contains"]
last = result["n131"]["rows"][4]["target_checks"]["public"]
assert last == {"exact_x_member": False, "affine_hull_contains": True}
lean_log = (HERE / "lean_reuse.log").read_text()
assert "error:" not in lean_log and "sorryAx" not in lean_log
assert "'ThreeCodeSign.atMost32Cover' depends on axioms: [propext, Quot.sound]" in lean_log
print("PASS_TRIPLE_X_PREFIX_CAPACITY_ARCHIVE")
