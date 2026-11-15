"""Preserve the prospective yield decision without changing the live runner."""

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
GATE = EXP / "n131_d13_m12_precompute_futility_20261115"
FROZEN = GATE / "protocol_v4.json"
AUDITOR = GATE / "audit_v4.py"
RESULT = HERE / "decision.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    assert not RESULT.exists(), "decision snapshot already exists"
    p = json.loads(FROZEN.read_text())
    run = Path(p["run_dir"])
    attempts = run / "precomputation_attempts.jsonl"
    lines = attempts.read_bytes().splitlines(keepends=True)
    assert len(lines) >= 32
    assert [json.loads(line)["relation_index"] for line in lines[:32]] == list(range(1, 33))
    check = subprocess.run(["python3", str(AUDITOR)], capture_output=True,
                           text=True, check=True)
    decision = json.loads(check.stdout)
    assert decision["status"] == "RECOMMEND_STOP_AFTER_AUDITED_ZERO_YIELD_PANEL"
    assert decision["independently_audited_zero_indices"] == list(range(10, 33))
    assert decision["productive_indices"] == []
    assert decision["non_timeout_zero_indices"] == []
    assert decision["protocol_sha256"] == sha(FROZEN.read_bytes())
    # The supervisor identity is recorded for review. Its PID alone is not a
    # future authorization to signal a possibly reused process identifier.
    ps = subprocess.run(["ps", "-p", "53627", "-o", "pid=", "-o", "ppid=",
                         "-o", "lstart=", "-o", "stat=", "-o", "command="],
                        capture_output=True, text=True, check=True)
    assert "run_d13_m12_single_target.py" in ps.stdout
    child = subprocess.run(["pgrep", "-P", "53627", "-fl", "."],
                           capture_output=True, text=True, check=False)
    record = {
        "kind": "n131_d13_m12_prospective_futility_decision_snapshot_v1",
        "status": "READY_FOR_OWNER_STOP_DECISION",
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "frozen_protocol_sha256": sha(FROZEN.read_bytes()),
        "auditor_source_sha256": sha(AUDITOR.read_bytes()),
        "snapshot_source_sha256": sha(Path(__file__).read_bytes()),
        "run_id": p["run_id"],
        "candidate_id": p["candidate_id"],
        "run_dir": str(run),
        "first_32_attempts_sha256": sha(b"".join(lines[:32])),
        "attempts_present_at_capture": len(lines),
        "audit": decision,
        "auditor_stderr": check.stderr,
        "supervisor_ps_at_capture": ps.stdout.strip(),
        "children_at_capture": child.stdout.splitlines(),
        "planned_action_if_approved": "Recheck supervisor creation time and run ID; independently audit latest append-only prefix; send SIGTERM to live supervisor and any matching child; preserve archive and write a separate censored terminal sidecar. Do not edit the frozen candidate or represent the partial precomputation as a complete solve.",
        "process_intervention_performed": False,
    }
    RESULT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": record["status"], "audit_status": decision["status"],
                      "prospective_attempts_completed": decision["prospective_attempts_completed"],
                      "attempts_present_at_capture": len(lines)}, sort_keys=True))


if __name__ == "__main__":
    main()
