#!/usr/bin/env python3
"""Bind the capped source, exact decisions, excluded-root control, and audit."""

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
    result = read("result.json")
    status = read("query_run_status.json")
    invalid = read("invalid_control.json")
    audit = read("audit.json")
    assert protocol["status"] == "FROZEN" and protocol["target_count"] == 1
    for path, digest in protocol["sources"].items():
        assert sha(Path(path)) == digest, path
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert result["status"] == "PASS_LINEARIZED_SUPERSET_SOURCE_FILTER_PANEL"
    assert result["full_product_space_size"] == 128
    assert result["usable_product_count"] == 32
    assert result["linearized_polynomial_nonzero_exponents"] == [1,2,4,8,16,32,64,128]
    assert [x["id"] for x in result["cases"]] == protocol["left_family_ids"]
    assert [len(x["hits"]) for x in result["cases"]] == [1,0]
    assert [x["gcds"] for x in result["cases"]] == [481,512]
    assert status["status"] == "EXIT_0" and status["exit_code"] == 0
    assert status["stop_reason"] is None
    assert status["parent_wall_seconds"] < protocol["query_wall_cap_seconds"]
    assert status["sampled_peak_process_tree_rss_bytes"] < protocol["process_tree_rss_cap_bytes"]
    for key, name in (("protocol", "protocol.json"), ("script", "query_sage.py"),
                      ("stdout", "query_stdout.log"), ("stderr", "query_stderr.log"),
                      ("sage_runtime_info", "sage_runtime_info.json")):
        assert status["source_sha256"][key] == sha(HERE / name)
    assert invalid["status"] == "PASS_INVALID_SUPERSET_ROOT_REJECTED"
    assert invalid["excluded_products_checked"] == 96
    assert invalid["excluded_products_with_field_roots"] == 1
    assert invalid["control"]["invalid_product"] == 0
    assert invalid["control"]["unfiltered_superset_gcd_degree"] == 1
    assert invalid["control"]["usable_source_hits"] == 0
    for key, name in (("protocol", "protocol.json"), ("query_result", "result.json"),
                      ("script", "invalid_control_sage.py")):
        assert invalid["source_sha256"][key] == sha(HERE / name)
    assert audit["status"] == "PASS_INDEPENDENT_PAIR_EQUATION_SOURCE_FILTER_AUDIT"
    assert (audit["positive_valid_pair_equation_matches"],
            audit["invalid_valid_pair_equation_matches"],
            audit["invalid_excluded_pair_equation_matches"]) == (1,0,1)
    for key, name in (("protocol", "protocol.json"), ("query_result", "result.json"),
                      ("invalid_control", "invalid_control.json"),
                      ("auditor", "audit_sage.py")):
        assert audit["source_sha256"][key] == sha(HERE / name)
    receipt = {
        "status": "PASS_LINEARIZED_SUPERSET_FILTER_AND_EXCLUDED_ROOT_RECEIPT",
        "target_count": 1,
        "ordinary_family_decisions": [1,0],
        "excluded_zero_product_control": True,
        "independent_pair_equation_counts": [1,0,1],
        "query_parent_wall_seconds": status["parent_wall_seconds"],
        "sampled_peak_process_tree_rss_bytes": status["sampled_peak_process_tree_rss_bytes"],
        "process_tree_monitor_degraded": status["process_tree_monitor_degraded"],
        "source_sha256": {name: sha(HERE / name) for name in (
            "protocol.json", "result.json", "query_run_status.json",
            "invalid_control.json", "audit.json")},
    }
    (HERE / "terminal_verification.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(receipt["status"])


if __name__ == "__main__":
    main()
