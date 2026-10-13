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
    source_protocol = read("source_protocol.json")
    source_files = {
        "builder": HERE / "source_compare.py",
        "circuit": HERE / "circuit_compare.py",
        "parent": GOAL / "n131_w18_allseed_fourpair_20261012/fourpair_v2.py",
        "source": GOAL / "n41_w7_entropy_cubic_20261011/w8/geometry.json",
        "public": GOAL / "n41_common_frob_factor_20261012/audit_result.json",
    }
    assert source_protocol["sha256"] == {key: sha(path) for key, path in source_files.items()}
    source_build = read("source_build_result.json")
    assert source_build["protocol_sha256"] == sha(HERE / "source_protocol.json")
    assert source_build["public_point"] == source_protocol["public_point"]
    for row in source_build["rows"]:
        assert row["formula_sha256"] == sha(HERE / f"public_{row['variant']}.xcnf")
        assert row["source_counts"]["and_gates"] == 2397
    source_run_protocol = read("source_run_protocol.json")
    source_run_files = {
        "runner": HERE / "source_run.py",
        "source_protocol": HERE / "source_protocol.json",
        "build_result": HERE / "source_build_result.json",
        "solver": Path(source_run_protocol["solver_path"]),
        "two_s3_links": HERE / "public_two_s3_links.xcnf",
        "direct_s4": HERE / "public_direct_s4.xcnf",
    }
    assert source_run_protocol["sha256"] == {
        key: sha(path) for key, path in source_run_files.items()}
    source_run = read("source_run_result.json")
    assert source_run["protocol_sha256"] == sha(HERE / "source_run_protocol.json")
    for row in source_run["rows"]:
        assert row["status"] == "BOUNDED_UNKNOWN" and row["stop_reason"] == "WALL_CAP"
        assert row["solver_terminal_lines"] == []
        variant = row["variant"]
        assert row["stdout_sha256"] == sha(HERE / f"public_{variant}.solver.stdout")
        assert row["stderr_sha256"] == sha(HERE / f"public_{variant}.solver.stderr")
    control_protocol = read("source_control_protocol.json")
    control_files = {
        "script": HERE / "control_middle_sage.py",
        "runtime": HERE / "source_sage_runtime_info.json",
        "prior": GOAL / "n41_common_frob_factor_20261012/audit_result.json",
        "s4_audit": HERE / "audit_result.json",
    }
    assert control_protocol["sha256"] == {key: sha(path) for key, path in control_files.items()}
    control = read("source_control.json")
    assert control["status"] == "PASS_THREE_PAIR_GROUP_CONTROL"
    assert control["protocol_sha256"] == sha(HERE / "source_control_protocol.json")
    assert control["target_reciprocal"] == audit["n41"]["target_reciprocal"]
    control_build_protocol = read("source_control_build_protocol.json")
    control_build_files = {
        "builder": HERE / "source_control_build.py",
        "source_builder": HERE / "source_compare.py",
        "control": HERE / "source_control.json",
        "public_build": HERE / "source_build_result.json",
    }
    assert control_build_protocol["sha256"] == {
        key: sha(path) for key, path in control_build_files.items()}
    assert control_build_protocol["parent_protocol_sha256"] == sha(
        HERE / "source_control_build_protocol_v1.json")
    control_failure = read("source_control_build_failure_v1.json")
    assert control_failure["status"] == "ASSERTION_FAILURE_AFTER_BOTH_FORMULAS_WRITTEN"
    assert control_failure["protocol_sha256"] == sha(HERE / "source_control_build_protocol_v1.json")
    assert control_failure["formula_sha256"] == {
        variant: sha(HERE / f"control_{variant}.xcnf")
        for variant in ("two_s3_links", "direct_s4")}
    control_build = read("source_control_build_result.json")
    assert control_build["protocol_sha256"] == sha(HERE / "source_control_build_protocol.json")
    for row in control_build["rows"]:
        assert row["formula_sha256"] == sha(HERE / f"control_{row['variant']}.xcnf")
    control_run_protocol = read("control_run_protocol.json")
    control_run_files = {
        "runner": HERE / "control_run.py",
        "build": HERE / "source_control_build_result.json",
        "solver": Path(control_run_protocol["solver_path"]),
        "two_s3_links": HERE / "control_two_s3_links.xcnf",
        "direct_s4": HERE / "control_direct_s4.xcnf",
    }
    assert control_run_protocol["sha256"] == {
        key: sha(path) for key, path in control_run_files.items()}
    control_run = read("control_run_result.json")
    assert control_run["protocol_sha256"] == sha(HERE / "control_run_protocol.json")
    assert all(row["status"] == "SAT_PENDING_MODEL_CHECK" for row in control_run["rows"])
    model_protocol = read("control_model_protocol.json")
    model_files = {
        "checker": HERE / "check_control_models.py",
        "control": HERE / "source_control.json",
        "run": HERE / "control_run_result.json",
        "two_s3_formula": HERE / "control_two_s3_links.xcnf",
        "s4_formula": HERE / "control_direct_s4.xcnf",
        "two_s3_stdout": HERE / "control_two_s3_links.solver.stdout",
        "s4_stdout": HERE / "control_direct_s4.solver.stdout",
    }
    assert model_protocol["sha256"] == {key: sha(path) for key, path in model_files.items()}
    model = read("control_model_result.json")
    assert model["status"] == "PASS_BOTH_COMPLETE_MODELS_AND_GROUP_CONTROL"
    assert model["protocol_sha256"] == sha(HERE / "control_model_protocol.json")
    from check_control_models import check
    assert model["rows"] == [check(variant) for variant in ("two_s3_links", "direct_s4")]
    print(json.dumps({"status": "PASS_TERMINAL_BINDINGS", "fields": ["n41", "n131"],
                      "symbolic_terms": 24, "symmetric_terms": 6,
                      "circuit_rows": len(counts["rows"]),
                      "public_query_statuses": [row["status"] for row in source_run["rows"]],
                      "control_models": len(model["rows"])}, sort_keys=True))


if __name__ == "__main__":
    main()
