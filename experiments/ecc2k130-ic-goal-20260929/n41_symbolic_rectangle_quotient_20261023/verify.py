"""Check frozen sources, all symbolic stages, Sage audits, and witness control."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol_names = ["protocol.json", "protocol_v2.json", "selection_protocol.json",
                  "adaptive_protocol.json", "hash_protocol.json"]
for name in protocol_names:
    protocol = read(name)
    assert protocol["candidate_id"] is None
    for source_name, item in protocol["sources"].items():
        assert sha(item["path"]) == item["sha256"], (name, source_name)

initial = read("result.json")
initial_audit = read("audit_result.json")
sweep = read("result_v2.json")
sweep_audit = read("audit_result_v2.json")
selection = read("selection_result.json")
adaptive = read("adaptive_result.json")
adaptive_audit = read("adaptive_audit_result.json")
fingerprint = read("hash_result.json")
fingerprint_audit = read("hash_audit_result.json")
failure = read("freeze_v2_attempt1_failure.json")

assert failure["status"] == "FREEZE_ASSERTION_FAILED_BEFORE_PROTOCOL_WRITE"
assert initial["status"] == "PASS_N41_SYMBOLIC_TWO_CODE_RECTANGLES"
assert initial_audit["status"] == "PASS_INDEPENDENT_SAGE_SYMBOLIC_RECTANGLE_AUDIT"
assert initial["rectangles"] == 2 and initial_audit["roots_checked"] == 64
assert initial["rows"][0]["cubic_constant"] == 0
assert initial["rows"][0]["target_rejected"] is True
assert initial["rows"][1]["cubic_constant"] is None
assert initial["rows"][1]["target_rejected"] is False

assert sweep["status"] == "PASS_N41_SYMBOLIC_COMPLETE_2X2_SWEEP"
assert sweep_audit["status"] == "PASS_INDEPENDENT_SAGE_COMPLETE_2X2_AUDIT"
assert sweep["rectangles"] == 132 and sweep["families_covered"] == 528
assert len(sweep["rows"]) == 132
assert sum(row["target_rejected"] for row in sweep["rows"]) == 5
assert sweep_audit["roots_checked"] == 4224
assert sweep_audit["coefficients_checked"] == 4752

assert selection["status"] == "PASS_N41_DISJOINT_CUBIC_BIT_SELECTION"
assert selection["training_rectangles"] == 32
assert selection["holdout_rectangles"] == 100
assert len(selection["bit_order"]) == 15
assert selection["training_full_feature_rejected"] == 32
assert selection["training_selected_rejected"] == 32
assert selection["holdout_full_feature_rejected"] == 98
assert selection["holdout_selected_rejected"] == 21
assert selection["holdout_witness_selected_rejected"] is False

assert adaptive["status"] == "PASS_N41_ADAPTIVE_SYMBOLIC_HOLDOUT"
assert adaptive_audit["status"] == "PASS_INDEPENDENT_SAGE_ADAPTIVE_HOLDOUT_AUDIT"
assert adaptive["rectangles"] == 100 and adaptive["families_covered"] == 400
assert adaptive["bit_order"] == selection["bit_order"]
assert adaptive["rejected_rectangles"] == 21
assert adaptive_audit["roots_checked"] == 3200
assert adaptive_audit["residue_root_checks"] == 41664

assert fingerprint["status"] == "PASS_N41_QUOTIENT_FINGERPRINT"
assert fingerprint_audit["status"] == "PASS_INDEPENDENT_SAGE_QUOTIENT_FINGERPRINT_AUDIT"
assert fingerprint["rectangles"] == 132 and fingerprint["families_covered"] == 528
assert fingerprint["rejected_rectangles"] == 131
assert fingerprint["rejected_by_checkpoint"] == {
    "8": 108, "12": 130, "16": 131, "24": 131}
assert fingerprint_audit["roots_checked"] == 4224
assert fingerprint_audit["coefficients_checked"] == 4752
assert fingerprint_audit["indicator_root_checks"] == 16896
assert fingerprint_audit["exact_coordinate_families"] == 1
survivors = [row for row in fingerprint["rows"] if not row["target_rejected"]]
assert len(survivors) == 1
assert survivors[0]["prefix"] == [38, 53]
assert 966 in survivors[0]["case_indices"]
assert survivors[0]["bits_evaluated"] == 24
assert all(row["bits_evaluated"] <= 24 for row in fingerprint["rows"])

for result, audit, protocol_name, result_name in [
    (initial, initial_audit, "protocol.json", "result.json"),
    (sweep, sweep_audit, "protocol_v2.json", "result_v2.json"),
    (adaptive, adaptive_audit, "adaptive_protocol.json", "adaptive_result.json"),
    (fingerprint, fingerprint_audit, "hash_protocol.json", "hash_result.json"),
]:
    assert result["candidate_id"] is audit["candidate_id"] is None
    assert result["protocol_sha256"] == audit["protocol_sha256"] == sha(HERE / protocol_name)
    assert audit["result_sha256"] == sha(HERE / result_name)
    assert result["self_maxrss_raw"] < 4 * 1024**3
    assert result["wall_seconds"] < 300

lean = (HERE / "lean_check.log").read_text()
for theorem in ("indicator_true_iff_all_equal", "indicator_zero_excludes_exact",
                "zero_persists"):
    assert f"QuotientFingerprint.{theorem}" in lean
assert "sorryAx" not in lean
print("PASS_N41_SYMBOLIC_RECTANGLE_FINGERPRINT_RECORD")
