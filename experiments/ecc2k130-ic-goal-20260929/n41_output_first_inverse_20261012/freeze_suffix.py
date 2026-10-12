"""Freeze the exact suffix-output rank check before executing it."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n41_full_firsthalf_exact_20261011"
assert not (HERE / "suffix_protocol.json").exists()
paths = {
    "source": HERE / "suffix_span_sage.py",
    "input": PARENT / "exact_input.txt",
    "exact_receipt": PARENT / "receipt.json",
    "runtime": HERE / "sage_runtime_info.json",
}
assert json.loads(paths["runtime"].read_text())["status"] == "verified"
protocol = {
    "status": "FROZEN_N41_EXACT_SUFFIX_RECIPROCAL_SPAN",
    "candidate_id": None,
    "field": "GF(2)[t]/(t^41+t^3+1)",
    "curve": "y^2+xy=x^3+1",
    "source_pair_policy": "first_64_canonical_distinct_column_pairs_per_rotation_20_30",
    "prediction": "test_whether_4096_exact_suffix_sums_span_trace_zero_hyperplane",
    "sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest()
               for name, path in paths.items()},
}
(HERE / "suffix_protocol.json").write_text(json.dumps(protocol, sort_keys=True, indent=2) + "\n")
print(protocol["status"])
