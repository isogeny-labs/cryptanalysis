"""Check the pinned S4 control, then query the unchanged N41 public point."""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "n41_n131_s4_target_gate_20261013"
sys.path.insert(0, str(PRIOR))
import control_run
import source_run
import check_control_models


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "run_protocol.json").read_text())
    files = {"runner": HERE / "run.py",
             "formula_result": HERE / "formula_result.json",
             "public_formula": HERE / "public_direct_s4.xcnf",
             "control_formula": HERE / "control_direct_s4.xcnf",
             "source_runner": PRIOR / "source_run.py",
             "control_runner": PRIOR / "control_run.py",
             "model_checker": PRIOR / "check_control_models.py",
             "solver": Path(protocol["solver_path"])}
    assert protocol["status"] == "FROZEN"
    assert protocol["sha256"] == {key: sha(path) for key, path in files.items()}
    control_run.HERE = HERE
    source_run.HERE = HERE
    check_control_models.HERE = HERE
    control = control_run.solve("direct_s4", {
        "solver_path": protocol["solver_path"],
        "solver_flags": protocol["control_solver_flags"],
        "rss_cap_bytes": protocol["rss_cap_bytes"],
        "wall_cap_seconds": protocol["control_wall_cap_seconds"]})
    if control["status"] == "SAT_PENDING_MODEL_CHECK":
        model = check_control_models.check("direct_s4")
    else:
        model = None
    assert model is not None and model["status"] == "PASS_COMPLETE_XCNF_MODEL"
    public = source_run.solve("direct_s4", Path(protocol["solver_path"]),
                              protocol["public_solver_flags"],
                              protocol["public_wall_cap_seconds"],
                              protocol["rss_cap_bytes"])
    result = {"status": "PAIRED_CONTROL_AND_PUBLIC_QUERY_COMPLETE",
              "candidate_id": None,
              "protocol_sha256": sha(HERE / "run_protocol.json"),
              "control": control, "control_model": model, "public": public}
    (HERE / "run_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"control": control["status"], "public": public["status"],
                      "public_wall_seconds": public["wall_ns"]/1e9}, sort_keys=True))


if __name__ == "__main__":
    main()
