"""Check both frozen feature-rank protocols and Sage audits."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "n41_output_first_inverse_20261012"
INPUT = HERE.parent / "n41_full_firsthalf_exact_20261011/exact_input.txt"
specs = [
    ("protocol.json", {
        "source": HERE / "quadratic.py",
        "audit_source": HERE / "audit_sage.py",
        "suffix_values": PRIOR / "suffix_analysis.json",
        "suffix_protocol": PRIOR / "suffix_protocol.json",
        "trace_values": PRIOR / "analysis.json",
        "sage_runtime": HERE / "sage_runtime_info.json",
    }),
    ("valid_protocol.json", {
        "source": HERE / "valid_quadratic.py",
        "audit_source": HERE / "valid_audit_sage.py",
        "suffix": PRIOR / "suffix_analysis.json",
        "trace": PRIOR / "analysis.json",
        "input": INPUT,
        "runtime": HERE / "sage_runtime_info.json",
    }),
]
for name, paths in specs:
    protocol = json.loads((HERE / name).read_text())
    assert protocol["status"].startswith("FROZEN_N41_")
    for key, path in paths.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == protocol["sha256"][key]

result = json.loads((HERE / "result.json").read_text())
audit = json.loads((HERE / "audit.json").read_text())
valid = json.loads((HERE / "valid_result.json").read_text())
valid_audit = json.loads((HERE / "valid_audit.json").read_text())
assert result["status"] == "COMPLETE_N41_SUFFIX_DEGREE2_FEATURE_RANK"
assert audit["status"] == "PASS_N41_SUFFIX_DEGREE2_SAGE_RANK_AUDIT"
assert result["input_count"] == 4096 and result["feature_count"] == result["rank"] == 821
assert audit["selected_row_rank"] == 821 and audit["source_rows"] == 821
assert valid["status"] == "COMPLETE_N41_COLUMN_COMPATIBLE_SUFFIX_DEGREE2_RANK"
assert valid_audit["status"] == "PASS_N41_COLUMN_COMPATIBLE_SUFFIX_SAGE_AUDIT"
assert valid["all_pair_sums"] == 4096
assert valid["cross_pair_column_rejections"] == valid_audit["cross_pair_column_rejections"] == 552
assert valid["compatible_pair_sums"] == valid_audit["compatible_pair_sums"] == 3544
assert valid["linear_rank"] == valid_audit["linear_rank"] == 40
assert valid["degree2_feature_count"] == valid["degree2_rank"] == valid_audit["degree2_rank"] == 821
assert set(valid["independent_source_indices"]).issubset(set(valid["valid_source_indices"]))
print("PASS_N41_COLUMN_COMPATIBLE_QUADRATIC_RECEIPTS", 3544, 40, 821)
