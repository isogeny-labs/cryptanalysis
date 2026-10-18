"""Read-only verification of frozen protocols and completed receipts."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((here / name).read_text())


for name in ("panel_protocol.json", "run_protocol.json",
             "symbolic_protocol.json", "leading_protocol.json"):
    protocol = read(name)
    for path, digest in protocol["sources"].items():
        assert sha(path) == digest, (name, path)

panel = read("panel.json")
run = read("run_result.json")
symbolic = read("symbolic_result.json")
leading = read("leading_result.json")
assert len(panel) == 33 and panel[0]["kind"] == "positive"
assert panel[0]["w"] == 2127775291906 and panel[0]["z"] == 1795929544156
assert run["status"] == "PASS_TWO_QUARTIC_SHARED_ROOT_PANEL"
assert run["final_codes_factorized"] == 71
assert run["frozen_positive_rows"] == 1
assert run["source_valid_control_rows"] == 32
assert run["control_shared_root_false_positives"] == 0
assert run["shared_root_count_histogram"] == {"0": 32, "1": 1}
assert all(row["q3_degree"] == row["q4_degree"] == 4 for row in run["row_results"])
assert symbolic["status"] == "PASS_FIXED_CODE_JOINT_POLYNOMIAL"
assert symbolic["panel_rows"] == 33 and symbolic["unique_code_pairs"] == 33
assert symbolic["degrees"] == [16] and symbolic["nonzero_coefficient_counts"] == [17]
assert symbolic["field_root_counts"] == [16]
assert leading["status"] == "PASS_ALL_CODE_PAIR_DEGREE_CENSUS"
assert leading["individual_quartic_leads_checked"] == 20164
assert leading["code_pairs_proved_degree_16"] == 5041
assert leading["code_pairs_with_degree_below_16"] == 0
for name in ("census_attempt1.json", "census_attempt2.json"):
    attempt = read(name)
    assert attempt["status"] == "BOUNDED_UNKNOWN"
    frozen = read(attempt["protocol_snapshot"])
    assert sha(here / attempt["source_snapshot"]) == frozen["sources"][str(here / "census_sage.py")]
for name in ("attempt1.json", "attempt2.json"):
    attempt = read(name)
    assert attempt["status"] == "PRODUCER_FAILURE"
    frozen = read(attempt["protocol_snapshot"])
    assert sha(here / attempt["source_snapshot"]) == frozen["sources"][str(here / "run_sage.py")]
lean = (here / "lean_check.log").read_text()
assert "sorryAx" not in lean and lean.count("depends on axioms") == 3
print(json.dumps({"status":"PASS_FROZEN_TWO_QUARTIC_RECEIPTS",
                  "panel_rows":33,"all_code_pairs_degree_16":5041,
                  "capped_full_censuses":2,"producer_failures_retained":2},sort_keys=True))
