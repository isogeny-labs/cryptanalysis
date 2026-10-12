"""Read-only verification of frozen N131 ten-pair result artifacts."""

import hashlib
import json
from pathlib import Path

import archive

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    archive.verify()
    control, frozen, plan, solver, sage, audit = (
        json.loads((HERE / name).read_text()) for name in (
            "control_result.json", "protocol.json", "solver_protocol.json",
            "solver_result.json", "sage_audit_result.json", "audit_result.json"))
    assert control["status"] == "PASS_TENPAIR_CONSTRUCTED_ASSIGNMENT"
    assert control["protocol_sha256"] == sha(HERE / "protocol.json")
    assert frozen["source_sha256"]["tenpair"] == sha(HERE / "tenpair.py")
    assert plan["runner_sha256"] == sha(HERE / "run_preflight.py")
    assert solver["solver_protocol_sha256"] == sha(HERE / "solver_protocol.json")
    assert sage["status"] == "PASS_SAGE_TENPAIR_SOURCE_SUM_AND_TARGET"
    assert sage["sha256"]["audit_script"] == sha(HERE / "audit_fixture_sage.py")
    assert audit["status"] == "PASS_N131_TENPAIR_PREFLIGHT_AUDIT"
    assert audit["classified_solver_status"] == "CENSORED_TIME"
    for name, digest in audit["sha256"].items():
        filename = {"auditor": "audit_preflight.py", "protocol": "protocol.json",
                    "control": "control_result.json",
                    "solver_protocol": "solver_protocol.json",
                    "solver_result": "solver_result.json",
                    "sage_audit": "sage_audit_result.json",
                    "archive_receipt": "archive_receipt.json"}[name]
        assert digest == sha(HERE / filename), name
    assert solver["status_lines"] == ["s INDETERMINATE"]
    assert solver["stderr_sha256"] == sha(HERE / "solver.stderr.txt")
    assert solver["stdout_sha256"] == sha(HERE / "solver.stdout.txt")
    print("PASS_N131_TENPAIR_FROZEN_RECEIPTS", flush=True)


if __name__ == "__main__":
    main()
