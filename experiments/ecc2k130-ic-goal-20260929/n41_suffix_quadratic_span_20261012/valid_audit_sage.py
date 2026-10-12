"""Independent Sage linear and quadratic ranks on column-compatible sums."""

import hashlib
import json
from pathlib import Path

from sage.all import GF, matrix


HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "n41_output_first_inverse_20261012"
INPUT = HERE.parent / "n41_full_firsthalf_exact_20261011/exact_input.txt"
protocol = json.loads((HERE / "valid_protocol.json").read_text())
result = json.loads((HERE / "valid_result.json").read_text())
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
coordinate_bits = [i for i in range(41) if i != drop]

lines = INPUT.read_text().splitlines()
assert int(lines[0]) == 1712
offset = 1713
columns = []
for rotation in (20, 30):
    assert lines[offset] == "%d 64" % rotation
    offset += 1
    columns.append([int(line.split()[2]) for line in lines[offset:offset + 64]])
    offset += 64
assert offset == len(lines)
left, right = suffix["selected_pair_source_indices"]
valid = []
for li, (a, b) in enumerate(left):
    for ri, (c, d) in enumerate(right):
        if len({columns[0][a], columns[0][b], columns[1][c], columns[1][d]}) == 4:
            valid.append(64 * li + ri)
assert valid == result["valid_source_indices"]
assert len(valid) == result["compatible_pair_sums"]
selected = result["independent_source_indices"]
assert len(selected) == len(set(selected)) == 821
assert set(selected).issubset(set(valid))

linear_rows = []
feature_rows = []
for index in selected:
    value = suffix["reciprocals"][index]
    coords = [(value >> bit) & 1 for bit in coordinate_bits]
    linear_rows.append(coords)
    feature_rows.append([1] + coords +
                        [coords[i] * coords[j] for i in range(40)
                         for j in range(i + 1, 40)])
linear_rank = int(matrix(GF(2), linear_rows).rank())
degree2_rank = int(matrix(GF(2), feature_rows).rank())
assert linear_rank == result["linear_rank"] == 40
assert degree2_rank == result["degree2_rank"] == 821
audit = {
    "status": "PASS_N41_COLUMN_COMPATIBLE_SUFFIX_SAGE_AUDIT",
    "compatible_pair_sums": len(valid),
    "cross_pair_column_rejections": 4096 - len(valid),
    "selected_rows": len(selected),
    "linear_rank": linear_rank,
    "degree2_rank": degree2_rank,
}
(HERE / "valid_audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
print(audit["status"], len(valid), linear_rank, degree2_rank)
