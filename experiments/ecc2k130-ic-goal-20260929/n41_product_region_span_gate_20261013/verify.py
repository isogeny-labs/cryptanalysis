"""Read-only terminal check of frozen N41 product-region evidence."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


for name in ("protocol.json", "audit_protocol.json", "audit_run_protocol.json",
             "exception_protocol.json", "exception_audit_protocol.json",
             "exception_audit_run_protocol.json"):
    record = load(name)
    assert record["status"] == "FROZEN", name
    for path, expected in record["sources"].items():
        assert digest(path) == expected, (name, path)

for name, protocol in (("run_result.json", "protocol.json"),
                       ("audit_run_result.json", "audit_run_protocol.json"),
                       ("exception_run_result.json", "exception_protocol.json"),
                       ("exception_audit_run_result.json", "exception_audit_run_protocol.json")):
    record = load(name)
    frozen = load(protocol)
    assert record["status"] == "EXIT_0" and record["exit_code"] == 0, name
    assert not record["monitor_degraded"] and record["stop_reason"] is None, name
    assert record["wall_ns"] <= frozen["wall_cap_seconds"] * 10**9, name
    assert record["sampled_peak_combined_rss_bytes"] <= frozen["rss_cap_bytes"], name
    assert record["protocol_sha256"] == digest(HERE / protocol), name
    for path, expected in record["sha256"].items():
        assert digest(HERE / path) == expected, (name, path)

native = load("result.json")
audit = load("audit_result.json")
exception = load("exception_result.json")
exception_audit = load("exception_audit_result.json")
assert native["status"] == "COMPLETE_N41_REGION_SPAN_PANEL"
assert audit["status"] == "PASS_INDEPENDENT_N41_REGION_RANK_CENSUS"
assert exception["status"] == "PASS_EXCEPTIONAL_FOUR_FAMILY_REGION"
assert exception_audit["status"] == "PASS_INDEPENDENT_FOUR_FAMILY_EXCEPTION_REPLAY"
assert audit["families_rebuilt"] == 2048
assert audit["public_target_trace"] == exception_audit["public_target_trace"] == 0
assert native["public_target_reciprocal"] == exception["target_reciprocal"]
assert len(native["levels"]) == len(audit["levels"]) == 12

for level, replay in zip(native["levels"], audit["levels"]):
    f = level["free_product_bits"]
    assert f == replay["free_product_bits"]
    assert level["families_per_region"] == replay["families_per_region"] == 1 << f
    assert level["region_count"] == replay["region_count"] == 2048 >> f
    assert level["union_rank_histogram"] == replay["rank_histogram"]
    assert sum(level["union_rank_histogram"].values()) == level["region_count"]
    assert min(map(int, level["union_rank_histogram"])) == level["min_union_rank"]
    assert max(map(int, level["union_rank_histogram"])) == level["max_union_rank"]
    if f < 4:
        assert level["sampled_public_region_pairs"] == 512
        assert level["constructed_positive_checked"] == 1
        assert sum(level["sampled_cross_rank_histogram"].values()) == 512

assert native["levels"][2]["union_rank_histogram"] == {"19": 1, "23": 2, "24": 487, "25": 22}
assert exception["product_codes"] == exception_audit["product_codes"] == [0, 1, 2, 3]
assert exception["output_union_rank"] == exception_audit["output_union_rank"] == 19
assert exception["cross_rank"] == exception_audit["cross_span_rank"] == 40
assert exception["target_span_consistent"]
# At f=2 only the rank-19 self-pair misses r+s>41; its cross rank is 40.
assert native["levels"][2]["region_count"] ** 2 - 1 == 262143
# At all larger regions every pair satisfies the dimension theorem.
assert all(level["min_union_rank"] * 2 > 41 for level in native["levels"][3:])

terminal = {
    "status": "PASS_FROZEN_REGION_SPAN_GATE",
    "verified_level_count": 12,
    "four_family_ordered_pairs": 512**2,
    "four_family_pairs_from_dimension_theorem": 512**2 - 1,
    "four_family_exception_cross_rank": 40,
    "minimum_family_count_with_zero_linear_span_rejection": 4,
    "public_target_trace": 0,
    "evidence_sha256": {name: digest(HERE / name) for name in
                        ("result.json", "audit_result.json", "exception_result.json",
                         "exception_audit_result.json")},
}
print(json.dumps(terminal, indent=2, sort_keys=True))
