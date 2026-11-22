"""Verify the frozen quotient-cubic record and its independent Sage replay."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


first = read("protocol.json")
second = read("protocol_v2.json")
attempt = read("attempt1_result.json")
failure = read("attempt1_failure.json")
result = read("result.json")
audit = read("audit_result.json")
for name, protocol in (("first", first), ("second", second)):
    for source_name, source in protocol["sources"].items():
        assert sha(source["path"]) == source["sha256"], (name, source_name)
assert first["status"] == "FROZEN_BEFORE_N41_QUOTIENT_CUBIC"
assert second["status"] == "FROZEN_BEFORE_N41_QUOTIENT_CUBIC_V2"
assert first["panel_indices"] == second["panel_indices"]
assert first["witness_index"] == second["witness_index"] == 966
assert failure["status"] == "AUDIT_FAILED_CHART_MISMATCH"
assert attempt["status"] == "PASS_N41_ROOT_FREE_QUOTIENT_CUBIC"
assert result["status"] == "PASS_N41_ROOT_FREE_QUOTIENT_CUBIC_V2"
assert audit["status"] == "PASS_INDEPENDENT_SAGE_QUOTIENT_CUBIC_AUDIT"
assert all(record["candidate_id"] is None for record in (first, second, attempt, result, audit))
assert result["protocol_sha256"] == audit["protocol_sha256"] == sha(HERE / "protocol_v2.json")
assert audit["result_sha256"] == sha(HERE / "result.json")
assert result["feature_width"] == 10661
assert result["families"] == audit["families_checked"] == 8
assert audit["roots_checked"] == 64
assert audit["target_decisions_checked"] == 520
assert [row["index"] for row in result["rows"]] == second["panel_indices"]
for row in result["rows"]:
    zero = int(row["zero_mask_hex"], 16)
    one = int(row["one_mask_hex"], 16)
    assert zero & one == 0
    assert zero | one < 1 << 10661
    assert (zero | one).bit_count() == row["constant_bits"]
    assert len(row["h"]) == 9 and row["h"][-1] == 1
    assert 0 <= len(row["rejected_target_indices"]) <= 65
    assert row["rejected_target_indices"] == sorted(set(row["rejected_target_indices"]))
witness = next(row for row in result["rows"] if row["index"] == 966)
assert witness["codes"] == [24, 37]
assert 0 not in witness["rejected_target_indices"]
assert len(witness["rejected_target_indices"]) == 64
assert all(len(row["rejected_target_indices"]) == 65
           for row in result["rows"] if row["index"] != 966)
lean_log = (HERE / "lean_check.log").read_text()
assert "does not depend on any axioms" in lean_log
assert "QuotientCubic.constant_remainder_sound" in lean_log
assert "QuotientCubic.reject_mismatch" in lean_log
print("PASS_N41_QUOTIENT_CUBIC_RECORD")
