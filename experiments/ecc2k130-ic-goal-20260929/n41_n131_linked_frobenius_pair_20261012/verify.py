"""Read-only digest and cross-record auditor for this linked-pair experiment."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(name):
    return json.loads((HERE / name).read_text())


def main():
    protocol = record("protocol.json")
    receipt = record("receipt.json")
    audit_protocol = record("audit_protocol.json")
    audit = record("audit_result.json")
    projection_protocol = record("projection_protocol.json")
    projection = record("projection_result.json")
    checks = [
        ("source", HERE / "join_linked.cpp"),
        ("binary", HERE / "join_linked"),
        ("runner", HERE / "run.py"),
        ("input", PARENT / "n41_w8_sixpair_mitm_20261011" / "join_input.tsv"),
    ]
    for key, path in checks:
        assert sha(path) == protocol["sha256"][key], (key, path)
    assert receipt["protocol_sha256"] == sha(HERE / "protocol.json")
    assert receipt["stdout_sha256"] == sha(HERE / "stdout.log")
    assert receipt["stderr_sha256"] == sha(HERE / "stderr.log")
    assert receipt["exit_code"] == 0 and receipt["worker_count"] == 1
    assert receipt["runner_wall_ns"] < 180 * 10**9
    assert receipt["peak_combined_rss_bytes_sampled"] < 4 * 2**30
    assert receipt["hit_line"] in (HERE / "stdout.log").read_text()
    for key, filename in (("audit_source", "audit_sage.py"),
                          ("native_receipt", "receipt.json"),
                          ("stdout", "stdout.log"),
                          ("sage_runtime", "sage_runtime_info.json")):
        assert audit_protocol["sha256"][key] == sha(HERE / filename)
    assert audit["sha256"]["audit_source"] == sha(HERE / "audit_sage.py")
    assert audit["status"] == "PASS_INDEPENDENT_N41_LINKED_FROBENIUS_PUBLIC_RELATION"
    assert audit["source_pairs_free"] == 9
    assert audit["source_edges_distinct"] == 9
    assert audit["folded_columns_nonzero"] == 18
    assert audit["rank_after_with_linked_row"] == audit["rank_before_with_prior_six_nine_ten"] + 1
    assert projection_protocol["sha256"]["projection_source"] == sha(HERE / "projection.py")
    assert projection["sha256"]["projection_source"] == sha(HERE / "projection.py")
    assert projection["status"] == "PASS_CONSERVATIVE_LABELED_SOURCE_PROJECTION"
    assert all(int(x) for x in projection["one_plus_lambda_pow_16_for_each_root_mod_r"])
    print("PASS_LINKED_PAIR_RECEIPT_AUDIT")


if __name__ == "__main__":
    main()
