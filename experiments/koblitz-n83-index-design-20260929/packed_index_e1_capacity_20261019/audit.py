#!/usr/bin/env python3
"""Independently replay the sealed N83 four-million-state capacity receipts."""

import json
import statistics
import subprocess
from pathlib import Path

import run


HERE = Path(__file__).resolve().parent
SOURCE_COMMIT = "7d41c7aa6"
SOURCE_PATH = ("experiments/koblitz-n83-index-design-20260929/"
               "packed_index_e1_capacity_20261019/")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    protocol, manifest = run.load_seal()
    for name, expected in (("native_packed_index.rs", "native_source"),
                           ("run.py", "runner"),
                           ("protocol.json", None)):
        archived = subprocess.run(
            ["git", "show", f"{SOURCE_COMMIT}:{SOURCE_PATH}{name}"],
            cwd=HERE.parents[2], check=True, capture_output=True,
        ).stdout
        actual = (HERE / name).read_bytes()
        require(archived == actual, f"sealed {name} changed since source commit")
        if expected:
            require(run.digest(HERE / name) == protocol["inputs_sha256"][expected],
                    f"sealed {name} digest differs")
    build = json.loads((HERE / "build_receipt.json").read_text())
    require(build["protocol_sha256"] == run.digest(HERE / "protocol.json") and
            build["stage_manifest_sha256"] == run.digest(HERE / "stage_manifest.json") and
            build["workload_sha256"] == run.digest(HERE / "workload.json") and
            build["source_sha256"] == protocol["inputs_sha256"]["native_source"] and
            build["host_isolation_receipt"] is None,
            "build receipt differs from sealed inputs")
    raw = []
    rows = []
    cap_bytes = protocol["limits"]["peak_rss_cap_mib"] * 1024 * 1024
    require(cap_bytes == 1_073_741_824 and
            protocol["limits"]["pair_state_cap"] == 4_000_000 and
            protocol["limits"]["hard_os_memory_limit"] is None,
            "capacity protocol differs")
    for number, mode in enumerate(protocol["run_order"], 1):
        stem = f"run_{number}_{mode}"
        output = HERE / f"{stem}.json"
        record = json.loads((HERE / f"{stem}.record.json").read_text())
        result = json.loads(output.read_text())
        require(record["sequence_number"] == number and record["mode"] == mode and
                record["execution_status"] == "completed" and
                record["exit_code"] == 0 and
                record["raw_result_sha256"] == run.digest(output) and
                record["host"] == build and
                result["index_mode"] == mode and
                result["native_source_sha256"] == build["source_sha256"] and
                result["stage_protocol_sha256"] == build["protocol_sha256"] and
                result["curve_id"] == protocol["curve_id"] and
                result["workload_id"] == protocol["workload_id"] and
                result["native_s3_generator_target_control"]["status"] == "PASS" and
                result["relation"] is None and
                result["target_table_hits"] == 0,
                f"{stem}: raw receipt or declared cap differs")
        if mode == "hash":
            require(result["status"] == "memory_cap_exceeded" and
                    result["index_pair_states_examined"] == 3_235_840 and
                    result["target_states_scanned"] == 0 and
                    result["peak_rss_bytes"] == 1_073_954_816 and
                    result["peak_rss_bytes"] > cap_bytes and
                    result["root_table_allocated_bytes"] == 402_653_184,
                    f"{stem}: hash cap receipt differs")
        else:
            require(mode == "split-hash" and
                    result["status"] == "state_cap_no_relation" and
                    result["index_pair_states_examined"] == 4_000_000 and
                    result["target_states_scanned"] == 4_000_000 and
                    result["peak_rss_bytes"] == 1_052_164_096 and
                    result["peak_rss_bytes"] <= cap_bytes and
                    result["root_table_allocated_bytes"] == 268_435_456,
                    f"{stem}: split completion receipt differs")
        require((HERE / f"{stem}.stderr.txt").read_bytes() == b"",
                f"{stem}: stderr is not empty")
        raw.append(result)
        rows.append(record)
    fixed = ("curve_id", "workload_id", "factor_base_enumerated_set_sha256",
             "lookup_sample", "native_s3_generator_target_control")
    require(all(all(result[key] == raw[0][key] for key in fixed) for result in raw),
            "a cross-layout correctness invariant differs")
    summary = json.loads((HERE / "summary.json").read_text())
    require(summary["protocol_sha256"] == run.digest(HERE / "protocol.json") and
            summary["source_sha256"] == protocol["inputs_sha256"]["native_source"] and
            summary["curve_id"] == manifest["curve_id"] and
            summary["workload_id"] == manifest["workload_id"] and
            summary["actual_usable_points_B"] == manifest["actual_usable_points_B"] and
            summary["folded_columns_K"] == manifest["representative_count_K"] and
            len(summary["paired_rows"]) == len(raw) and
            not summary["invariant_mismatches"] and
            summary["status"] == "validated_bounded_capacity_screen" and
            all(not variation for variation in summary["within_mode_variation"].values()) and
            summary["candidate_id"] is None and
            summary["online_speedup"] is None,
            "summary differs from the raw run set")
    for number, (result, row) in enumerate(zip(raw, summary["paired_rows"]), 1):
        require(row["sequence_number"] == number and
                row["mode"] == result["index_mode"] and
                row["status"] == result["status"] and
                row["index_pair_states_examined"] ==
                    result["index_pair_states_examined"] and
                row["index_satisfiable_s3_states"] ==
                    result["index_satisfiable_s3_states"] and
                row["target_states_scanned"] == result["target_states_scanned"] and
                row["peak_rss_bytes"] == result["peak_rss_bytes"] and
                row["table_allocated_bytes"] ==
                    result["root_table_allocated_bytes"] and
                row["verified_relation"] is False,
                f"summary row {number} differs from raw bytes")
    for mode in ("hash", "split-hash"):
        selected = [result for result in raw if result["index_mode"] == mode]
        require(summary["index_satisfiable_states_by_mode"][mode] ==
                    [result["index_satisfiable_s3_states"] for result in selected] and
                summary["distinct_root_keys_by_mode"][mode] ==
                    [result["index_distinct_root_keys"] for result in selected] and
                summary["medians"][mode]["peak_rss_bytes"] ==
                    statistics.median(result["peak_rss_bytes"] for result in selected),
                f"{mode}: summary capacity values differ from raw bytes")
    split_ms = statistics.median(
        int(result["timing_ns"]["target_pdp_and_native_check"]) / 1e6
        for result in raw if result["index_mode"] == "split-hash")
    print(json.dumps({"status": "PASS_SEALED_CAPACITY_DIFFERENCE",
                      "source_commit": SOURCE_COMMIT,
                      "calls": len(raw), "hash_index_states": 3_235_840,
                      "split_index_states": 4_000_000,
                      "hash_peak_rss_bytes": 1_073_954_816,
                      "split_peak_rss_bytes": 1_052_164_096,
                      "split_target_stage_median_ms": split_ms,
                      "candidate_id": None, "online_speedup": None},
                     sort_keys=True))


if __name__ == "__main__":
    main()
