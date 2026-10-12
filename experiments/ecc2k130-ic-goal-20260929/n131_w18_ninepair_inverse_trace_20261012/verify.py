"""Verify frozen receipts, compressed formulas, Sage control, and Lean log."""

import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    protocol = read("protocol.json")
    control = read("control_result.json")
    query = read("query_result.json")
    audit = read("audit_result.json")
    gate = read("control_gate_sage.json")
    archive = read("archive_receipt.json")
    assert protocol["status"] == "FROZEN_N131_NINEPAIR_ORBIT_BEFORE_CONTROL_AND_QUERY"
    assert protocol["candidate_id"] is None
    assert protocol["target_choice_count"] == 524
    assert protocol["worker_count"] == 1
    assert protocol["combined_rss_cap_bytes"] == 4 * 1024**3
    assert protocol["total_target_dependent_cap_seconds"] == 600
    assert control["variant"] == "balanced_inverse_trace_source"
    assert control["assignment_check"] == {
        "clauses": control["formula"]["clauses"],
        "native_xor_rows": control["formula"]["native_xor_rows"],
    }
    assert control["protocol_sha256"] == query["protocol_sha256"] == sha(HERE / "protocol.json")
    assert gate["status"] == "PASS_SAGE_N131_NINEPAIR_INVERSE_TRACE_CONTROL"
    assert gate["inverse_witness_checks"] == gate["distinct_folded_columns"] == 18
    assert gate["source_sha256"]["protocol"] == sha(HERE / "protocol.json")
    assert gate["source_sha256"]["control"] == sha(HERE / "control_result.json")
    assert query["status"] == audit["query_status"] == "BOUNDED_UNKNOWN"
    assert query["stop_reason"] == "TOTAL_QUERY_TIMEOUT"
    assert query["target_dependent_attempt_ns"] == sum(query["phase_ns"].values())
    assert query["target_dependent_attempt_ns"] == audit["target_dependent_attempt_ns"]
    assert query["peak_combined_rss_bytes_sampled"] < protocol["combined_rss_cap_bytes"]
    assert query["status_lines"] == [] and not query["decoded_model_saved"]
    assert audit["status"] == "PASS_N131_INVERSE_TRACE_TREE_RECEIPT_AUDIT"
    assert audit["ordinary_xcnf_rebuilt_byte_for_byte"]
    assert audit["sha256"]["query"] == sha(HERE / "query_result.json")
    assert audit["sha256"]["control_gate_sage"] == sha(HERE / "control_gate_sage.json")
    assert audit["sha256"]["stdout"] == sha(HERE / "solver.stdout.txt")
    assert audit["sha256"]["stderr"] == sha(HERE / "solver.stderr.txt")
    assert archive["status"] == "PASS_FROZEN_XCNF_GZIP_BYTE_REPLAY"
    assert archive["protocol_sha256"] == sha(HERE / "protocol.json")
    for name, result in (("control", control), ("ordinary", query)):
        packed = HERE / f"{name}.xcnf.gz"
        profile = result["formula"]
        row = archive["formulas"][name]
        assert sha(packed) == row["gzip_sha256"]
        digest, count = hashlib.sha256(), 0
        with gzip.open(packed, "rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
                count += len(chunk)
        assert digest.hexdigest() == row["raw_sha256"] == profile["xcnf_sha256"]
        assert count == row["raw_bytes"] == profile["xcnf_bytes"]
    assert "does not depend on any axioms" in (HERE / "lean_check.txt").read_text()
    print("PASS_N131_INVERSE_TRACE_ARCHIVED_RECEIPTS")


if __name__ == "__main__":
    main()
