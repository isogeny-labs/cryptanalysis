"""Replay frozen source bindings and terminal evidence for the S4 gate."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    protocol = read("protocol.json")
    assert protocol["status"] == "FROZEN"
    assert protocol["source_sha256"] == sha(HERE / "derive.py")
    assert protocol["prior_n41_relation_sha256"] == sha(
        GOAL / "n41_common_frob_factor_20261012/audit_result.json")
    resultant, symmetric = read("resultant.json"), read("symmetric_result.json")
    assert resultant["term_count"] == 24 == len(resultant["terms"])
    assert symmetric["term_count"] == 6 == len(symmetric["terms"])
    audit_protocol = read("audit_protocol.json")
    audit_files = {
        "script": HERE / "audit_sage.py",
        "runtime": HERE / "sage_runtime_info.json",
        "resultant": HERE / "resultant.json",
        "symmetric": HERE / "symmetric_result.json",
        "n41_relation": GOAL / "n41_common_frob_factor_20261012/audit_result.json",
        "n131_control": GOAL / "n131_w15_onepair_fixed_sat_gate_20261010/fivepair_control_group_lift.json",
    }
    assert audit_protocol["status"] == "FROZEN"
    assert audit_protocol["sha256"] == {key: sha(path) for key, path in audit_files.items()}
    assert audit_protocol["parent_protocol_sha256"] == sha(HERE / "audit_protocol_v2.json")
    audit, run = read("audit_result.json"), read("audit_run_v3.json")
    assert audit["status"] == "PASS_SYMBOLIC_RESULTANT_AND_GROUP_CONTROLS"
    assert audit["protocol_sha256"] == run["protocol_sha256"] == sha(HERE / "audit_protocol.json")
    assert run["status"] == "EXIT_0" and run["returncode"] == 0
    assert run["driver_sha256"] == sha(HERE / "audit_driver.py")
    assert run["peak_sampled_direct_pid_rss_bytes"] < audit_protocol["rss_cap_bytes"]
    assert run["elapsed_seconds"] < audit_protocol["wall_cap_seconds"]
    assert run["stdout_sha256"] == sha(HERE / "sage_stdout_v3.log")
    assert run["stderr_sha256"] == sha(HERE / "sage_stderr_v3.log")
    for field in ("n41", "n131"):
        item = audit[field]
        assert item["univariate_degree"] == 4
        assert len(item["field_roots"]) == 4
        assert item["field_roots"] == item["signed_group_x_roots"]
        assert item["target_reciprocal"] in item["field_roots"]
    counts = read("circuit_counts.json")
    assert counts["status"] == "ARITHMETIC_CORE_COUNTS_ONLY"
    assert counts["source_sha256"] == sha(HERE / "circuit_compare.py")
    assert counts["audit_sha256"] == sha(HERE / "audit_result.json")
    assert counts["karatsuba_sha256"] == sha(
        ROOT / "experiments/koblitz-polynomial-w-pair-20260925/karatsuba_circuit.py")
    assert len(counts["rows"]) == 4
    for lean_log, theorem in (("lean_polynomial_check.log", "resultant_eq_symmetric"),
                              ("lean_bezout_check.log", "bezout_equals_resultant")):
        output = (HERE / lean_log).read_text()
        assert theorem in output and "[propext]" in output
        assert "error:" not in output and "sorryAx" not in output
    for source in ("S4Polynomial.lean", "S4Bezout.lean"):
        body = (HERE / source).read_text()
        assert "theorem " in body and "#print axioms" in body
        assert "sorry" not in body and "admit" not in body
    assert read("launch_failure_v1.json")["status"] == "LAUNCH_WRAPPER_FAILED"
    assert read("audit_run_v2.json")["status"] == "EXIT_NONZERO"
    print(json.dumps({"status": "PASS_TERMINAL_BINDINGS", "fields": ["n41", "n131"],
                      "symbolic_terms": 24, "symmetric_terms": 6,
                      "circuit_rows": len(counts["rows"])}, sort_keys=True))


if __name__ == "__main__":
    main()
