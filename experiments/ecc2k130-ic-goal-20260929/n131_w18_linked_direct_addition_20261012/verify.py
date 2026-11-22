"""Read-only verifier for the direct-addition N131 experiment bundle."""

import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "n131_w18_linked_signature_prefix_20261012"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def unpacked(path):
    digest, size = hashlib.sha256(), 0
    with gzip.open(path, "rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def main():
    candidate = read(HERE / "protocol.json")
    stage_protocol = read(HERE / "stage_protocol.json")
    stage = read(HERE / "stage_result.json")
    control_protocol = read(HERE / "control_protocol.json")
    control = read(HERE / "control_result.json")
    direct_control = read(HERE / "direct_control_result.json")
    public = read(HERE / "public_protocol.json")
    query = read(HERE / "query_result.json")
    audit_protocol = read(HERE / "query_audit_protocol.json")
    audit = read(HERE / "query_audit_result.json")
    archive_protocol = read(HERE / "archive_protocol.json")
    archive = read(HERE / "archive_result.json")
    assert candidate["status"] == "FROZEN_N131_LINKED_TENPAIR_BEFORE_CONTROL_AND_QUERY"
    assert candidate["source_sha256"]["linked_direct_addition"] == sha(HERE / "direct.py")
    assert candidate["curve_id"] == public["curve_id"] == query["curve_id"]
    assert candidate["workload_id"] == public["workload_id"] == query["workload_id"]
    for protocol, paths in (
        (stage_protocol, {"stage": HERE / "stage.py", "gate": HERE / "direct.py",
                          "fixture": HERE / "control_fixture.json",
                          "candidate_protocol": HERE / "protocol.json"}),
        (control_protocol, {"control": HERE / "control.py", "gate": HERE / "direct.py",
                            "candidate_protocol": HERE / "protocol.json",
                            "stage_result": HERE / "stage_result.json",
                            "fixture": HERE / "control_fixture.json"}),
        (public, {"runner": HERE / "public.py", "gate": HERE / "direct.py",
                  "candidate_protocol": HERE / "protocol.json",
                  "stage_result": HERE / "stage_result.json",
                  "control_protocol": HERE / "control_protocol.json",
                  "control_result": HERE / "control_result.json",
                  "direct_control_result": HERE / "direct_control_result.json",
                  "prior_all_root_audit": PREVIOUS / "fast_audit_result.json",
                  "prior_all_root_audit_protocol": PREVIOUS / "fast_audit_protocol.json",
                  "prior_root_table": PREVIOUS / "rows.tsv.gz"}),
        (audit_protocol, {"audit_source": HERE / "audit_query.py",
                          "candidate_protocol": HERE / "protocol.json",
                          "public_protocol": HERE / "public_protocol.json",
                          "direct_control": HERE / "direct_control_result.json",
                          "query": HERE / "query_result.json",
                          "stdout": HERE / "solver.stdout.txt",
                          "stderr": HERE / "solver.stderr.txt"}),
        (archive_protocol, {"source": HERE / "archive.py",
                            "control": HERE / "control_result.json",
                            "query": HERE / "query_result.json",
                            "terminal_audit": HERE / "query_audit_result.json"}),
    ):
        for key, path in paths.items():
            assert protocol["sha256"][key] == sha(path), key
    assert stage["status"] == "PASS_N131_LINKED_DIRECT_ADDITION_CONSTRUCTED_CIRCUIT_BUILD"
    assert stage["stage_protocol_sha256"] == sha(HERE / "stage_protocol.json")
    assert stage["formula_variables"] == 304057
    assert stage["formula_clauses"] == 609681
    assert control["status"] == "PASS_FULL_N131_LINKED_TENPAIR_CONSTRUCTED_WITNESS"
    assert control["protocol_sha256"] == sha(HERE / "protocol.json")
    assert direct_control["status"] == "PASS_FULL_N131_DIRECT_LINKED_ADDITION_CONSTRUCTED_ASSIGNMENT"
    assert direct_control["inherited_control_sha256"] == sha(HERE / "control_result.json")
    assert direct_control["control_protocol_sha256"] == sha(HERE / "control_protocol.json")
    assert query["protocol_sha256"] == sha(HERE / "protocol.json")
    assert query["public_target"] == candidate["public_target"]
    assert query["worker_count"] == public["worker_count"] == 1
    assert query["target_dependent_attempt_ns"] == sum(query["phase_ns"].values())
    assert query["peak_combined_rss_bytes_sampled"] <= public["combined_rss_cap_bytes"]
    assert query["stdout_sha256"] == sha(HERE / "solver.stdout.txt")
    assert query["stderr_sha256"] == sha(HERE / "solver.stderr.txt")
    assert audit["status"] == "PASS_N131_DIRECT_ADDITION_TERMINAL_RECEIPT_AUDIT"
    assert audit["query_status"] == query["status"]
    assert audit["ordinary_xcnf_rebuilt_byte_for_byte"]
    assert audit["query_audit_protocol_sha256"] == sha(HERE / "query_audit_protocol.json")
    assert audit_protocol["sha256"]["ordinary_xcnf"] == query["formula"]["xcnf_sha256"]
    assert archive["status"] == "PASS_DIRECT_ADDITION_BOTH_XCNF_ARCHIVE_REPLAY"
    assert archive["archive_protocol_sha256"] == sha(HERE / "archive_protocol.json")
    for label, filename, profile in (
        ("control", "control.xcnf.gz", control["formula"]),
        ("public", "ordinary.xcnf.gz", query["formula"]),
    ):
        packed = HERE / filename
        receipt = archive["files"][label]
        assert sha(packed) == receipt["gzip_sha256"]
        digest, size = unpacked(packed)
        assert digest == receipt["raw_sha256"] == profile["xcnf_sha256"]
        assert size == receipt["raw_bytes"] == profile["xcnf_bytes"]
    assert "does not depend on any axioms" in (HERE / "lean_check.log").read_text()
    print("PASS_N131_DIRECT_ADDITION_FINAL_EVIDENCE_AUDIT", query["status"])


if __name__ == "__main__":
    main()
