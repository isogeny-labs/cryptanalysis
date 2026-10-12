"""Independent checked-Sage rank of the selected quadratic feature rows."""

import hashlib
import json
from pathlib import Path

from sage.all import GF, matrix


HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "n41_output_first_inverse_20261012"
protocol = json.loads((HERE / "protocol.json").read_text())
result = json.loads((HERE / "result.json").read_text())
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
drop = trace.index(1)
coordinates = [i for i in range(41) if i != drop]
assert result["trace_pivot_removed"] == drop
assert result["coordinate_bits"] == coordinates
indices = result["independent_source_indices"]
assert len(indices) == 821 and len(set(indices)) == 821
assert all(0 <= index < 4096 for index in indices)

rows = []
for index in indices:
    value = suffix["reciprocals"][index]
    coordinates_gf2 = [(value >> bit) & 1 for bit in coordinates]
    row = [1]
    row.extend(coordinates_gf2)
    row.extend(coordinates_gf2[i] * coordinates_gf2[j]
               for i in range(40) for j in range(i + 1, 40))
    assert len(row) == 821
    rows.append(row)
rank = int(matrix(GF(2), rows).rank())
audit = {
    "status": "PASS_N41_SUFFIX_DEGREE2_SAGE_RANK_AUDIT",
    "source_rows": len(rows),
    "feature_columns": 821,
    "selected_row_rank": rank,
    "source_sha256": protocol["sha256"]["suffix_values"],
}
assert rank == result["rank"] == 821
(HERE / "audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
print(audit["status"], rank)
