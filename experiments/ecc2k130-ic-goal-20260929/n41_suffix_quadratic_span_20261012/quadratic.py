"""Find independent degree-at-most-two feature rows among exact suffix sums."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "n41_output_first_inverse_20261012"
protocol = json.loads((HERE / "protocol.json").read_text())
for name, path in {
    "source": HERE / "quadratic.py",
    "audit_source": HERE / "audit_sage.py",
    "suffix_values": PRIOR / "suffix_analysis.json",
    "suffix_protocol": PRIOR / "suffix_protocol.json",
    "trace_values": PRIOR / "analysis.json",
    "sage_runtime": HERE / "sage_runtime_info.json",
}.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == protocol["sha256"][name]

suffix = json.loads((PRIOR / "suffix_analysis.json").read_text())
trace = json.loads((PRIOR / "analysis.json").read_text())["trace_functional_coefficients"]
assert len(trace) == 41 and suffix["reciprocal_rank"] == 40
drop = trace.index(1)
keep = [i for i in range(41) if i != drop]
assert len(keep) == 40


def features(value):
    bits = [(value >> i) & 1 for i in keep]
    row = 1
    for i, bit in enumerate(bits):
        if bit:
            row |= 1 << (1 + i)
    feature = 41
    for i in range(40):
        for j in range(i + 1, 40):
            if bits[i] and bits[j]:
                row |= 1 << feature
            feature += 1
    assert feature == 821
    return row


pivots = {}
selected = []
for index, value in enumerate(suffix["reciprocals"]):
    row = features(value)
    while row:
        leading = row.bit_length() - 1
        if leading not in pivots:
            pivots[leading] = row
            selected.append(index)
            break
        row ^= pivots[leading]

result = {
    "status": "COMPLETE_N41_SUFFIX_DEGREE2_FEATURE_RANK",
    "candidate_id": None,
    "input_count": len(suffix["reciprocals"]),
    "trace_pivot_removed": drop,
    "coordinate_bits": keep,
    "feature_order": "constant_then_40_coordinates_then_lexicographic_i_lt_j_products",
    "feature_count": 821,
    "rank": len(pivots),
    "independent_source_indices": selected,
    "suffix_sha256": protocol["sha256"]["suffix_values"],
}
(HERE / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(result["status"], result["input_count"], result["rank"])
