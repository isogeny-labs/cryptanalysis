"""Census of linear reciprocal constraints on frozen target-derived residuals."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, matrix


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n41_full_firsthalf_exact_20261011"
protocol = json.loads((HERE / "protocol.json").read_text())
for name, path in {
    "source": HERE / "analyze_sage.py",
    "input": PARENT / "exact_input.txt",
    "exact_receipt": PARENT / "receipt.json",
    "s3_receipt": PARENT / "s3_receipt.json",
    "runtime": HERE / "sage_runtime_info.json",
}.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == protocol["sha256"][name]

ring = PolynomialRing(GF(2), "t")
t = ring.gen()
field = GF(2**41, "t", modulus=t**41 + t**3 + 1)
curve = EllipticCurve(field, [1, 0, 0, 0, 1])


def dec(value):
    return field(ring([(int(value) >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


lines = (PARENT / "exact_input.txt").read_text().splitlines()
assert int(lines[0]) == 1712
targets = []
for line in lines[1:1713]:
    label, x, y = line.split()
    point = curve(dec(int(x)), dec(int(y)))
    assert point[0] != 0
    targets.append((label, point))
assert len(targets) == 1712 and targets[0][0] == "positive"
assert len({name for name, _ in targets}) == 1712

exact = json.loads((PARENT / "receipt.json").read_text())
s3 = json.loads((PARENT / "s3_receipt.json").read_text())
assert exact["status"] == "COMPLETE_EXACT_TRANSPORT_PAIR_PANEL"
assert s3["status"] == "COMPLETE_RECIPROCAL_S3_PANEL"
for index, (label, point) in enumerate(targets):
    expected = [enc(point[0]), enc(point[1])]
    assert exact["queries"][index]["label"] == label
    assert s3["queries"][index]["label"] == label
    assert exact["queries"][index]["target"] == expected
    assert s3["queries"][index]["target"] == expected
    assert exact["queries"][index]["status"] == s3["queries"][index]["status"]
    assert exact["queries"][index]["status"] == (
        "EXACT_FOUR_ATOM_HIT" if index == 0 else "COMPLETE_EXACT_NO_SUM"
    )

reciprocals = [enc(1 / point[0]) for _, point in targets]
assert len(set(reciprocals)) == len(reciprocals)
assert all(dec(value).trace() == 0 for value in reciprocals)
bits = [[(value >> i) & 1 for i in range(41)] for value in reciprocals]
linear_rank = int(matrix(GF(2), bits).rank())
affine_rank = int(matrix(GF(2), [
    [(value ^ reciprocals[0]) >> i & 1 for i in range(41)]
    for value in reciprocals[1:]
]).rank())
trace_vector = [int(dec(1 << i).trace()) for i in range(41)]
assert sum(trace_vector) > 0
assert all(sum(a * b for a, b in zip(row, trace_vector)) % 2 == 0 for row in bits)

result = {
    "status": "COMPLETE_N41_RESIDUAL_LINEAR_SPAN_CENSUS",
    "candidate_id": None,
    "input_law": "all_1711_eligible_first_pair_residuals_with_fixed_second_pair_plus_positive",
    "public_target": "n41_full_firsthalf_exact_20261011",
    "count": len(reciprocals),
    "positive_hits": 1,
    "control_exact_misses": 1711,
    "all_trace_zero": True,
    "reciprocal_linear_rank": linear_rank,
    "reciprocal_affine_rank": affine_rank,
    "field_dimension": 41,
    "trace_functional_coefficients": trace_vector,
    "reciprocals": reciprocals,
    "input_sha256": protocol["sha256"]["input"],
}
(HERE / "analysis.json").write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
print(result["status"], len(reciprocals), linear_rank, affine_rank)
