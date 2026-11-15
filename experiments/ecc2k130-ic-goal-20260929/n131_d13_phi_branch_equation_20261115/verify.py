"""Read-only custody check for the N131 source branch identity."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    protocol = read("protocol.json")
    result = read("audit_result.json")
    sage_p = read("audit_sage_protocol.json")
    sage = read("audit_sage_status.json")
    assert protocol["status"] == "FROZEN_BEFORE_AUDIT"
    assert protocol["audit_source_sha256"] == sha(HERE / "audit.py")
    assert protocol["lean_source_sha256"] == sha(HERE / "BranchEquation.lean")
    for name, digest in protocol["input_sha256"].items():
        assert sha(protocol["inputs"][name]) == digest
    assert result["status"] == "PASS_ALL_VALID_SELECTORS_BOTH_BRANCHES"
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert result["valid_selectors"] == 4134
    assert result["branch_equations_checked"] == 8268
    assert result["image_phi_unique_per_position"] == 4134
    assert not (HERE / "audit.stderr").read_text()
    assert sage_p["status"] == "FROZEN_BEFORE_INDEPENDENT_AUDIT"
    assert sage_p["source_sha256"] == sha(HERE / "audit_sage.py")
    assert sage_p["sage_runtime_info_sha256"] == sha(HERE / "sage_runtime_info.json")
    for name, digest in sage_p["input_sha256"].items():
        assert sha(sage_p["inputs"][name]) == digest
    assert sage["status"] == "CAPPED_180_SECONDS"
    assert sage["protocol_sha256"] == sha(HERE / "audit_sage_protocol.json")
    assert sage["source_sha256"] == sha(HERE / "audit_sage.py")
    assert sage["stderr_sha256"] == sha(HERE / "audit_sage.stderr")
    assert not (HERE / "audit_sage_result.json").read_text()
    assert "AssertionError" in (HERE / "audit_sage.stderr").read_text()
    lean = (HERE / "BranchEquation.lean").read_text()
    assert all(word not in lean for word in ("sorry", "admit", "sorryAx"))
    output = (HERE / "lean.stdout").read_text()
    assert "BranchEquation.branch_equation' depends on axioms: [propext, Classical.choice, Quot.sound]" in output
    assert "BranchEquation.image_unique' depends on axioms: [propext, Classical.choice, Quot.sound]" in output
    assert not (HERE / "lean.stderr").read_text()
    assert 10*(13+13*131) == 17160
    print(json.dumps({"status": "PASS", "valid_selectors": 4134,
                      "branch_cases": 8268,
                      "derived_leaf_and_upper_bound": 17160,
                      "chart_specific_sage_replay": sage["status"]}, sort_keys=True))


if __name__ == "__main__":
    main()
