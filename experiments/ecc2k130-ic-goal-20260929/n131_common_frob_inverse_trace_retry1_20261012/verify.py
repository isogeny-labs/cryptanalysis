"""Read-only verification of the frozen inverse-trace five-pair receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
ORIGINAL = GOAL / "n131_common_frob_inverse_trace_20261012"
PRIOR_TARGET = GOAL / "n41_common_frob_factor_20261012/n131_projection_result.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    frozen = read(HERE / "audit_protocol.json")
    paths = {
        "script": HERE / "audit.py",
        "circuit": HERE / "circuit.py",
        "query_protocol": HERE / "query_protocol.json",
        "query_result": HERE / "query_result.json",
        "target": HERE / "target_result.json",
        "target_stdout": HERE / "target_project.stdout",
        "target_stderr": HERE / "target_project.stderr",
        "public_build": HERE / "public_build_result.json",
        "build_stdout": HERE / "build.stdout",
        "build_stderr": HERE / "build.stderr",
        "solver_stdout": HERE / "solver.stdout",
        "solver_stderr": HERE / "solver.stderr",
        "public_xcnf": HERE / "public.xcnf",
        "control_xcnf": ORIGINAL / "control.xcnf",
        "control_result": ORIGINAL / "control_result.json",
        "fixture": HERE / "fixture.json",
        "prior_target": PRIOR_TARGET,
        "failed_attempt": ORIGINAL / "query_result.json",
    }
    assert frozen["sha256"] == {name: digest(path) for name, path in paths.items()}
    audit = read(HERE / "audit_result.json")
    query = read(HERE / "query_result.json")
    gate_protocol = read(HERE / "gate_protocol.json")
    gate = read(HERE / "gate_result.json")
    original = read(ORIGINAL / "query_result.json")
    assert audit["protocol_sha256"] == digest(HERE / "audit_protocol.json")
    assert audit["status"] == "PASS_N131_INVERSE_TRACE_FROZEN_EVIDENCE_AUDIT"
    assert audit["mathematical_outcome"] == "BOUNDED_UNKNOWN"
    assert query["status"] == "PARENT_TIME_CAP"
    assert audit["phase_ns"]["total"] == sum(
        value for key, value in audit["phase_ns"].items() if key != "total"
    ) == query["target_dependent_attempt_ns"]
    assert audit["phase_ns"]["total"] == 600155675667
    assert gate_protocol["sha256"]["script"] == digest(HERE / "gate_sage.py")
    assert gate_protocol["sha256"]["fixture"] == digest(HERE / "fixture.json")
    assert gate["protocol_sha256"] == digest(HERE / "gate_protocol.json")
    assert gate["status"] == "PASS_CHECKED_SAGE_N131_FIVEPAIR_INVERSE_TRACE_WITNESSES"
    assert len(gate["witnesses"]) == 10
    assert all(item["inverse_trace"] == 0 for item in gate["witnesses"])
    assert len({item["folded_column"] for item in gate["witnesses"]}) == 10
    assert original["status"] == "PRODUCER_FAILURE_TARGET"
    assert "KeyError: 'frobenius_shift'" in (ORIGINAL / "target_project.stderr").read_text()
    assert "does not depend on any axioms" in (HERE / "lean_check.txt").read_text()
    print("PASS_N131_INVERSE_TRACE_READ_ONLY_RECEIPT_CHECK BOUNDED_UNKNOWN")


if __name__ == "__main__":
    main()
