#!/usr/bin/env python3
"""Check frozen source, complete subset, group replay, and phase receipts."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    protocol = read("subset_protocol.json")
    result = read("subset_result.json")
    audit = read("subset_audit.json")
    query = read("subset_query_run_status.json")
    replay = read("subset_audit_run_status.json")
    partial = read("query_run_status.json")
    assert protocol["status"] == "FROZEN"
    assert protocol["target_count"] == 1 and protocol["batch"] is False
    for path, digest in protocol["sources"].items():
        assert sha(Path(path)) == digest, path
    assert partial["status"] == "CENSORED_TIME"
    assert partial["stop_reason"] == "WALL_CAP"
    assert 180 <= partial["parent_wall_seconds"] < 190
    assert result["protocol_sha256"] == sha(HERE / "subset_protocol.json")
    assert [r["id"] for r in result["cases"]] == protocol["left_family_ids"]
    assert [r["id"] for r in audit["cases"]] == protocol["left_family_ids"]
    assert audit["status"] == "PASS_INDEPENDENT_TARGET_FIBER_GROUP_REPLAY"
    assert audit["total_signed_combinations"] == 4 * 16 * 16384
    assert audit["source_sha256"]["protocol"] == sha(HERE / "subset_protocol.json")
    assert audit["source_sha256"]["query_result"] == sha(HERE / "subset_result.json")
    assert audit["source_sha256"]["auditor"] == sha(HERE / "audit_subset_sage.py")
    for phase, receipt, script in (("query", query, "query_subset_sage.py"),
                                    ("audit", replay, "audit_subset_sage.py")):
        assert receipt["phase"] == phase and receipt["status"] == "EXIT_0"
        assert receipt["exit_code"] == 0 and receipt["stop_reason"] is None
        assert receipt["parent_wall_seconds"] < protocol[f"{phase}_wall_cap_seconds"]
        assert receipt["sampled_peak_process_tree_rss_bytes"] < protocol["process_tree_rss_cap_bytes"]
        assert receipt["source_sha256"]["protocol"] == sha(HERE / "subset_protocol.json")
        assert receipt["source_sha256"]["script"] == sha(HERE / script)
        assert receipt["source_sha256"]["stdout"] == sha(HERE / f"subset_{phase}_stdout.log")
        assert receipt["source_sha256"]["stderr"] == sha(HERE / f"subset_{phase}_stderr.log")
        assert receipt["source_sha256"]["sage_runtime_info"] == sha(HERE / "sage_runtime_info.json")
    for algebraic, geometric in zip(result["cases"], audit["cases"]):
        assert algebraic["id"] == geometric["id"]
        assert algebraic["left_roots"] == 8
        assert algebraic["target_derived_right_candidates"] == 16
        assert bool(algebraic["hits"]) == bool(geometric["group_law_matches"])
        assert len(algebraic["hits"]) == geometric["fiber_query_hits"]
    assert [len(row["hits"]) for row in result["cases"]] == [1, 0, 0, 0]
    assert [row["group_law_matches"] for row in audit["cases"]] == [1, 0, 0, 0]
    receipt = {
        "status": "PASS_COMPLETE_FOUR_FAMILY_TARGET_FIBER_RECEIPT",
        "case_count": 4, "target_count": 1,
        "total_gcds": sum(row["gcds"] for row in result["cases"]),
        "signed_group_combinations": audit["total_signed_combinations"],
        "partial_sweep_status": partial["status"],
        "query_monitor_degraded": query["process_tree_monitor_degraded"],
        "audit_monitor_degraded": replay["process_tree_monitor_degraded"],
        "source_sha256": {name: sha(HERE / name) for name in (
            "subset_protocol.json", "subset_result.json", "subset_audit.json",
            "subset_query_run_status.json", "subset_audit_run_status.json")},
    }
    (HERE / "terminal_verification.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(receipt["status"])


if __name__ == "__main__":
    main()
