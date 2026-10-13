"""Check the frozen constructed N131 right-block experiment and coverage bound."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
GOAL = HERE.parent


def read(name):
    return json.loads((HERE / name).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_sources(record):
    for name, expected in record["sources"].items():
        assert digest(name) == expected, name


protocol = read("protocol.json")
pipeline_protocol = read("pipeline_protocol.json")
audit_protocol = read("audit_protocol.json")
for frozen in (protocol, pipeline_protocol, audit_protocol):
    assert frozen["status"] == "FROZEN"
    check_sources(frozen)
assert protocol["target_kind"] == "constructed_correctness_control"
assert protocol["left_input_law"] == pipeline_protocol["left_input_law"]

preview = read("preview_targets.json")
targets = read("target_candidates.json")
assert targets["rows"] == preview["rows"]
assert targets["public_target"] == protocol["public_target"]
assert targets["candidate_count"] == targets["distinct_candidate_count"] == 8
right_roots = [root for row in targets["rows"] for root in row["right_roots"]]
assert len(right_roots) == 8

pipeline = read("pipeline_result.json")
assert pipeline["status"] == "COMPLETE_ALL_TARGET_DERIVED_RIGHT_CANDIDATES"
assert pipeline["target_count"] == pipeline["worker_count"] == 1
assert pipeline["source_sha256"]["protocol"] == digest(HERE / "pipeline_protocol.json")
assert pipeline["source_sha256"]["runner"] == digest(HERE / "run_pipeline.py")
assert pipeline["target_candidates_sha256"] == digest(HERE / "target_candidates.json")
assert len(pipeline["attempts"]) == 8
assert pipeline["phase_wall_ns"]["T_target_query"] == pipeline["target_derivation"]["wall_ns"]
assert pipeline["phase_wall_ns"]["T_target_PDP"] == sum(
    item["wall_ns"] for item in pipeline["attempts"]
)
assert pipeline["partial_target_dependent_parent_wall_ns"] == (
    pipeline["phase_wall_ns"]["T_target_query"]
    + pipeline["phase_wall_ns"]["T_target_PDP"]
    + pipeline["unassigned_parent_overhead_ns"]
)
assert pipeline["partial_target_dependent_parent_wall_ns"] < 600_000_000_000
assert pipeline["peak_sampled_combined_rss_bytes"] < protocol["rss_cap_bytes"]
assert pipeline["complete_one_target_online_wall_ns"] is None
assert pipeline["candidate_id"] is None

for label, item in enumerate(pipeline["attempts"]):
    directory = HERE / f"attempt_{label:02d}"
    native = read(f"attempt_{label:02d}/native_result.json")
    assert item["index"] == label
    assert item["right_reciprocal"] == right_roots[label]
    assert item["input_sha256"] == digest(directory / "input.txt")
    assert item["native_result_sha256"] == digest(directory / "native_result.json")
    assert item["sha256"]["stdout"] == digest(directory / "solver.stdout.txt")
    assert item["sha256"]["stderr"] == digest(directory / "solver.stderr.txt")
    assert item["exit_code"] == 0 and item["stop_reason"] is None
    assert item["native_status"] == native["status"] == "COMPLETE_ALGEBRAIC_SCAN"
    assert item["processed_first_products"] == native["processed_product_states"] == 32827
    assert native["total_product_states"] == 32827
    assert native["full_second_product_space_size"] == 131072
    assert item["raw_gcd_hits"] == len(native["hits"]) == (1 if label == 5 else 0)

audit = read("audit_result.json")
audit_run = read("audit_run_status.json")
assert audit["status"] == "PASS_TARGET_DERIVED_N131_RIGHT_SOURCE_AND_GROUP_REPLAY"
assert audit["source_sha256"]["audit_protocol"] == digest(HERE / "audit_protocol.json")
assert audit["source_sha256"]["native_hit"] == digest(HERE / "attempt_05/native_result.json")
assert audit["source_sha256"]["pipeline_result"] == digest(HERE / "pipeline_result.json")
assert audit["source_sha256"]["script"] == digest(HERE / "audit_sage.py")
assert audit_run["status"] == "EXIT_0" and audit_run["exit_code"] == 0
assert audit_run["audit_result_sha256"] == digest(HERE / "audit_result.json")
assert audit_run["audit_protocol_sha256"] == digest(HERE / "audit_protocol.json")
assert audit_run["sha256"]["stdout"] == digest(HERE / "audit.stdout.txt")
assert audit_run["sha256"]["stderr"] == digest(HERE / "audit.stderr.txt")
assert audit_run["wall_ns"] < 120_000_000_000
assert audit_run["sampled_peak_combined_rss_bytes"] < protocol["rss_cap_bytes"]
assert audit["candidate_index"] == 5 and audit["raw_gcd_hit_count"] == 1
assert audit["right_source_pairs"] == [[19, 22], [24, 25]]
assert audit["all_folded_columns"] == [3, 4, 17, 18, 19, 22, 24, 25]
assert audit["signed_assignments_checked"] == 256
assert len(audit["public_group_matches"]) == 1

bridge_path = GOAL / "n131_linearized_superset_preflight_20261013/result.json"
bridge = json.loads(bridge_path.read_text())
assert bridge["status"] == "PASS_N131_W18_CONSTRUCTED_SOURCE_RESULTANT_BRIDGE"
assert bridge["usable_pair_counts_by_slot"] == [32947, 32916, 32827, 32842]
first, second = bridge["usable_pair_counts_by_slot"][2:]
labelled_choices = 16 * first * second
order = protocol["subgroup_order"]
assert labelled_choices == 17_249_669_344
assert labelled_choices < order

result = {
    "status": "PASS_CONSTRUCTED_RIGHT_BLOCK_TERMINAL_CHECK",
    "curve_id": protocol["curve_id"],
    "target_kind": protocol["target_kind"],
    "left_input_law": protocol["left_input_law"],
    "candidate_id": None,
    "ordinary_target_online_wall_ns": None,
    "right_pair_usable_counts": [first, second],
    "right_signed_labelled_choices": labelled_choices,
    "uniform_subgroup_target_coverage_upper_fraction": [labelled_choices, order],
    "fixed_left_source_bound_input_sha256": digest(bridge_path),
    "public_target": protocol["public_target"],
    "target_derived_right_candidates": 8,
    "complete_native_scans": 8,
    "total_first_product_states_processed": sum(
        item["processed_first_products"] for item in pipeline["attempts"]
    ),
    "source_checked_raw_hits": 1,
    "signed_assignments_checked": 256,
    "public_group_matches": 1,
    "pipeline_parent_wall_ns": pipeline["partial_target_dependent_parent_wall_ns"],
    "separate_audit_parent_wall_ns": audit_run["wall_ns"],
    "sum_of_separate_parent_intervals_ns": (
        pipeline["partial_target_dependent_parent_wall_ns"] + audit_run["wall_ns"]
    ),
    "pipeline_peak_sampled_combined_rss_bytes": pipeline["peak_sampled_combined_rss_bytes"],
    "audit_peak_sampled_combined_rss_bytes": audit_run["sampled_peak_combined_rss_bytes"],
    "pipeline_protocol_sha256": digest(HERE / "pipeline_protocol.json"),
    "audit_protocol_sha256": digest(HERE / "audit_protocol.json"),
    "pipeline_result_sha256": digest(HERE / "pipeline_result.json"),
    "audit_result_sha256": digest(HERE / "audit_result.json"),
}
output = HERE / "terminal_verification.json"
rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
if output.exists():
    assert output.read_text() == rendered
else:
    with output.open("x") as stream:
        stream.write(rendered)
print(result["status"], labelled_choices, flush=True)
