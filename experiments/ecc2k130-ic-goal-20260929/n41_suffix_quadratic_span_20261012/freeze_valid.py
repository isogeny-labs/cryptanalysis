"""Freeze the cross-pair column shield before the decisive rank test."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "n41_output_first_inverse_20261012"
assert not (HERE / "valid_protocol.json").exists()
paths = {
    "source": HERE / "valid_quadratic.py",
    "audit_source": HERE / "valid_audit_sage.py",
    "suffix": PRIOR / "suffix_analysis.json",
    "trace": PRIOR / "analysis.json",
    "input": HERE.parent / "n41_full_firsthalf_exact_20261011/exact_input.txt",
    "runtime": HERE / "sage_runtime_info.json",
}
protocol = {
    "status": "FROZEN_N41_COLUMN_COMPATIBLE_SUFFIX_DEGREE2_RANK",
    "candidate_id": None,
    "source_policy": "first_64_canonical_distinct_column_pairs_per_side",
    "cross_pair_shield": "all_four_source_columns_pairwise_distinct",
    "feature_law": "constant_plus_40_trace_kernel_coordinates_plus_780_squarefree_quadratics",
    "prediction": "test_linear_rank_40_and_quadratic_rank_821_after_cross_pair_shield",
    "sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest()
               for name, path in paths.items()},
}
(HERE / "valid_protocol.json").write_text(json.dumps(protocol, sort_keys=True, indent=2) + "\n")
print(protocol["status"])
