"""Read-only prospective query-yield gate for the live frozen N131 run."""

import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
PROTOCOL = BASE / "protocol.json"
PREFIX = BASE / "first_seven.jsonl"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads(PROTOCOL.read_text())
    assert protocol["audit_source_sha256"] == sha(Path(__file__))
    assert protocol["first_seven_sha256"] == sha(PREFIX)
    assert protocol["prospective_attempt_indices"] == [8, 30]
    assert protocol["maximum_models_per_query"] == 4
    assert protocol["first_rank_check_verified_rows"] == 4390
    assert protocol["preparation_attempt_cap"] == 8192
    run = Path(protocol["run_dir"])
    live_path = run / "precomputation_attempts.jsonl"
    lines = live_path.read_bytes().splitlines(keepends=True)
    frozen = PREFIX.read_bytes().splitlines(keepends=True)
    assert lines[:7] == frozen and len(frozen) == 7
    rows = [json.loads(line) for line in lines]
    assert [row["relation_index"] for row in rows] == list(range(1, len(rows) + 1))
    assert all(row["status"] == "timeout" and row["verified_relation_count"] == 0
               for row in rows[:7])
    observed = rows[7:30]
    productive = [row["relation_index"] for row in observed
                  if row["verified_relation_count"] >= 1]
    if len(rows) < 30:
        status = "PENDING_PROSPECTIVE_QUERIES"
    elif productive:
        status = "CONTINUE_PRODUCTIVE_QUERY_OBSERVED"
    elif (run / "result.json").exists():
        status = "TERMINAL_RUN_REQUIRES_REVIEW"
    else:
        status = "RECOMMEND_STOP_AFTER_ZERO_YIELD_PANEL"
    result = {
        "kind": "n131_d13_m12_prospective_precompute_yield_gate_v1",
        "status": status,
        "candidate_id": protocol["candidate_id"],
        "run_id": protocol["run_id"],
        "protocol_sha256": sha(PROTOCOL),
        "attempts_completed": len(rows),
        "prospective_attempts_completed": len(observed),
        "prospective_productive_indices": productive,
        "prospective_verified_rows": sum(row["verified_relation_count"] for row in observed),
        "first_seven_prefix_sha256": sha(PREFIX),
        "live_attempts_sha256": sha(live_path),
        "run_result_exists": (run / "result.json").exists(),
    }
    print(json.dumps(result, sort_keys=True))
    if len(sys.argv) == 2 and sys.argv[1] == "--write-gate-result":
        assert len(rows) >= 30
        with (BASE / "gate_result.json").open("x") as stream:
            json.dump(result, stream, sort_keys=True, indent=2)
            stream.write("\n")


if __name__ == "__main__":
    assert len(sys.argv) in (1, 2)
    main()
