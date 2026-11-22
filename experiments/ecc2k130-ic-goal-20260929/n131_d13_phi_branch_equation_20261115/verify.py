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
    valid_p = read("valid_codes_protocol.json")
    valid = read("valid_codes_result.json")
    sage_p2 = read("audit_sage_protocol_v2.json")
    sage2 = read("audit_sage_v2_status.json")
    sage_p3 = read("audit_sage_protocol_v3.json")
    sage3 = read("audit_sage_v3_result.json")
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
    assert valid_p["status"] == "FROZEN_BEFORE_ENUMERATION"
    assert valid_p["source_sha256"] == sha(HERE / "enumerate_valid.py")
    for name, digest in valid_p["input_sha256"].items():
        assert sha(valid_p["inputs"][name]) == digest
    assert valid["status"] == "PASS_EXACT_ENUMERATION"
    assert valid["protocol_sha256"] == sha(HERE / "valid_codes_protocol.json")
    assert valid["count"] == len(read("valid_codes.json")) == 4134
    assert valid["codes_sha256"] == sha(HERE / "valid_codes.json")
    assert valid["source_phi_digest"] == result["source_phi_digest"]
    assert not (HERE / "valid_codes.stderr").read_text()
    assert sage_p2["status"] == "FROZEN_VALID_CODES_REPLAY"
    assert sage_p2["amends_protocol_sha256"] == sha(HERE / "audit_sage_protocol.json")
    assert sage_p2["capped_attempt_status_sha256"] == sha(HERE / "audit_sage_status.json")
    assert sage_p2["source_sha256"] == sha(HERE / "audit_sage_v2.py")
    for name, digest in sage_p2["input_sha256"].items():
        assert sha(sage_p2["inputs"][name]) == digest
    assert sage2["status"] == "CAPPED_180_SECONDS"
    assert sage2["protocol_sha256"] == sha(HERE / "audit_sage_protocol_v2.json")
    assert sage2["source_sha256"] == sha(HERE / "audit_sage_v2.py")
    assert sage2["stderr_sha256"] == sha(HERE / "audit_sage_v2.stderr")
    assert not (HERE / "audit_sage_v2_result.json").read_text()
    assert "AssertionError" in (HERE / "audit_sage_v2.stderr").read_text()
    assert sage_p3["status"] == "FROZEN_FIELD_CHART_REPLAY"
    assert sage_p3["amends_protocol_sha256"] == sha(HERE / "audit_sage_protocol_v2.json")
    assert sage_p3["capped_attempt_status_sha256"] == sha(HERE / "audit_sage_v2_status.json")
    assert sage_p3["source_sha256"] == sha(HERE / "audit_sage_v3.py")
    for name, digest in sage_p3["input_sha256"].items():
        assert sha(sage_p3["inputs"][name]) == digest
    assert sage3["status"] == "PASS_ALL_VALID_SELECTORS"
    assert sage3["protocol_sha256"] == sha(HERE / "audit_sage_protocol_v3.json")
    assert sage3["valid_selectors"] == 4134
    assert sage3["source_phi_digest"] == result["source_phi_digest"]
    assert sage3["image_phi_digest"] == result["image_phi_digest"]
    assert not (HERE / "audit_sage_v3.stderr").read_text()
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
                      "chart_specific_sage_replay": sage3["status"],
                      "capped_sage_attempts": 2}, sort_keys=True))


if __name__ == "__main__":
    main()
