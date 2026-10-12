"""Bind the existing public-point residual panel before its span census."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n41_full_firsthalf_exact_20261011"
paths = {
    "source": HERE / "analyze_sage.py",
    "input": PARENT / "exact_input.txt",
    "exact_receipt": PARENT / "receipt.json",
    "s3_receipt": PARENT / "s3_receipt.json",
    "runtime": HERE / "sage_runtime_info.json",
}
assert not (HERE / "protocol.json").exists()
assert json.loads(paths["runtime"].read_text())["status"] == "verified"
assert json.loads(paths["exact_receipt"].read_text())["status"] == "COMPLETE_EXACT_TRANSPORT_PAIR_PANEL"
assert json.loads(paths["s3_receipt"].read_text())["status"] == "COMPLETE_RECIPROCAL_S3_PANEL"
protocol = {
    "status": "FROZEN_N41_RESIDUAL_LINEAR_SPAN_CENSUS",
    "candidate_id": None,
    "field": "GF(2)[t]/(t^41+t^3+1)",
    "curve": "y^2+xy=x^3+1",
    "input_law": "1711_eligible_target_derived_first_pair_residuals_with_fixed_second_pair_plus_positive",
    "scope": "linear_GF2_functionals_of_reciprocal_residual_coordinate",
    "prediction": "test_whether_rank_is_40_and_only_trace_zero_linear_constraint_survives",
    "sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest()
               for name, path in paths.items()},
}
(HERE / "protocol.json").write_text(json.dumps(protocol, sort_keys=True, indent=2) + "\n")
print(protocol["status"])
