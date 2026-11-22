"""Independent low-pivot replay of the W23 quadratic-capacity evidence."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
freeze = json.loads((HERE / "verification_protocol.json").read_text())
for path, digest in freeze["sources"].items():
    assert sha(path) == digest, path
assert sha(HERE / "verify.py") == freeze["verifier_sha256"]
result = json.loads((HERE / "result.json").read_text())
coeffs = json.loads((HERE / "coefficients.json").read_text())
audit = json.loads((HERE / "audit_result.json").read_text())
conflict = json.loads((HERE / "certificate.json").read_text())
panel = json.loads((HERE / "panel.json").read_text())
assert result["field_degree"] == 131 and result["feature_count"] == 8646
assert result["frozen_code_count"] == 80 and result["processed_code_count"] == len(coeffs) == 68
selected_masks = [variant["mask"] for variant in panel["variants"]]
assert selected_masks == sorted(selected_masks) and panel["masks_scanned"] == 311
assert selected_masks[67] == 274 and selected_masks[-1] == 311
assert sum(mask < 256 for mask in selected_masks[:68]) == 64
assert all(mask >> 9 == 0 for mask in selected_masks[:68])
assert audit["status"] == "PASS_FULL_N131_W23_RR_DETERMINANT_REPLAY"
assert audit["audited_charts"] == 136 and audit["audited_determinants"] == 8704
assert audit["zero_states"] == []

def truth_direct(coefficients, sign):
    answer = 0
    for subset in range(64):
        if subset & sign == subset:
            answer ^= coefficients[subset]
    return answer

def feature_direct(value):
    active = {index for index in range(131) if (value >> index) & 1}
    vector = 0
    for index in active:
        vector ^= 1 << index
    location = 131
    for i in range(131):
        for j in range(i + 1, 131):
            if i in active and j in active:
                vector ^= 1 << location
            location += 1
    assert location == 8646
    return vector

rows = []
low_basis = {}
rank_after = []
certified_weight = int(result["certified_prefix_certificate_hex"], 16)
assert result["certified_prefix_code_count"] == 67
for ordinal, record in enumerate(coeffs):
    assert record["mask"] == panel["variants"][ordinal]["mask"]
    assert len(record["coefficients"]) == 2
    zeros = []
    for root in range(2):
        values = [truth_direct(record["coefficients"][root], sign) for sign in range(64)]
        expected_digest = hashlib.sha256(json.dumps(values).encode()).hexdigest()
        assert audit["chart_digests"][2 * ordinal + root]["truth_sha256"] == expected_digest
        for sign, value in enumerate(values):
            if value == 0:
                zeros.append([root, sign])
            row = feature_direct(value)
            index = len(rows)
            rows.append(row)
            if ordinal < 67:
                assert (row & certified_weight).bit_count() & 1, (ordinal, root, sign)
            if index <= conflict["first_failure_index"]:
                reduced = row
                while reduced:
                    pivot = (reduced & -reduced).bit_length() - 1
                    if pivot not in low_basis:
                        low_basis[pivot] = reduced
                        break
                    reduced ^= low_basis[pivot]
    assert zeros == record["zero_states"] == result["records"][ordinal]["zero_states"] == []
    rank_after.append(len(low_basis))

assert len(rows) == 8704
assert rank_after[:67] == [128 * (i + 1) for i in range(67)]
assert rank_after[67] == 8642
assert len(low_basis) == conflict["rank_before_failure"] == 8642
assert result["first_failure"] == {"mask": 274, "ordinal": 67, "root": 1,
                                    "sign": 2, "reason": "QUADRATIC_SYSTEM_INCONSISTENT"}
assert conflict["first_failure_index"] == 8642
assert conflict["first_failure_position"] == [67, 274, 1, 2]
indices = conflict["dependency_row_indices"]
assert indices == sorted(set(indices)) and len(indices) == conflict["dependency_size"] == 4373
assert indices[-1] == 8642 and len(indices) & 1
combined = 0
for index in indices:
    combined ^= rows[index]
assert combined == 0
lean = (HERE / "lean.stdout").read_text()
assert "'QuadraticConflict.no_score_for_odd_zero_dependency' depends on axioms:" in lean
assert "sorryAx" not in lean and not (HERE / "lean.stderr").read_text()

receipt = {"status": "PASS_N131_W23_QUADRATIC_CAPACITY_REPLAY",
           "result_sha256": sha(HERE / "result.json"),
           "coefficient_sha256": sha(HERE / "coefficients.json"),
           "audit_sha256": sha(HERE / "audit_result.json"),
           "certificate_sha256": sha(HERE / "certificate.json"),
           "verification_protocol_sha256": sha(HERE / "verification_protocol.json"),
           "full_sage_determinants": 8704,
           "certified_complete_code_prefix": 67,
           "first_conflict_code_ordinal": 67,
           "odd_dependency_size": len(indices)}
(HERE / "terminal.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(receipt["status"])
