#!/usr/bin/env python3
"""Replay the sealed four-call RunPod root-index stage receipts."""

import json
import statistics
import subprocess
from pathlib import Path

import run


HERE = Path(__file__).resolve().parent
SOURCE_COMMIT = "b57a02234"
SOURCE_PATH = ("experiments/koblitz-n83-index-design-20260929/"
               "packed_index_e1_runpod_tier1_20261019/")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def main():
    protocol, manifest = run.load_seal()
    for name in ("Cargo.toml", "Cargo.lock", "native_packed_index.rs",
                 "run.py", "protocol.json", "stage_manifest.json", "workload.json"):
        archived = subprocess.run(
            ["git", "show", f"{SOURCE_COMMIT}:{SOURCE_PATH}{name}"],
            cwd=HERE.parents[2], capture_output=True, check=True).stdout
        require((HERE / name).read_bytes() == archived,
                f"{name} differs from the premeasurement source commit")

    host = json.loads((HERE / "build_receipt.json").read_text())
    require(host["protocol_sha256"] == run.digest(HERE / "protocol.json") and
            host["stage_manifest_sha256"] == run.digest(HERE / "stage_manifest.json") and
            host["workload_sha256"] == run.digest(HERE / "workload.json") and
            host["source_sha256"] == protocol["inputs_sha256"]["native_source"] and
            host["runpod_pod_id"] == protocol["runpod"]["pod_id"] and
            host["machine"] == "x86_64" and
            host["host_isolation_receipt"] is None,
            "build receipt does not match the sealed Tier 1 inputs")
    topology = host["topology_and_cgroup_before_panel"]
    require(len(topology["affinity_cpus"]) == 8 and
            topology["affinity_cpus"] == sorted(topology["affinity_cpus"]) and
            topology["cpu_max"] == "max 100000" and
            int(topology["memory_max"]) == 16_000_000_000,
            "RunPod exposed resource envelope differs")

    cap = protocol["limits"]["peak_rss_cap_mib"] * 1024 * 1024
    require(cap == 1_073_741_824 and
            protocol["limits"]["pair_state_cap"] == 4_000_000 and
            protocol["limits"]["hard_os_memory_limit"] is None and
            protocol["run_order"] == ["hash", "split-hash", "split-hash", "hash"],
            "bounded protocol differs")
    raw = []
    for number, mode in enumerate(protocol["run_order"], 1):
        stem = f"run_{number}_{mode}"
        output = HERE / f"{stem}.json"
        record = json.loads((HERE / f"{stem}.record.json").read_text())
        result = json.loads(output.read_text())
        envelope = record["tier1_envelope"]
        require(record["sequence_number"] == number and
                record["mode"] == mode and
                record["execution_status"] == "completed" and
                record["exit_code"] == 0 and
                record["raw_result_sha256"] == run.digest(output) and
                record["host"] == host and
                result["index_mode"] == mode and
                result["curve_id"] == protocol["curve_id"] and
                result["workload_id"] == protocol["workload_id"] and
                result["native_source_sha256"] == host["source_sha256"] and
                result["stage_protocol_sha256"] == host["protocol_sha256"] and
                result["input_representatives_sha256"] ==
                    protocol["inputs_sha256"]["representatives"] and
                result["status"] == "state_cap_no_relation" and
                result["index_pair_states_examined"] == 4_000_000 and
                result["target_states_scanned"] == 4_000_000 and
                result["peak_rss_bytes"] <= cap and
                result["relation"] is None and
                result["target_table_hits"] == 0 and
                result["native_s3_generator_target_control"]["status"] == "PASS",
                f"{stem}: raw result or first-attempt record differs")
        require(envelope["before"]["affinity_cpus"] == topology["affinity_cpus"] and
                envelope["after"]["affinity_cpus"] == topology["affinity_cpus"] and
                envelope["before"]["cpu_max"] == topology["cpu_max"] and
                envelope["after"]["cpu_max"] == topology["cpu_max"] and
                envelope["before"]["memory_max"] == topology["memory_max"] and
                envelope["after"]["memory_max"] == topology["memory_max"] and
                envelope["cgroup_nr_throttled_delta"] == 0 and
                envelope["cgroup_throttled_usec_delta"] == 0 and
                envelope["host_steal_jiffies_delta"] == 0 and
                envelope["calibration_before_ns"] > 0 and
                envelope["calibration_after_ns"] > 0 and
                envelope["calibration_ratio"] >= 1,
                f"{stem}: exposed host envelope or counters differ")
        require((HERE / f"{stem}.stderr.txt").read_bytes() == b"",
                f"{stem}: unexpected worker stderr")
        raw.append(result)

    for key in ("curve_id", "workload_id", "factor_base_enumerated_set_sha256",
                "lookup_sample", "native_s3_generator_target_control",
                "index_satisfiable_s3_states", "index_distinct_root_keys"):
        require(all(item[key] == raw[0][key] for item in raw[1:]),
                f"cross-layout invariant {key} differs")
    summary = json.loads((HERE / "summary.json").read_text())
    require(summary["status"] == "validated_bounded_capacity_screen" and
            summary["protocol_sha256"] == run.digest(HERE / "protocol.json") and
            summary["source_sha256"] == host["source_sha256"] and
            summary["curve_id"] == manifest["curve_id"] and
            summary["workload_id"] == manifest["workload_id"] and
            summary["actual_usable_points_B"] == manifest["actual_usable_points_B"] and
            summary["folded_columns_K"] == manifest["representative_count_K"] and
            summary["invariant_mismatches"] == {} and
            all(not v for v in summary["within_mode_variation"].values()) and
            len(summary["paired_rows"]) == 4 and
            summary["candidate_id"] is None and
            summary["online_speedup"] is None,
            "summary identity or outcome differs")
    for number, (item, row) in enumerate(zip(raw, summary["paired_rows"]), 1):
        require(row["sequence_number"] == number and
                row["mode"] == item["index_mode"] and
                row["status"] == item["status"] and
                row["index_pair_states_examined"] == item["index_pair_states_examined"] and
                row["target_states_scanned"] == item["target_states_scanned"] and
                row["peak_rss_bytes"] == item["peak_rss_bytes"] and
                row["table_allocated_bytes"] == item["root_table_allocated_bytes"] and
                row["target_stage_ns"] ==
                    int(item["timing_ns"]["target_pdp_and_native_check"]) and
                row["verified_relation"] is False,
                f"summary row {number} differs from raw result")
    for mode in ("hash", "split-hash"):
        selected = [item for item in raw if item["index_mode"] == mode]
        for field, original in (("peak_rss_bytes", "peak_rss_bytes"),
                                ("table_allocated_bytes", "root_table_allocated_bytes"),
                                ("target_stage_ns", "timing_ns")):
            values = [int(item["timing_ns"]["target_pdp_and_native_check"])
                      if original == "timing_ns" else item[original] for item in selected]
            require(summary["medians"][mode][field] == statistics.median(values),
                    f"{mode}: median {field} differs from raw results")
    hash_peak = summary["medians"]["hash"]["peak_rss_bytes"]
    split_peak = summary["medians"]["split-hash"]["peak_rss_bytes"]
    require(hash_peak - split_peak == 201_326_592 and
            summary["medians"]["hash"]["table_allocated_bytes"] -
            summary["medians"]["split-hash"]["table_allocated_bytes"] ==
            134_217_728,
            "memory reduction differs from independent raw replay")
    print(json.dumps({"status": "PASS_SEALED_RUNPOD_TIER1_STAGE_REPLAY",
                      "source_commit": SOURCE_COMMIT, "calls": 4,
                      "hash_peak_rss_bytes": hash_peak,
                      "split_peak_rss_bytes": split_peak,
                      "peak_rss_reduction_bytes": hash_peak - split_peak,
                      "candidate_id": None, "online_speedup": None}, sort_keys=True))


if __name__ == "__main__":
    main()
