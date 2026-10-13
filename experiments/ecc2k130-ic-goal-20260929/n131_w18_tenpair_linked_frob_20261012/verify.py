"""Read-only final verifier for the linked N131 control and terminal receipt."""

import hashlib
import json
from pathlib import Path

import archive

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    protocol = read("protocol.json")
    control = read("control_result.json")
    fixture_audit_protocol = read("fixture_audit_protocol.json")
    sage = read("sage_fixture_result.json")
    query = read("query_result.json")
    audit_protocol = read("audit_protocol.json")
    audit = read("audit_result.json")
    packed = read("archive_receipt.json")
    assert protocol["status"] == "FROZEN_N131_LINKED_TENPAIR_BEFORE_CONTROL_AND_QUERY"
    assert protocol["linked_slots"] == [0, 1]
    assert protocol["distinct_folded_columns_required"] == 18
    assert control["status"] == "PASS_FULL_N131_LINKED_TENPAIR_CONSTRUCTED_WITNESS"
    assert sage["status"] == "PASS_INDEPENDENT_SAGE_N131_LINKED_CONSTRUCTED_GROUP_REPLAY"
    assert sage["distinct_folded_columns"] == 18
    assert fixture_audit_protocol["sha256"]["audit_source"] == sha(HERE / "audit_fixture_sage.py")
    assert fixture_audit_protocol["sha256"]["fixture"] == sha(HERE / "control_fixture.json")
    assert fixture_audit_protocol["sha256"]["sage_runtime"] == sha(HERE / "sage_runtime_info.json")
    assert query["status"] == "BOUNDED_UNKNOWN"
    assert query["stop_reason"] == "TOTAL_QUERY_TIMEOUT"
    assert query["solver_exit_code"] == -9
    assert query["target_dependent_attempt_ns"] == sum(query["phase_ns"].values())
    assert query["worker_count"] == protocol["worker_count"] == 1
    assert query["public_target"] == protocol["public_target"]
    assert query["peak_combined_rss_bytes_sampled"] < protocol["combined_rss_cap_bytes"]
    for name, filename in (("audit_source", "audit.py"),
                           ("protocol", "protocol.json"),
                           ("control", "control_result.json"),
                           ("sage_control", "sage_fixture_result.json"),
                           ("query", "query_result.json"),
                           ("stdout", "solver.stdout.txt"),
                           ("stderr", "solver.stderr.txt")):
        assert audit_protocol["sha256"][name] == sha(HERE / filename)
    assert audit["status"] == "PASS_N131_LINKED_TENPAIR_BINARY_FROBENIUS_RECEIPT_AUDIT"
    assert audit["sha256"]["auditor"] == sha(HERE / "audit.py")
    assert audit["ordinary_xcnf_rebuilt_byte_for_byte"]
    for name in ("control", "ordinary"):
        row = packed["formulas"][name]
        digest, size = archive.uncompressed_digest(HERE / f"{name}.xcnf.gz")
        assert digest == row["raw_sha256"]
        assert size == row["raw_bytes"]
        assert sha(HERE / f"{name}.xcnf.gz") == row["gzip_sha256"]
    assert packed["formulas"]["ordinary"]["raw_sha256"] == audit_protocol["sha256"]["ordinary_formula"]
    print("PASS_N131_LINKED_FINAL_ARCHIVE_AND_RECEIPT_AUDIT")


if __name__ == "__main__":
    main()
