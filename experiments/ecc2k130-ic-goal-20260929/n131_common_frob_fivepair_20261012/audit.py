"""Rebuild both N131 XCNFs and audit the capped public solver receipt."""

import hashlib
import json
import tempfile
import time
from pathlib import Path

import circuit

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
TARGET = GOAL / "n41_common_frob_factor_20261012/n131_projection_result.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    protocol = read(HERE / "audit_protocol.json")
    files = {"source": HERE / "audit.py", "circuit": HERE / "circuit.py",
             "fixture": HERE / "fixture.json", "target": TARGET,
             "control_result": HERE / "control_result.json",
             "public_build": HERE / "public_build_result.json",
             "query_result": HERE / "query_result.json",
             "control_xcnf": HERE / "control.xcnf",
             "public_xcnf": HERE / "public.xcnf",
             "solver_stdout": HERE / "solver.stdout",
             "solver_stderr": HERE / "solver.stderr"}
    assert protocol["status"] == "FROZEN_BEFORE_N131_TERMINAL_AUDIT"
    assert protocol["sha256"] == {name: sha(path) for name, path in files.items()}
    fixture, target = read(HERE / "fixture.json"), read(TARGET)
    control, public = read(HERE / "control_result.json"), read(HERE / "public_build_result.json")
    query = read(HERE / "query_result.json")
    assert fixture["status"] == "PASS_N131_FIVEPAIR_CONSTRUCTED_CHART"
    assert control["status"] == "PASS_COMPLETE_N131_FIVEPAIR_ASSIGNMENT"
    assert target["status"] == "PASS_CHECKED_SAGE_N131_COMMON_FACTOR_TARGET"
    assert query["status"] == query["solver"]["stop_reason"] == "PARENT_TIME_CAP"
    assert query["solver"]["exit_code"] == -9
    assert query["solver_terminal_lines"] == []
    assert query["peak_combined_rss_bytes_sampled"] < 4*1024**3
    assert query["solver"]["wall_ns"] > 480*10**9
    assert query["target_dependent_attempt_ns"] >= 600*10**9
    assert query["target_dependent_attempt_ns"] < 601*10**9
    assert query["build"]["wall_ns"]+query["solver"]["wall_ns"] <= query["target_dependent_attempt_ns"]
    bookkeeping = (query["target_dependent_attempt_ns"]-
                   query["build"]["wall_ns"]-query["solver"]["wall_ns"])
    assert bookkeeping >= 0
    stdout = (HERE / "solver.stdout").read_text(errors="replace")
    assert [line for line in stdout.splitlines() if line.startswith("s ")] == []
    assert sum(line.startswith("c rst") for line in stdout.splitlines()) == query["solver_restart_rows"]
    assert query["solver"]["stdout_sha256"] == sha(HERE / "solver.stdout")
    assert query["solver"]["stderr_sha256"] == sha(HERE / "solver.stderr")
    assert query["build"]["stdout_sha256"] == sha(HERE / "build.stdout")
    assert query["build"]["stderr_sha256"] == sha(HERE / "build.stderr")
    assert (HERE / "solver.stderr").read_text() == ""
    assert (HERE / "build.stderr").read_text() == ""
    assert control["xcnf_sha256"] == sha(HERE / "control.xcnf")
    assert public["xcnf_sha256"] == sha(HERE / "public.xcnf")
    assert public["public_point"] == target["public_point"]
    assert public["transformed_target"] == target["transformed_target"]
    assert public["raw_preimages"] == target["raw_preimages"]
    profiles = {}
    start = time.monotonic_ns()
    for label, zlist in (("control", [fixture["raw_target_reciprocal"]]),
                         ("public", target["raw_preimage_reciprocals"])):
        formula, wires, metadata = circuit.build(zlist)
        receipt = control if label == "control" else public
        assert formula.next_var-1 == receipt["variables"]
        assert formula.and_count == receipt["and_gates"]
        assert len(formula.clauses) == receipt["cnf_clauses"]
        assert len(formula.xors) == receipt["native_xor_rows"]
        assert metadata == receipt["metadata"]
        if label == "control":
            assert circuit.check_assignment(formula, wires, fixture) == receipt["assignment_check"]
        else:
            assert wires["target_flags"] == public["target_flags"]
            assert wires["masks"] == public["mask_wires"]
            assert wires["pair_outputs"] == public["pair_output_wires"]
            assert wires["middle"] == public["middle_wires"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / f"{label}.xcnf"
            formula.write(path)
            assert path.read_bytes() == (HERE / f"{label}.xcnf").read_bytes()
        profiles[label] = {"variables": receipt["variables"],
                           "clauses": receipt["cnf_clauses"],
                           "xor_rows": receipt["native_xor_rows"],
                           "bytes": receipt["xcnf_bytes"],
                           "sha256": receipt["xcnf_sha256"]}
    ended = time.monotonic_ns()
    result = {"status": "PASS_N131_FIVEPAIR_TERMINAL_EVIDENCE_AUDIT",
              "public_process_status": query["status"],
              "mathematical_outcome": "BOUNDED_UNKNOWN",
              "profiles": profiles, "solver_restart_rows": query["solver_restart_rows"],
              "phase_ns": {"build_parent": query["build"]["wall_ns"],
                           "solver_parent": query["solver"]["wall_ns"],
                           "bookkeeping": bookkeeping,
                           "total": query["target_dependent_attempt_ns"]},
              "audit_wall_ns": ended-start,
              "peak_combined_rss_bytes_sampled": query["peak_combined_rss_bytes_sampled"],
              "protocol_sha256": sha(HERE / "audit_protocol.json")}
    with (HERE / "audit_result.json").open("x") as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write("\n")
    print(result["status"], result["mathematical_outcome"], flush=True)


if __name__ == "__main__":
    main()
