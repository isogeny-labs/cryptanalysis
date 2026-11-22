"""Verify the frozen two-code propagation census and independent receipts."""

import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
PREVIOUS = BASE.parent / "n41_sixpair_code_propagation_20261115"
SOURCE = BASE.parent / "n41_sixpair_shared_target_20261017"
CASES = BASE.parent / "n41_w8_two_code_affine_span_20261013" / "cases.jsonl"
GEOMETRY = BASE.parent / "n41_w8_fixed_sum_table_20261009" / "geometry.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((BASE / name).read_text())


def main():
    protocol = read("protocol.json")
    result = read("result.json")
    audit = read("audit_result.json")
    comparison = read("source_validity_comparison.json")
    failure = read("audit_precheck_failure.json")
    sources = {"screen": BASE / "screen.py", "propagator": PREVIOUS / "screen.py",
               "public_xcnf": SOURCE / "public.xcnf",
               "witness": SOURCE / "join_audit_result.json"}
    assert protocol["source_sha256"] == {key: sha(path) for key, path in sources.items()}
    assert result["protocol_sha256"] == sha(BASE / "protocol.json")
    assert result["public_xcnf_sha256"] == sha(sources["public_xcnf"])
    assert result["status"] == "PASS_BOUNDED_TWO_CODE_PROPAGATION_SCREEN"
    assert result["code_pair_count"] == 1600 and result["conflicts"] == 46
    assert result["open_families"] == 1554 and result["witness_codes"] == [6, 100]
    assert audit["status"] == "PASS_INDEPENDENT_FULL_SCAN_TWO_CODE_REPLAY"
    assert audit["code_pair_count"] == 1600 and audit["conflicts"] == 46
    audit_sources = {"public_xcnf": sources["public_xcnf"],
                     "protocol": BASE / "protocol.json", "result": BASE / "result.json",
                     "auditor": BASE / "audit.py", "reference_full_scan": PREVIOUS / "audit.py"}
    assert audit["input_sha256"] == {key: sha(path) for key, path in audit_sources.items()}
    producer_rows = result["rows"]
    audit_rows = audit["rows"]
    assert len(producer_rows) == len(audit_rows) == 1600
    for producer, reference in zip(producer_rows, audit_rows):
        assert (producer["first_code"], producer["second_code"], producer["status"]) == (
            reference["first_code"], reference["second_code"], reference["status"])
        if producer["status"] == "OPEN":
            assert producer["assigned_variables"] == reference["assigned_variables"]
    witness = next(row for row in producer_rows
                   if [row["first_code"], row["second_code"]] == [6, 100])
    assert witness["status"] == "OPEN"
    assert comparison["status"] == "PASS_CONFLICTS_EQUAL_SOURCE_INVALID_PAIRS"
    comparison_sources = {"result": BASE / "result.json", "cases": CASES,
                          "geometry": GEOMETRY, "script": BASE / "compare_source_validity.py"}
    assert comparison["source_sha256"] == {
        key: sha(path) for key, path in comparison_sources.items()}
    assert comparison["source_admissible_pairs"] == 1554
    assert comparison["conflicts_on_admissible_pairs"] == 0
    assert comparison["unrejected_invalid_pairs"] == 0
    assert failure["status"] == "PRECHECK_ASSERTION_FAILURE"
    assert failure["pair_codes"] == [2, 2]
    assert failure["producer_status"] == failure["full_scan_status"] == "CONFLICT"
    print("PASS_TWO_CODE_PROPAGATION_VERIFICATION", len(producer_rows), 46, 1554)


if __name__ == "__main__":
    main()
