"""Read-only end-to-end evidence verifier for this bounded signature-gate run."""

import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAT = HERE / "sat"
SUPPORT = HERE.parent / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def uncompressed(path):
    digest = hashlib.sha256()
    size = 0
    with gzip.open(path, "rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def main():
    source = read(HERE / "protocol.json")
    census = read(HERE / "census_result.json")
    hash_protocol = read(HERE / "hash_selection_protocol.json")
    hashed = read(HERE / "hash_manifest.json")
    table_audit = read(HERE / "table_audit_result.json")
    fast_protocol = read(HERE / "fast_audit_protocol.json")
    fast = read(HERE / "fast_audit_result.json")
    sat_protocol = read(SAT / "protocol.json")
    control = read(SAT / "control_result.json")
    public_protocol = read(HERE / "public_gate_protocol.json")
    query = read(SAT / "query_result.json")
    query_audit_protocol = read(HERE / "query_audit_protocol.json")
    query_audit = read(HERE / "query_audit_result.json")
    slow = read(HERE / "slow_audit_stop_receipt.json")
    assert source["sha256"] == {
        "source": sha(HERE / "census_sage.py"),
        "support": sha(SUPPORT),
        "sage_runtime": sha(HERE / "sage_runtime_info.json"),
    }
    assert census["status"] == "PASS_EXACT_W18_LINKED_SIGNATURE_SOURCE_CENSUS"
    assert census["source_codes"] == 33191 and census["pair_output_roots"] == 66382
    assert census["rows_gzip_sha256"] == sha(HERE / "rows.tsv.gz")
    assert hash_protocol["sha256"]["rows"] == sha(HERE / "rows.tsv.gz")
    assert hashed["status"] == "PASS_EXACT_ALL_SOURCE_LINEAR_SIGNATURE_SEPARATOR"
    assert hashed["first_passing_seed"] == 42
    assert hashed["signature_width_bits"] == 14
    assert table_audit["status"] == "PASS_FULL_W18_SOURCE_AND_14_BIT_SIGNATURE_TABLE_AUDIT"
    assert table_audit["pair_output_roots"] == 66382
    for key, path in {
        "source": HERE / "audit_fast_sage.py",
        "table": HERE / "rows.tsv.gz",
        "census": HERE / "census_result.json",
        "hash": HERE / "hash_manifest.json",
        "support": SUPPORT,
        "runtime": HERE / "sage_fast_audit_runtime_info.json",
    }.items():
        assert fast_protocol["sha256"][key] == sha(path), key
    assert fast["status"] == "PASS_INDEPENDENT_SAGE_ALL_W18_LINKED_ADDITION_FORMULAS"
    assert fast["source_codes"] == 33191 and fast["pair_output_roots"] == 66382
    assert fast["signed_additions_replayed"] == 265528
    assert fast["zero_signature_differences"] == 0
    assert fast["audit_protocol_sha256"] == sha(HERE / "fast_audit_protocol.json")
    assert (HERE / "fast_audit_stderr.log").stat().st_size == 0
    assert control["status"] == "PASS_FULL_N131_LINKED_TENPAIR_CONSTRUCTED_WITNESS"
    assert control["protocol_sha256"] == sha(SAT / "protocol.json")
    assert sat_protocol["worker_count"] == 1
    assert sat_protocol["combined_rss_cap_bytes"] == 4 * 1024**3
    assert public_protocol["status"] == "FROZEN_BEFORE_N131_14BIT_SIGNATURE_PUBLIC_QUERY"
    for key, path in {
        "runner": HERE / "public_gate_v3.py",
        "sat_protocol": SAT / "protocol.json",
        "constructed_control": SAT / "control_result.json",
        "control_archive": HERE / "archive_receipt.json",
        "table_audit": HERE / "table_audit_result.json",
        "hash_manifest": HERE / "hash_manifest.json",
        "fast_audit": HERE / "fast_audit_result.json",
        "fast_audit_protocol": HERE / "fast_audit_protocol.json",
        "source_table": HERE / "rows.tsv.gz",
    }.items():
        assert public_protocol["sha256"][key] == sha(path), key
    assert query["status"] == "BOUNDED_UNKNOWN"
    assert query["stop_reason"] == "TOTAL_QUERY_TIMEOUT"
    assert query["worker_count"] == 1 and query["solver_exit_code"] == -9
    assert query["public_target"] == public_protocol["public_target"]
    assert query["target_dependent_attempt_ns"] == sum(query["phase_ns"].values())
    assert query["peak_combined_rss_bytes_sampled"] < public_protocol["combined_rss_cap_bytes"]
    assert query["stdout_sha256"] == sha(SAT / "solver.stdout.txt")
    assert query["stderr_sha256"] == sha(SAT / "solver.stderr.txt")
    assert query_audit_protocol["sha256"]["audit_source"] == sha(HERE / "audit_query.py")
    assert query_audit_protocol["sha256"]["query"] == sha(SAT / "query_result.json")
    for key, path in {
        "fast_audit": HERE / "fast_audit_result.json",
        "public_gate_protocol": HERE / "public_gate_protocol.json",
        "sat_protocol": SAT / "protocol.json",
        "stdout": SAT / "solver.stdout.txt",
        "stderr": SAT / "solver.stderr.txt",
    }.items():
        assert query_audit_protocol["sha256"][key] == sha(path), key
    assert query_audit_protocol["sha256"]["ordinary_xcnf"] == query["formula"]["xcnf_sha256"]
    assert query_audit["status"] == "PASS_N131_SIGNATURE_GATE_TERMINAL_RECEIPT_AUDIT"
    assert query_audit["ordinary_xcnf_rebuilt_byte_for_byte"]
    for prefix, packed, profile in (
        ("control", SAT / "control.xcnf.gz", control["formula"]),
        ("query", SAT / "ordinary.xcnf.gz", query["formula"]),
    ):
        receipt = read(HERE / ("archive_receipt.json" if prefix == "control"
                               else "query_archive_receipt.json"))
        assert sha(packed) == receipt["gzip_sha256"]
        digest, size = uncompressed(packed)
        assert digest == receipt["raw_sha256"] == profile["xcnf_sha256"]
        assert size == receipt["raw_bytes"] == profile["xcnf_bytes"]
        if prefix == "query":
            assert receipt["query_archive_protocol_sha256"] == sha(HERE / "query_archive_protocol.json")
    assert slow["status"] == "OPERATOR_STOPPED_REDUNDANT_POINT_OBJECT_AUDIT"
    assert slow["exit_code"] == 143 and slow["progress_rows"] == []
    assert slow["sha256"]["stdout"] == sha(HERE / "audit_stdout.log")
    assert slow["sha256"]["stderr"] == sha(HERE / "audit_stderr.log")
    assert "does not depend on any axioms" in (HERE / "lean_check.log").read_text()
    print("PASS_N131_SIGNATURE_GATE_FINAL_EVIDENCE_AUDIT")


if __name__ == "__main__":
    main()
