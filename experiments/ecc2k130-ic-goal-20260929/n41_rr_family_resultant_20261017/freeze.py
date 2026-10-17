"""Freeze the source and input state for the N41 family-resultant gate."""
import hashlib
import json
from pathlib import Path


D = Path(__file__).resolve().parent
ROOT = D.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


sources = [
    "n41_rr_two_slot_quotient_20261016/run.py",
    "n41_rr_two_slot_quotient_20261016/result.json",
    "n41_sixpair_shared_target_20261017/join_audit_result.json",
    "n41_w8_fixed_sum_table_20261009/geometry.json",
    "n41_n131_sixpair_rr_root_span_20261016/run.py",
]
prior = json.loads((ROOT / sources[1]).read_text())
hit = json.loads((ROOT / sources[2]).read_text())
assert prior["fixed_state_ids"] == [116, 47, 128, 34]
assert prior["matches"] == [[12, 122]]
record = {
    "schema": 1,
    "candidate_id": None,
    "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
    "raw_target": hit["raw_target"],
    "fixed_state_ids": prior["fixed_state_ids"],
    "field_modulus": (1 << 41) | (1 << 3) | 1,
    "free_slots": [0, 1],
    "sources": {name: sha(ROOT / name) for name in sources},
    "runner_sha256": sha(D / "run.py"),
    "monitor_sha256": sha(D / "run_monitored.py"),
    "runtime_info_sha256": sha(D / "sage_runtime_info.json"),
    "producer_sha256": sha(Path(__file__)),
    "single_worker": True,
    "wall_cap_s": 30,
    "rss_cap_bytes": 4 * 1024 ** 3,
}
(D / "protocol.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
print(sha(D / "protocol.json"))
