"""Build optimized S4 public and planted N41 formulas from frozen source code."""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PRIOR = GOAL / "n41_n131_s4_target_gate_20261013"
sys.path.insert(0, str(PRIOR))
import source_compare as source
import source_control_build as control_builder
import optimized


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "formula_protocol.json").read_text())
    files = {"builder": HERE / "build.py",
             "optimized": HERE / "optimized.py",
             "source_builder": PRIOR / "source_compare.py",
             "control_builder": PRIOR / "source_control_build.py",
             "source_protocol": PRIOR / "source_protocol.json",
             "public_build": PRIOR / "source_build_result.json",
             "control": PRIOR / "source_control.json",
             "public": GOAL / "n41_common_frob_factor_20261012/audit_result.json"}
    assert protocol["status"] == "FROZEN"
    assert protocol["sha256"] == {key: sha(path) for key, path in files.items()}
    public = json.loads(files["public_build"].read_text())
    control = json.loads(files["control"].read_text())
    assert public["public_point"] == protocol["public_point"]
    assert public["public_target_reciprocal"] == protocol["public_target_reciprocal"]
    assert control["target_reciprocal"] == protocol["constructed_target_reciprocal"]
    source.HERE = HERE
    source.s4 = optimized.s4
    control_builder.HERE = HERE
    control_builder.s4 = optimized.s4
    public_row = source.build(protocol["public_target_reciprocal"], "direct_s4")
    control_row = control_builder.build("direct_s4", control)
    prior_row = next(row for row in public["rows"] if row["variant"] == "direct_s4")
    assert public_row["source_counts"]["and_gates"] == prior_row["source_counts"]["and_gates"]
    assert public_row["source_counts"]["variables"] == prior_row["source_counts"]["variables"]
    assert public_row["total_counts"]["and_gates"] < prior_row["total_counts"]["and_gates"]
    assert control_row["source_counts"] == {
        key: prior_row["source_counts"][key] for key in control_row["source_counts"]}
    result = {"status": "PASS_REBUILT_SOURCE_WITH_FIVE_MUL_S4",
              "candidate_id": None, "protocol_sha256": sha(HERE / "formula_protocol.json"),
              "prior_public_formula_sha256": prior_row["formula_sha256"],
              "public": public_row, "control": control_row}
    (HERE / "formula_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"public": public_row, "control": control_row}, sort_keys=True))


if __name__ == "__main__":
    main()
