#!/usr/bin/env python3
"""Bind W18 bridge, frozen native stage, and independent GCD-root replay."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    bridge_protocol = read("protocol.json")
    bridge = read("result.json")
    protocol = read("native_protocol.json")
    run = read("native_run_status.json")
    result = read("native_result.json")
    audit = read("native_audit.json")
    assert bridge_protocol["status"] == protocol["status"] == "FROZEN"
    for source, digest in bridge_protocol["sources"].items():
        assert sha(Path(source)) == digest, source
    for source, digest in protocol["sources"].items():
        assert sha(Path(source)) == digest, source
    assert bridge["status"] == "PASS_N131_W18_CONSTRUCTED_SOURCE_RESULTANT_BRIDGE"
    assert bridge["full_product_dimension"] == 17
    assert bridge["usable_pair_counts_by_slot"] == [32947,32916,32827,32842]
    assert bridge["pair_equation_values"] == [0]*4
    assert bridge["fouratom_resultant_values"] == [0,0]
    assert bridge["pair_upper_values"] == [0,0]
    assert bridge["target_upper_value"] == 0
    assert bridge["source_sha256"]["protocol"] == sha(HERE / "protocol.json")
    assert bridge["source_sha256"]["script"] == sha(HERE / "check.py")
    assert protocol["worker_count"] == 1
    assert protocol["query_cap_seconds"] == 600
    assert protocol["rss_cap_bytes"] == 4*(1 << 30)
    assert run["status"] == "EXIT_0" and run["exit_code"] == 0
    assert run["stop_reason"] is None
    assert run["parent_wall_seconds"] < protocol["parent_wall_cap_seconds"]
    assert run["sampled_peak_rss_bytes"] < protocol["rss_cap_bytes"]
    assert run["source_sha256"]["protocol"] == sha(HERE / "native_protocol.json")
    for key, name in (("input", "native_input.txt"), ("binary", "native_w18"),
                      ("stdout", "native.stdout.txt"), ("stderr", "native.stderr.txt"),
                      ("native_result", "native_result.json")):
        assert run["source_sha256"][key] == sha(HERE / name)
    assert result["status"] == "COMPLETE_ALGEBRAIC_SCAN"
    assert result["total_product_states"] == result["processed_product_states"] == 32947
    assert result["full_second_product_space_size"] == 1 << 17
    assert result["seed_masks"] == [7,3]
    assert len(result["hits"]) == 1 and result["hits"][0]["gcd_degree"] == 1
    assert result["peak_rss_bytes"] < protocol["rss_cap_bytes"]
    assert audit["status"] == "PASS_NATIVE_W18_GCD_SOURCE_REPLAY"
    assert audit["first_masks"] == [3,4] and audit["second_masks"] == [17,18]
    assert audit["first_product"] == 48
    assert audit["second_product_usable"] and audit["fouratom_resultant_zero"]
    for key, name in (("native_protocol", "native_protocol.json"),
                      ("native_result", "native_result.json"),
                      ("preflight_result", "result.json"),
                      ("sage_runtime_info", "sage_runtime_info.json"),
                      ("auditor", "audit_sage.py")):
        assert audit["source_sha256"][key] == sha(HERE / name)
    receipt = {
        "status": "PASS_N131_W18_FULL_BIN_GCD_AND_SOURCE_REPLAY",
        "curve_id": bridge["curve_id"],
        "target_kind": "constructed_correctness_control",
        "processed_first_products": result["processed_product_states"],
        "full_second_product_space_size": result["full_second_product_space_size"],
        "native_query_ns": result["query_ns"],
        "native_setup_ns": result["setup_ns"],
        "native_peak_rss_bytes": result["peak_rss_bytes"],
        "parent_wall_seconds": run["parent_wall_seconds"],
        "source_sha256": {name: sha(HERE / name) for name in (
            "protocol.json", "result.json", "native_protocol.json",
            "native_result.json", "native_run_status.json", "native_audit.json")},
    }
    (HERE / "terminal_verification.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(receipt["status"])


if __name__ == "__main__":
    main()
