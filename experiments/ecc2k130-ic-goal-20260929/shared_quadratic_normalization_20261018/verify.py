"""Verify frozen sources, two independent arithmetic audits, and Lean log."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
protocol = json.loads((HERE / "protocol.json").read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for relative, expected in protocol["repo_sources_sha256"].items():
    assert digest(ROOT / relative) == expected, relative
for name, expected in protocol["local_sha256"].items():
    assert digest(HERE / name) == expected, name

result = json.loads((HERE / "result.json").read_text())
audit = json.loads((HERE / "audit_result.json").read_text())
assert result["status"] == "COMPLETE_SHARED_QUADRATIC_AUDIT"
assert audit["status"] == "INDEPENDENT_SAGE_AUDIT_PASS"
assert audit["producer_sha256"] == digest(HERE / "result.json")
assert len(result["rows"]) == len(audit["rows"]) == 4
for row, independent in zip(result["rows"], audit["rows"]):
    assert row["field_degree"] == independent["field_degree"]
    assert row["target_index"] == independent["target_index"]
    assert row["p_rank"] == independent["source_span_rank"]
    assert row["other_root_in_source_span"] == independent["other_root_in_source_span"]
    assert row["exception_count"] == independent["exception_count"] == 1
    assert row["p_rank"] == row["q_rank"] == row["source_bits"]
    assert row["q_quadratic_coefficient_rank"] == (37 if row["field_degree"] == 41 else 131)
    if row["field_degree"] == 41:
        assert row["exhaustive_n41_exception_codes"] == [0]
    else:
        assert row["exhaustive_n41_exception_codes"] is None

log = (HERE / "lean_check.log").read_text()
for theorem in ("leading_expansion", "normalized_zero_iff",
                "shared_quadratic_coefficient", "exceptional_factorization",
                "branch_enumeration_length"):
    assert "'SharedQuadratic." + theorem + "' depends on axioms: " in log
assert "sorryAx" not in log and "error:" not in log
assert (HERE / "lean-toolchain").read_text().strip() == "leanprover/lean4:v4.34.1"
assert json.loads((HERE / "sage_runtime_info.json").read_text())["status"] == "verified"
print(json.dumps({"status": "VERIFIED", "rows": 4,
                  "source_and_artifact_hashes": len(protocol["repo_sources_sha256"]) +
                  len(protocol["local_sha256"])}, sort_keys=True))
