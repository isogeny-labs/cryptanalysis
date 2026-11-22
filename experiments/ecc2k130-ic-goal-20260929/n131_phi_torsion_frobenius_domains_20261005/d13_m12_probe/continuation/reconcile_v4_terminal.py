"""Reconcile the stopped v2 watcher with the later frozen v4 public-Q run.

The v4 run was launched separately from the old watcher. Its terminal receipt
is an upstream gate for the d13/m12 full-candidate preflight; it is never
treated as a verified relation or as a completed IC candidate.
"""

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
PROBE = HERE.parent
RUN = PROBE / "public_q_runs" / "d13_m12_20261009T221148Z"
STATE = HERE / "state.json"
BEFORE = HERE / "state_before_v4_reconciliation_20261115.json"
RECEIPT = HERE / "v4_terminal_reconciliation_20261115.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def write_new(path, data):
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def main():
    assert not BEFORE.exists() and not RECEIPT.exists()
    state = load(STATE)
    assert state["status"] == "WAIT_FOR_R3_DRAIN"
    assert state["target_count"] == 1 and state["batch"] is False
    watcher_pid = state["watcher_pid"]
    process = subprocess.run(["ps", "-p", str(watcher_pid), "-o", "pid="],
                             capture_output=True, text=True, check=False)
    assert not process.stdout.strip(), "old watcher PID still exists"

    started = load(RUN / "started.json")
    result = load(RUN / "result.json")
    audit = load(RUN / "independent_sage_replay.json")
    protocol = PROBE / "public_q_first_relation_protocol_v4.json"
    producer = PROBE / "run_public_q_first_relation_v4.py"
    auditor = PROBE / "audit_public_q_first_relation_v4.py"
    assert result["status"] == "timeout"
    assert len(result["attempts"]) == 1
    assert result["attempts"][0]["stop_reason"] == "parent_timeout"
    assert result["attempts"][0]["solver_status"] == "indeterminate"
    assert result["independently_verified_relation_count"] == 0
    assert audit["status"] == "NO_RELATION_RECORDED"
    assert audit["verified_model_count"] == 0 and audit["verified_rows"] == []
    assert audit["input_sha256"]["result.json"] == digest(RUN / "result.json")
    for record in (started, result, audit):
        assert record["curve_id"] == "EC1N131Ckb1heb5f1998f20b"
        assert record["workload_id"] == state["last_preflight"]["workload_id"]
        assert record["proposal_id"] == state["proposal_id"]
        assert record["target_count"] == 1 and record["candidate_id"] is None
    assert started["protocol_sha256"] == result["protocol_sha256"] == digest(protocol)
    assert started["source_sha256"] == result["source_sha256"] == digest(producer)
    assert audit["source_sha256"] == digest(auditor)
    assert audit["input_sha256"][protocol.name] == digest(protocol)
    assert datetime.fromisoformat(result["finished_utc"]) > datetime.fromisoformat(state["updated_utc"])

    solver_log = RUN / "attempts" / "model_01" / "cryptominisat.stdout.txt"
    lines = solver_log.read_text(errors="replace").splitlines()
    assert not any(line.startswith(("s SATISFIABLE", "s UNSATISFIABLE", "v "))
                   for line in lines)
    receipt = {
        "kind": "d13_m12_v4_terminal_state_reconciliation_v1",
        "status": "PASS_TERMINAL_TIMEOUT_RECONCILED",
        "old_state_sha256": digest(STATE),
        "old_watcher_pid": watcher_pid,
        "old_watcher_pid_absent": True,
        "run_dir": str(RUN),
        "started_sha256": digest(RUN / "started.json"),
        "result_sha256": digest(RUN / "result.json"),
        "audit_sha256": digest(RUN / "independent_sage_replay.json"),
        "protocol_sha256": digest(protocol),
        "producer_sha256": digest(producer),
        "auditor_sha256": digest(auditor),
        "solver_stdout_sha256": digest(solver_log),
        "result_status": result["status"],
        "independently_verified_relation_count": 0,
        "target_count": 1,
        "batch": False,
        "reconciled_utc": datetime.now(timezone.utc).isoformat(),
    }
    # Keep the old watcher state byte-for-byte before updating its mutable gate.
    BEFORE.write_bytes(STATE.read_bytes())
    write_new(RECEIPT, receipt)
    state.update({
        "status": "TERMINAL_NO_VERIFIED_RELATION",
        "result_status": result["status"],
        "run_dir": str(RUN),
        "result_sha256": receipt["result_sha256"],
        "audit_status": audit["status"],
        "audit_sha256": receipt["audit_sha256"],
        "reconciliation_receipt": str(RECEIPT),
        "reconciliation_receipt_sha256": digest(RECEIPT),
        "updated_utc": receipt["reconciled_utc"],
    })
    temporary = STATE.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, STATE)
    print(json.dumps({"status": state["status"], "result_sha256": receipt["result_sha256"],
                      "reconciliation_sha256": digest(RECEIPT)}, sort_keys=True))


if __name__ == "__main__":
    main()
