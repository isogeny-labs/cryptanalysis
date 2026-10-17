"""Freeze the three-family panel and source hashes before running the screen."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source_paths = (
        "n41_n131_sixpair_rr_root_span_20261016/run.py",
        "n41_rr_two_slot_quotient_20261016/run.py",
        "n41_sixpair_shared_target_20261017/join_audit_result.json",
        "n41_w8_fixed_sum_table_20261009/geometry.json",
        "n131_w23_sixpair_density_20261016/audit_result.json",
    )
    hit = json.loads((ROOT / source_paths[2]).read_text())
    protocol = {
        "schema": 1,
        "candidate_id": None,
        "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
        "fixed_state_ids": [hit["pair_rows"][i]["state_id"] for i in (3, 4, 5)],
        "free_slots": [0, 1, 2],
        "raw_target": hit["raw_target"],
        "runner_sha256": sha(D / "run.py"),
        "runtime_info_sha256": sha(D / "sage_runtime_info.json"),
        "sources": {path: sha(ROOT / path) for path in source_paths},
        "single_worker": True,
        "wall_cap_s": 600,
        "rss_cap_bytes": 4 * (1 << 30),
    }
    (D / "protocol.json").write_text(json.dumps(protocol, sort_keys=True, indent=2) + "\n")
    print(json.dumps({k: protocol[k] for k in ("fixed_state_ids", "raw_target", "wall_cap_s")}, sort_keys=True))


if __name__ == "__main__":
    main()
