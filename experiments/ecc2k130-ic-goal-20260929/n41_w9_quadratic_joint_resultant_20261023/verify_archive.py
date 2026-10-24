"""Verify frozen N41 direct-resultant sources and measured receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def check_sources(name):
    cfg = json.loads((HERE / name).read_text())
    for key, value in cfg["sources"].items():
        if isinstance(value, dict):
            assert sha(value["path"]) == value["sha256"], (name, key)
        else:
            assert sha(key) == value, (name, key)
    return cfg


pre_cfg = check_sources("protocol.json")
build_cfg = check_sources("build_protocol.json")
run_cfg = check_sources("build_run_protocol.json")
probe_cfg = check_sources("probe_protocol.json")
reduce_cfg = check_sources("reduction_protocol.json")
assert all(cfg["candidate_id"] is None for cfg in
           (pre_cfg, build_cfg, run_cfg, probe_cfg, reduce_cfg))

pre = json.loads((HERE / "preflight_result.json").read_text())
assert pre["status"] == "PASS_N41_QUADRATIC_RESULTANT_PREFLIGHT"
assert pre["protocol_sha256"] == sha(HERE / "protocol.json")
assert len(pre["rows"]) == 33
assert pre["resultant_zero_count"] == pre["target_link_zero_count"] == 1
assert pre["first_lead_zero_count"] == pre["second_lead_zero_count"] == 0

build = json.loads((HERE / "build_result.json").read_text())
assert build["status"] == "PASS_N41_QUADRATIC_JOINT_RESULTANT_CIRCUIT"
assert build["protocol_sha256"] == sha(HERE / "build_protocol.json")
assert build["and_gates"] == 116305 and build["variables"] == 133375
assert build["clauses"] == 350856 and build["native_xor_rows"] == 16866
assert build["formula_sha256"] == sha(HERE / "resultant_formula.xcnf")
assert build["formula_bytes"] == (HERE / "resultant_formula.xcnf").stat().st_size
assert build["input_wires_sha256"] == sha(HERE / "resultant_input_wires.json")
assert len(build["controls_checked"]) == 33
assert sum(row["resultant_zero"] for row in build["controls_checked"]) == 1
supervisor = json.loads((HERE / "build_supervisor.json").read_text())
assert supervisor["status"] == build["status"]
assert supervisor["exit_code"] == 0
assert supervisor["result_sha256"] == sha(HERE / "build_result.json")

probe = json.loads((HERE / "probe_result.json").read_text())
assert probe["status"] == "COMPLETED_FROZEN_ABBA_PROBE"
assert probe["protocol_sha256"] == sha(HERE / "probe_protocol.json")
assert [row["arm"] for row in probe["arm_results"]] == [
    "explicit_y", "resultant", "resultant", "explicit_y"]
assert [row["reported_decisions"] for row in probe["arm_results"]] == [
    35089, 45271, 45271, 35089]
assert all(row["status"] == "INDETERMINATE_CONFLICT_CAP" and
           row["reported_conflicts"] == 20002 for row in probe["arm_results"])
for i, row in enumerate(probe["arm_results"]):
    stem = HERE / f"probe_{i}_{row['arm']}"
    assert sha(str(stem) + ".stdout") == row["solver_stdout_sha256"]
    assert sha(str(stem) + ".stderr") == row["solver_stderr_sha256"]

reduction = json.loads((HERE / "reduction_result.json").read_text())
assert reduction["status"] == "PASS_N41_SOURCE_QUADRATIC_REDUCTION"
assert reduction["protocol_sha256"] == sha(HERE / "reduction_protocol.json")
assert reduction["original_terms"] == 23 and reduction["reduced_terms"] == 54
assert len(reduction["rows"]) == 33
assert all(row["original"] == row["reduced"] for row in reduction["rows"])
print("PASS_N41_QUADRATIC_JOINT_RESULTANT_ARCHIVE")
