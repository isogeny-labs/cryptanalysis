"""Read-only verification of the prospective decision snapshot."""

import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
GATE = EXP / "n131_d13_m12_precompute_futility_20261115"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    d = json.loads((HERE / "decision.json").read_text())
    pfile = GATE / "protocol_v4.json"
    auditor = GATE / "audit_v4.py"
    assert d["status"] == "READY_FOR_OWNER_STOP_DECISION"
    assert d["process_intervention_performed"] is False
    assert d["frozen_protocol_sha256"] == sha(pfile.read_bytes())
    assert d["auditor_source_sha256"] == sha(auditor.read_bytes())
    assert d["snapshot_source_sha256"] == sha((HERE / "snapshot.py").read_bytes())
    p = json.loads(pfile.read_text())
    assert d["run_id"] == p["run_id"]
    lines = (Path(p["run_dir"]) / "precomputation_attempts.jsonl").read_bytes().splitlines(keepends=True)
    assert len(lines) >= 32
    assert sha(b"".join(lines[:32])) == d["first_32_attempts_sha256"]
    for index, line in enumerate(lines[:32], start=1):
        assert json.loads(line)["relation_index"] == index
    fresh = subprocess.run(["python3", str(auditor)], capture_output=True,
                           text=True, check=True)
    status = json.loads(fresh.stdout)
    assert status["status"] == d["audit"]["status"]
    assert status["status"] == "RECOMMEND_STOP_AFTER_AUDITED_ZERO_YIELD_PANEL"
    assert status["independently_audited_zero_indices"] == list(range(10, 33))
    assert d["audit"]["live_attempts_sha256"] == d["first_32_attempts_sha256"]
    print("PASS_N131_PROSPECTIVE_STOP_DECISION_SNAPSHOT")


if __name__ == "__main__":
    main()
