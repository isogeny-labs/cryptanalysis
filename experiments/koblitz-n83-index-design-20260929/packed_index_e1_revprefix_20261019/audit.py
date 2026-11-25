#!/usr/bin/env python3
"""Independently replay the sealed N83 three-layout root-index receipts."""

import json
import statistics
import subprocess
from pathlib import Path

import run


HERE = Path(__file__).resolve().parent
SOURCE_COMMIT = "b915f02fd"
SOURCE_PATH = ("experiments/koblitz-n83-index-design-20260929/"
               "packed_index_e1_revprefix_20261019/")


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
                result["status"] == "state_cap_no_relation" and
                result["relation"] is None and
                result["index_pair_states_examined"] == 2_000_000 and
                result["target_states_scanned"] == 2_000_000 and
                result["target_table_hits"] == 0,
                f"{stem}: raw receipt or declared cap differs")
        require((HERE / f"{stem}.stderr.txt").read_bytes() == b"",
                f"{stem}: stderr is not empty")
        raw.append(result)
        rows.append(record)
    fixed = ("curve_id", "workload_id", "factor_base_enumerated_set_sha256",
             "index_pair_states_examined", "index_satisfiable_s3_states",
             "index_distinct_root_keys", "target_states_scanned",
             "target_state_orientations_tested", "status", "relation",
             "lookup_sample", "operation_counts",
             "native_s3_generator_target_control", "target_table_hits",
             "target_partner_roots", "verified_single_target_dlp")
    require(all(all(result[key] == raw[0][key] for key in fixed) for result in raw),
            "a cross-layout correctness invariant differs")
    summary = json.loads((HERE / "summary.json").read_text())
    expected_summary = run.summarize(rows, protocol, manifest)
    require(summary == expected_summary and not summary["invariant_mismatches"] and
            summary["status"] == "validated_stage_comparison" and
            summary["candidate_id"] is None and
            summary["online_speedup"] is None,
            "summary differs from the raw run set")
    medians = {mode: {
        "target_stage_ms": statistics.median(
            int(result["timing_ns"]["target_pdp_and_native_check"]) / 1e6
            for result in raw if result["index_mode"] == mode),
        "lookup_comparisons_or_probes": int(raw[protocol["run_order"].index(mode)]
            ["root_table_hash_probes"]["target_lookup"]),
    } for mode in ("hash", "packed", "packed-rev")}
    print(json.dumps({"status": "PASS_SEALED_THREE_LAYOUT_PANEL",
                      "source_commit": SOURCE_COMMIT,
                      "calls": len(raw), "medians": medians,
                      "candidate_id": None, "online_speedup": None},
                     sort_keys=True))


if __name__ == "__main__":
    main()
