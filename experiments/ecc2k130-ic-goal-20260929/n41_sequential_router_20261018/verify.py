"""Verify frozen staged-router sources, checked proof, and both replays."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


lock = json.loads((HERE / "artifact_lock.json").read_text())
for name, digest in lock["local_sha256"].items():
    assert sha(HERE / name) == digest, name

for protocol_name, result_name, expected_stages in (
    ("protocol_v1.json", "result_v1.json", 4),
    ("protocol.json", "result.json", 38),
):
    protocol = json.loads((HERE / protocol_name).read_text())
    result = json.loads((HERE / result_name).read_text())
    assert protocol["candidate_id"] is None
    assert protocol["worker_count"] == 1
    assert protocol["wall_cap_seconds"] == 120
    assert protocol["rss_cap_bytes"] == 4*1024**3
    assert sha(HERE / "analyze.py") == protocol["script_sha256"]
    for relative, digest in protocol["sources_sha256"].items():
        assert sha(ROOT / relative) == digest, relative
    assert result["protocol_sha256"] == sha(HERE / protocol_name)
    assert result["status"] == "COMPLETE_SEQUENTIAL_ROUTER_SYNTHESIS"
    assert len(result["stages"]) == expected_stages
    assert result["wall_seconds_exploratory"] < 120
    assert result["peak_self_rss_bytes"] < 4*1024**3

result = json.loads((HERE / "result.json").read_text())
audit = json.loads((HERE / "audit_result.json").read_text())
assert audit["status"] == "INDEPENDENT_SEQUENTIAL_ROUTER_AUDIT_PASS"
assert audit["result_sha256"] == sha(HERE / "result.json")
assert audit["v1_result_sha256"] == sha(HERE / "result_v1.json")
assert result["stages"][0]["survivor_count"] == 766
assert result["stages"][-1]["surviving_source_indices"] == [966]
assert [row["degree"] for row in audit["checkpoints"]] == [5,4,3,2,1,0]
assert [row["survivors"] for row in audit["checkpoints"]] == [766,661,380,96,14,1]
assert audit["costs"]["high"]["same_order_static_term_evaluations"] == 1952605
assert audit["costs"]["high"]["staged_term_evaluations"] == 1154126
assert audit["costs"]["low"]["same_order_static_term_evaluations"] == 2242949
assert audit["costs"]["low"]["staged_term_evaluations"] == 1197038

log = (HERE / "lean_check.log").read_text()
assert "'ConditionalRouter.conditional_replacement' depends on axioms: [propext, Quot.sound]" in log
assert "sorryAx" not in log and "error:" not in log
assert (HERE / "lean-toolchain").read_text().strip() == "leanprover/lean4:v4.34.1"
print(json.dumps({"status": "VERIFIED", "stage_domains": 38,
                  "final_source_index": 966, "pinned_files": len(lock["local_sha256"])},
                 sort_keys=True))
