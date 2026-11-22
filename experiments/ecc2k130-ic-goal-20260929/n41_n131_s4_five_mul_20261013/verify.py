"""Read-only terminal audit of the shared-product S4 experiment."""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PRIOR = GOAL / "n41_n131_s4_target_gate_20261013"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    protocol = read("protocol.json")
    core_files = {"source": HERE / "optimized.py",
                  "prior_circuit": PRIOR / "circuit_compare.py",
                  "prior_audit": PRIOR / "audit_result.json"}
    assert protocol["status"] == "FROZEN"
    assert protocol["sha256"] == {key: sha(path) for key, path in core_files.items()}
    core = read("core_result.json")
    assert core["protocol_sha256"] == sha(HERE / "protocol.json")
    counts = {(row["field"], row["variant"]): row for row in core["rows"]}
    assert counts[("n41", "prior_s4")]["and_gates"] == 5652
    assert counts[("n41", "five_mul_s4")]["and_gates"] == 4710
    assert counts[("n131", "prior_s4")]["and_gates"] == 34902
    assert counts[("n131", "five_mul_s4")]["and_gates"] == 29085
    lean = (HERE / "lean_check.log").read_text()
    assert "FiveMulIdentity.optimized_eq_symmetric" in lean
    assert "FiveMulIdentity.resultant_eq_symmetric" in lean
    assert lean.count("[propext]") == 2 and "error:" not in lean
    source = (HERE / "FiveMulIdentity.lean").read_text()
    assert "#print axioms" in source and "sorry" not in source and "admit" not in source
    assert (HERE / "lean-toolchain").read_text().strip() == "leanprover/lean4:v4.34.1"

    formula_protocol = read("formula_protocol.json")
    formula_files = {"builder": HERE / "build.py", "optimized": HERE / "optimized.py",
                     "source_builder": PRIOR / "source_compare.py",
                     "control_builder": PRIOR / "source_control_build.py",
                     "source_protocol": PRIOR / "source_protocol.json",
                     "public_build": PRIOR / "source_build_result.json",
                     "control": PRIOR / "source_control.json",
                     "public": GOAL / "n41_common_frob_factor_20261012/audit_result.json"}
    assert formula_protocol["status"] == "FROZEN"
    assert formula_protocol["sha256"] == {key: sha(path) for key, path in formula_files.items()}
    formula = read("formula_result.json")
    assert formula["protocol_sha256"] == sha(HERE / "formula_protocol.json")
    assert formula["public"]["formula_sha256"] == sha(HERE / "public_direct_s4.xcnf")
    assert formula["control"]["formula_sha256"] == sha(HERE / "control_direct_s4.xcnf")
    assert formula["public"]["source_counts"]["and_gates"] == 2397
    assert formula["public"]["total_counts"]["and_gates"] == 7107
    prior_build = json.loads((PRIOR / "source_build_result.json").read_text())
    prior_s4 = next(row for row in prior_build["rows"] if row["variant"] == "direct_s4")
    assert formula["prior_public_formula_sha256"] == prior_s4["formula_sha256"]
    assert prior_s4["total_counts"]["and_gates"] == 8049

    run_protocol = read("run_protocol.json")
    run_files = {"runner": HERE / "run.py", "formula_result": HERE / "formula_result.json",
                 "public_formula": HERE / "public_direct_s4.xcnf",
                 "control_formula": HERE / "control_direct_s4.xcnf",
                 "source_runner": PRIOR / "source_run.py",
                 "control_runner": PRIOR / "control_run.py",
                 "model_checker": PRIOR / "check_control_models.py",
                 "solver": Path(run_protocol["solver_path"])}
    assert run_protocol["status"] == "FROZEN"
    assert run_protocol["sha256"] == {key: sha(path) for key, path in run_files.items()}
    run = read("run_result.json")
    assert run["protocol_sha256"] == sha(HERE / "run_protocol.json")
    assert run["control"]["status"] == "SAT_PENDING_MODEL_CHECK"
    assert run["public"]["status"] == "BOUNDED_UNKNOWN"
    assert run["public"]["stop_reason"] == "WALL_CAP"
    assert run["public"]["solver_terminal_lines"] == []
    for kind in ("control", "public"):
        row = run[kind]
        assert row["stdout_sha256"] == sha(HERE / f"{kind}_direct_s4.solver.stdout")
        assert row["stderr_sha256"] == sha(HERE / f"{kind}_direct_s4.solver.stderr")
    sys.path.insert(0, str(PRIOR))
    import check_control_models
    check_control_models.HERE = HERE
    assert run["control_model"] == check_control_models.check("direct_s4")

    sage_protocol = read("sage_protocol.json")
    sage_files = {"script": HERE / "symbolic_sage.py",
                  "runtime": HERE / "sage_runtime_info.json",
                  "prior_audit": PRIOR / "audit_result.json",
                  "prior_resultant": PRIOR / "resultant.json"}
    assert sage_protocol["status"] == "FROZEN"
    assert sage_protocol["sha256"] == {key: sha(path) for key, path in sage_files.items()}
    sage_result, sage_run = read("sage_result.json"), read("sage_run.json")
    assert sage_result["status"] == "PASS_SYMBOLIC_AND_FIELD_S4_REFACTOR"
    assert sage_result["protocol_sha256"] == sage_run["protocol_sha256"] == sha(HERE / "sage_protocol.json")
    assert sage_result["cases"]["n41"]["checked_signed_roots"] == 4
    assert sage_result["cases"]["n131"]["checked_signed_roots"] == 4
    assert sage_run["status"] == "EXIT_0" and sage_run["returncode"] == 0
    assert sage_run["driver_sha256"] == sha(HERE / "run_sage.py")
    assert sage_run["elapsed_seconds"] < sage_protocol["wall_cap_seconds"]
    assert sage_run["peak_sampled_direct_pid_rss_bytes"] < sage_protocol["rss_cap_bytes"]
    assert sage_run["stdout_sha256"] == sha(HERE / "sage_stdout.log")
    assert sage_run["stderr_sha256"] == sha(HERE / "sage_stderr.log")
    print(json.dumps({"status": "PASS_TERMINAL_BINDINGS",
                      "and_gates_saved_n41": 8049-7107,
                      "and_gates_saved_n131_core": 34902-29085,
                      "public_status": run["public"]["status"],
                      "control_model": run["control_model"]["status"]}, sort_keys=True))


if __name__ == "__main__":
    main()
