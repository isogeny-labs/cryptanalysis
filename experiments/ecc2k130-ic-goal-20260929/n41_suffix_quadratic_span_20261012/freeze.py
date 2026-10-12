"""Freeze sources and prior exact suffix values before the quadratic census."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "n41_output_first_inverse_20261012"
assert not (HERE / "protocol.json").exists()
paths = {
    "source": HERE / "quadratic.py",
    "audit_source": HERE / "audit_sage.py",
    "suffix_values": PRIOR / "suffix_analysis.json",
    "suffix_protocol": PRIOR / "suffix_protocol.json",
    "trace_values": PRIOR / "analysis.json",
    "sage_runtime": HERE / "sage_runtime_info.json",
}
assert json.loads(paths["sage_runtime"].read_text())["status"] == "verified"
assert json.loads(paths["suffix_values"].read_text())["reciprocal_rank"] == 40
protocol = {
    "status": "FROZEN_N41_SUFFIX_DEGREE2_FEATURE_RANK",
    "candidate_id": None,
    "input_law": "first_64_exact_right_pairs_each_rotation_all_4096_cross_sums",
    "feature_law": "constant_plus_40_trace_kernel_coordinates_plus_780_squarefree_quadratics",
    "prediction": "test_full_rank_821",
    "sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest()
               for name, path in paths.items()},
}
(HERE / "protocol.json").write_text(json.dumps(protocol, sort_keys=True, indent=2) + "\n")
print(protocol["status"])
