"""Read-only terminal check for three frozen trace-cut panels and audits."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def verify_sources(protocol):
    assert protocol["status"] == "FROZEN"
    for name, expected in protocol["sources"].items():
        assert sha(name) == expected, name


panels = {}
for label, protocol_name, receipt_name, cases_name, stdout_name, stderr_name in (
    ("sampled_rank3", "protocol.json", "run_result.json", "cases.jsonl", "native.stdout", "native.stderr"),
    ("row_rank1", "row_protocol.json", "row_run_result.json", "row_cases.jsonl", "row.stdout", "row.stderr"),
    ("informative_rank1", "info_protocol.json", "info_run_result.json", "info_cases.jsonl", "info.stdout", "info.stderr"),
):
    protocol = read(protocol_name)
    verify_sources(protocol)
    receipt = read(receipt_name)
    assert receipt["status"] == "EXIT_0" and receipt["exit_code"] == 0
    assert receipt["stop_reason"] is None and not receipt["monitor_degraded"]
    assert receipt["wall_ns"] < 120_000_000_000
    assert receipt["sampled_peak_combined_rss_bytes"] < 4 * 1024**3
    assert receipt["protocol_sha256"] == sha(HERE / protocol_name)
    assert receipt["sha256"][cases_name] == sha(HERE / cases_name)
    assert receipt["sha256"][stdout_name] == sha(HERE / stdout_name)
    assert receipt["sha256"][stderr_name] == sha(HERE / stderr_name)
    cases = [json.loads(line) for line in (HERE / cases_name).read_text().splitlines()]
    assert len(cases) == 32
    assert cases[0]["control"] and cases[0]["exact_hits"] == 1
    assert sum(case["exact_hits"] for case in cases) == 1
    assert all(case["target"] == 1000731834126 for case in cases[1:])
    assert all(case["ordinary_survivors"][0] == (1 << (case["left_dimension"] + case["right_dimension"])) for case in cases)
    assert all(case["ordinary_survivors"][12] >= case["exact_hits"] for case in cases)
    panels[label] = {"protocol_sha256": sha(HERE / protocol_name),
                     "receipt_sha256": sha(HERE / receipt_name),
                     "cases_sha256": sha(HERE / cases_name),
                     "wall_ns": receipt["wall_ns"],
                     "peak_sampled_combined_rss_bytes": receipt["sampled_peak_combined_rss_bytes"],
                     "cases": cases}

base = panels["sampled_rank3"]["cases"]
row = panels["row_rank1"]["cases"]
info = panels["informative_rank1"]["cases"]
for left, middle, right in zip(base, row, info):
    for key in ("case", "left_product", "right_product", "target", "exact_hits",
                "left_dimension", "right_dimension", "ordinary_survivors", "ordinary_lambdas"):
        assert left[key] == middle[key] == right[key], (key, left["case"])
    assert left["low_survivors"][12] >= left["exact_hits"]
    assert middle["row_survivors"][12] >= middle["exact_hits"]
    assert right["row_survivors"][12] >= right["exact_hits"]
    assert len(left["low_lambdas"]) == len(middle["row_lambdas"]) == len(right["row_lambdas"]) == 12
    assert max(left["low_rank_values"]) <= 3
    assert max(middle["row_ranks"]) <= 1
    assert max(right["row_ranks"]) <= 1

for audit_protocol, audit_result, audit_run, status in (
    ("audit_protocol.json", "audit_result.json", "audit_run_result.json",
     "PASS_INDEPENDENT_SAGE_TRACE_PROJECTION_AUDIT"),
    ("audit_info_protocol.json", "audit_info_result.json", "audit_info_run_result.json",
     "PASS_INDEPENDENT_SAGE_INFORMATIVE_ROW_KERNEL_AUDIT"),
):
    frozen = read(audit_protocol)
    verify_sources(frozen)
    result = read(audit_result)
    receipt = read(audit_run)
    assert result["status"] == status
    assert receipt["status"] == "EXIT_0" and receipt["exit_code"] == 0
    assert receipt["stop_reason"] is None and not receipt["monitor_degraded"]
    assert receipt["wall_ns"] < 120_000_000_000
    assert receipt["sampled_peak_combined_rss_bytes"] < 4 * 1024**3
    assert [item["case"] for item in result["audited_cases"]] == frozen["audited_case_indices"]

counts = {
    "sampled_rank3": sum(case["low_survivors"][12] == 0 for case in base),
    "deterministic_rank1": sum(case["row_survivors"][12] == 0 for case in row),
    "informative_rank1": sum(case["row_survivors"][12] == 0 for case in info),
    "ordinary": sum(case["ordinary_survivors"][12] == 0 for case in base),
}
assert counts == {"sampled_rank3": 15, "deterministic_rank1": 2,
                  "informative_rank1": 8, "ordinary": 4}
family_pairs = 1 << 70
result = {
    "status": "PASS_N41_TRACE_CUT_PANEL_AND_N131_SOURCE_BOUND",
    "candidate_id": None,
    "n41_curve_id": "EC1N41Ckb1h023d9a38bbf7",
    "panel_cases": 32,
    "constructed_positive_cases": 1,
    "exact_positive_cases": 1,
    "zero_survivor_cases_after_12_cuts": counts,
    "n131_product_family_dimension_per_slot": 35,
    "n131_literal_ordered_family_pairs": family_pairs,
    "n131_required_family_pair_rate_for_600_seconds": [family_pairs, 600],
    "n131_transfer_status": "REJECT_LITERAL_PAIRWISE_FAMILY_SCAN",
    "panel_receipts": {key: {name: value for name, value in entry.items() if name != "cases"}
                       for key, entry in panels.items()},
    "sage_audit_sha256": {name: sha(HERE / name)
                           for name in ("audit_result.json", "audit_info_result.json")},
}
output = HERE / "terminal.json"
rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
if output.exists():
    assert output.read_text() == rendered
else:
    output.write_text(rendered)
print(result["status"], counts)
