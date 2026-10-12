"""Rank degree-two features after the exact cross-pair column shield."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "n41_output_first_inverse_20261012"
INPUT = HERE.parent / "n41_full_firsthalf_exact_20261011/exact_input.txt"
protocol = json.loads((HERE / "valid_protocol.json").read_text())
for name, path in {
    "source": HERE / "valid_quadratic.py",
    "audit_source": HERE / "valid_audit_sage.py",
    "suffix": PRIOR / "suffix_analysis.json",
    "trace": PRIOR / "analysis.json",
    "input": INPUT,
    "runtime": HERE / "sage_runtime_info.json",
}.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == protocol["sha256"][name]

suffix = json.loads((PRIOR / "suffix_analysis.json").read_text())
trace = json.loads((PRIOR / "analysis.json").read_text())["trace_functional_coefficients"]
drop = trace.index(1)
keep = [bit for bit in range(41) if bit != drop]
lines = INPUT.read_text().splitlines()
cursor = 1713
columns = []
for rotation in (20, 30):
    assert lines[cursor] == "%d 64" % rotation
    cursor += 1
    columns.append([int(row.split()[2]) for row in lines[cursor:cursor + 64]])
    cursor += 64
assert cursor == len(lines)


def features(value):
    bits = [(value >> bit) & 1 for bit in keep]
    row = 1
    for i, bit in enumerate(bits):
        if bit:
            row |= 1 << (i + 1)
    feature = 41
    for i in range(40):
        for j in range(i + 1, 40):
            if bits[i] and bits[j]:
                row |= 1 << feature
            feature += 1
    assert feature == 821
    return row


valid_indices = []
pivots_linear = {}
pivots_degree2 = {}
independent_indices = []
left_pairs, right_pairs = suffix["selected_pair_source_indices"]
for index, value in enumerate(suffix["reciprocals"]):
    a, b = left_pairs[index // 64]
    c, d = right_pairs[index % 64]
    if len({columns[0][a], columns[0][b], columns[1][c], columns[1][d]}) != 4:
        continue
    valid_indices.append(index)
    linear = value
    while linear:
        pivot = linear.bit_length() - 1
        if pivot not in pivots_linear:
            pivots_linear[pivot] = linear
            break
        linear ^= pivots_linear[pivot]
    quadratic = features(value)
    while quadratic:
        pivot = quadratic.bit_length() - 1
        if pivot not in pivots_degree2:
            pivots_degree2[pivot] = quadratic
            independent_indices.append(index)
            break
        quadratic ^= pivots_degree2[pivot]

result = {
    "status": "COMPLETE_N41_COLUMN_COMPATIBLE_SUFFIX_DEGREE2_RANK",
    "candidate_id": None,
    "all_pair_sums": 4096,
    "cross_pair_column_rejections": 4096 - len(valid_indices),
    "compatible_pair_sums": len(valid_indices),
    "linear_rank": len(pivots_linear),
    "degree2_feature_count": 821,
    "degree2_rank": len(pivots_degree2),
    "trace_pivot_removed": drop,
    "valid_source_indices": valid_indices,
    "independent_source_indices": independent_indices,
}
(HERE / "valid_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(result["status"], len(valid_indices), len(pivots_linear), len(pivots_degree2))
