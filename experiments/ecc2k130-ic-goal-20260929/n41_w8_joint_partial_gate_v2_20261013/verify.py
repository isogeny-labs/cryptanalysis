"""Read-only terminal check of versioned W8 joint-partial span evidence."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "n41_w8_joint_partial_gate_20261013"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


for name in ("protocol.json", "audit_protocol.json"):
    record = load(HERE / name)
    assert record["status"] == "FROZEN"
    for path, expected in record["sources"].items():
        assert digest(path) == expected, (name, path)

native = load(HERE / "result.json")
run = load(HERE / "run_result.json")
audit = load(HERE / "audit_result.json")
audit_run = load(HERE / "audit_run_result.json")
prior = load(PRIOR / "result.json")
prior_run = load(PRIOR / "run_result.json")
assert native["status"] == "COMPLETE_N41_W8_JOINT_PARTIAL_SPAN_V2"
assert prior["status"] == "COMPLETE_N41_W8_JOINT_PARTIAL_SPAN"
assert audit["status"] == "PASS_INDEPENDENT_W8_JOINT_PARTIAL_SAGE_REPLAY"
assert native["target_reciprocal"] == audit["target_reciprocal"] == 344545435656
assert native["target_index"] == 1

for record, protocol in ((run, "protocol.json"), (audit_run, "audit_protocol.json")):
    frozen = load(HERE / protocol)
    assert record["status"] == "EXIT_0" and record["exit_code"] == 0
    assert record["stop_reason"] is None and not record["monitor_degraded"]
    assert record["wall_ns"] <= frozen["wall_cap_seconds"] * 10**9
    assert record["sampled_peak_combined_rss_bytes"] <= frozen["rss_cap_bytes"]
    assert record["protocol_sha256"] == digest(HERE / protocol)
    for name, expected in record["sha256"].items():
        assert digest(HERE / name) == expected
assert prior_run["status"] == "EXIT_0" and prior_run["exit_code"] == 0

assert len(native["levels"]) == len(audit["positive_levels"]) == len(prior["levels"]) == 6
expected = [(1, 64, 10, 0), (2, 64, 1, 0), (4, 6, 6, 58),
            (8, 1, 1, 63), (16, 0, 0, 64), (32, 1, 1, 63)]
for current, independent, archived, (width, rejects, empty, full) in zip(
        native["levels"], audit["positive_levels"], prior["levels"], expected):
    assert current["states_per_slot"] == width == archived["states_per_slot"]
    assert current["sampled_regions"] == 64
    assert (current["sampled_span_rejects"], current["sampled_empty_regions"],
            current["sampled_full_cross_rank"]) == (rejects, empty, full)
    assert current["sampled_exact_hits"] == 0
    assert current["positive_exact_hits"] == independent["exact_group_hits"] == 1
    assert current["positive_left_partials"] == independent["left_count"]
    assert current["positive_right_partials"] == independent["right_count"]
    assert current["positive_left_rank"] == independent["left_rank"]
    assert current["positive_right_rank"] == independent["right_rank"]
    assert current["positive_cross_rank"] == independent["cross_rank"]
    assert current["positive_span_consistent"]
    assert current["positive_starts"] == archived["positive_starts"]
    assert current["sampled_full_cross_rank"] == archived["sampled_full_cross_rank"]
    assert current["sampled_exact_hits"] == archived["sampled_exact_hits"]
    assert current["sampled_span_rejects"] >= archived["sampled_span_rejects"]
    if width >= 4:
        assert rejects == empty and full == 64 - empty
assert audit["empty_same_edge_control_count"] == 0
assert native["levels"][2]["positive_left_rank"] == 8
assert native["levels"][2]["positive_right_rank"] == 8
assert native["levels"][2]["positive_cross_rank"] == 40

terminal = {"status": "PASS_FROZEN_W8_JOINT_PARTIAL_GATE_V2",
            "positive_group_hit_replayed_at_all_levels": True,
            "sampled_nonempty_linear_span_rejects_at_width_four_or_more": 0,
            "sampled_exact_group_hits": 0,
            "empty_control_independently_replayed": True,
            "native_status": run["status"], "sage_status": audit_run["status"],
            "evidence_sha256": {name: digest(HERE / name) for name in
                                ("result.json", "run_result.json", "audit_result.json")}}
print(json.dumps(terminal, indent=2, sort_keys=True))
