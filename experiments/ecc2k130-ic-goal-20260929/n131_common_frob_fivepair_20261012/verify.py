"""Read-only verification of the frozen N131 five-pair public attempt."""

import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
FACTOR = GOAL / "n41_common_frob_factor_20261012/n131_projection_result.json"
SUPPORT = GOAL / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
PARENT = GOAL / "n131_w18_allseed_fourpair_20261012/fourpair_v2.py"
SPARSE = GOAL / "n41_basis_aware_quartic_20261011/sparse.py"
KARATSUBA = HERE.parents[1] / "koblitz-polynomial-w-pair-20260925/karatsuba_circuit.py"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    fixture_protocol = read(HERE / "fixture_protocol.json")
    fixture = read(HERE / "fixture.json")
    assert fixture_protocol["sha256"] == {
        "source": sha(HERE / "fixture_sage.py"), "support": sha(SUPPORT),
        "factor": sha(FACTOR), "sage_runtime": sha(HERE / "sage_runtime_info.json")}
    assert fixture["protocol_sha256"] == sha(HERE / "fixture_protocol.json")
    assert fixture["status"] == "PASS_N131_FIVEPAIR_CONSTRUCTED_CHART"
    assert len(fixture["masks"]) == 5 and len(set(fixture["columns"])) == 10
    control_protocol = read(HERE / "control_protocol.json")
    control = read(HERE / "control_result.json")
    assert control_protocol["sha256"] == {
        "runner": sha(HERE / "build_control.py"), "circuit": sha(HERE / "circuit.py"),
        "parent": sha(PARENT), "sparse": sha(SPARSE),
        "karatsuba": sha(KARATSUBA), "support": sha(SUPPORT),
        "fixture": sha(HERE / "fixture.json"),
        "sage_runtime": sha(HERE / "sage_runtime_info.json")}
    assert control["protocol_sha256"] == sha(HERE / "control_protocol.json")
    assert control["status"] == "PASS_COMPLETE_N131_FIVEPAIR_ASSIGNMENT"
    assert control["assignment_check"] == {
        "status": "PASS_COMPLETE_N131_FIVEPAIR_ASSIGNMENT",
        "variables": control["variables"],
        "cnf_clauses_checked": control["cnf_clauses"],
        "native_xor_rows_checked": control["native_xor_rows"]}
    protocol = read(HERE / "query_protocol.json")
    public = read(HERE / "public_build_result.json")
    query = read(HERE / "query_result.json")
    assert protocol["sha256"] == {
        "runner": sha(HERE / "run_public.py"), "builder": sha(HERE / "build_public.py"),
        "circuit": sha(HERE / "circuit.py"), "parent": sha(PARENT),
        "sparse": sha(SPARSE), "karatsuba": sha(KARATSUBA),
        "support": sha(SUPPORT), "target": sha(FACTOR),
        "fixture": sha(HERE / "fixture.json"),
        "control": sha(HERE / "control_result.json"), "solver": sha(SOLVER)}
    assert protocol["one_worker"] is True and protocol["total_cap_seconds"] == 600
    assert protocol["combined_rss_cap_bytes"] == 4*1024**3
    assert public["protocol_sha256"] == query["protocol_sha256"] == sha(HERE / "query_protocol.json")
    assert public["status"] == "PUBLIC_FORMULA_BUILT"
    assert public["public_point"] == protocol["public_point"]
    assert public["transformed_target"] == protocol["transformed_target"]
    assert public["raw_preimage_reciprocals"] == protocol["raw_preimage_reciprocals"]
    assert public["metadata"]["pair_count"] == 5
    assert len(public["mask_wires"]) == 10 and len(public["target_flags"]) == 4
    assert query["status"] == query["solver"]["stop_reason"] == "PARENT_TIME_CAP"
    assert query["solver"]["exit_code"] == -9
    assert query["solver_terminal_lines"] == []
    assert query["peak_combined_rss_bytes_sampled"] < 4*1024**3
    assert 600*10**9 <= query["target_dependent_attempt_ns"] < 601*10**9
    assert query["solver_command"][0] == str(SOLVER)
    assert "--threads=1" in query["solver_command"]
    assert "--maxtime=480" in query["solver_command"]
    assert query["build"]["stdout_sha256"] == sha(HERE / "build.stdout")
    assert query["build"]["stderr_sha256"] == sha(HERE / "build.stderr")
    assert query["solver"]["stdout_sha256"] == sha(HERE / "solver.stdout")
    assert query["solver"]["stderr_sha256"] == sha(HERE / "solver.stderr")
    stdout = (HERE / "solver.stdout").read_text(errors="replace")
    assert [line for line in stdout.splitlines() if line.startswith("s ")] == []
    assert sum(line.startswith("c rst") for line in stdout.splitlines()) == query["solver_restart_rows"]
    audit_protocol = read(HERE / "audit_protocol.json")
    audit = read(HERE / "audit_result.json")
    assert audit_protocol["sha256"] == {
        "source": sha(HERE / "audit.py"), "circuit": sha(HERE / "circuit.py"),
        "fixture": sha(HERE / "fixture.json"), "target": sha(FACTOR),
        "control_result": sha(HERE / "control_result.json"),
        "public_build": sha(HERE / "public_build_result.json"),
        "query_result": sha(HERE / "query_result.json"),
        "control_xcnf": control["xcnf_sha256"],
        "public_xcnf": public["xcnf_sha256"],
        "solver_stdout": sha(HERE / "solver.stdout"),
        "solver_stderr": sha(HERE / "solver.stderr")}
    assert audit["status"] == "PASS_N131_FIVEPAIR_TERMINAL_EVIDENCE_AUDIT"
    assert audit["protocol_sha256"] == sha(HERE / "audit_protocol.json")
    assert audit["mathematical_outcome"] == "BOUNDED_UNKNOWN"
    phases = audit["phase_ns"]
    assert phases["build_parent"]+phases["solver_parent"]+phases["bookkeeping"] == phases["total"]
    assert phases["total"] == query["target_dependent_attempt_ns"]
    archive_protocol = read(HERE / "archive_protocol.json")
    archive = read(HERE / "archive_result.json")
    assert archive_protocol["source_sha256"] == sha(HERE / "archive.py")
    assert archive_protocol["terminal_audit_sha256"] == sha(HERE / "audit_result.json")
    assert archive["status"] == "PASS_BYTE_REPLAY_XCNF_ARCHIVE"
    assert archive["protocol_sha256"] == sha(HERE / "archive_protocol.json")
    assert archive_protocol["input_sha256"] == {
        name: row["raw_sha256"] for name, row in archive["files"].items()}
    for name, row in archive["files"].items():
        packed = (HERE / (name + ".gz")).read_bytes()
        assert digest(packed) == row["gzip_sha256"] and len(packed) == row["gzip_bytes"]
        raw = gzip.decompress(packed)
        assert digest(raw) == row["raw_sha256"] and len(raw) == row["raw_bytes"]
    assert archive["files"]["control.xcnf"]["raw_sha256"] == control["xcnf_sha256"]
    assert archive["files"]["public.xcnf"]["raw_sha256"] == public["xcnf_sha256"]
    print("PASS_N131_FIVEPAIR_FROZEN_EVIDENCE_AUDIT BOUNDED_UNKNOWN")


if __name__ == "__main__":
    main()
