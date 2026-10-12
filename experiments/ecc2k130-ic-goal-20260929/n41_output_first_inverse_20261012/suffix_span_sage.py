"""Exact right-suffix outputs: test the linear image of their reciprocals."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, matrix


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n41_full_firsthalf_exact_20261011"
protocol = json.loads((HERE / "suffix_protocol.json").read_text())
for name, path in {
    "source": HERE / "suffix_span_sage.py",
    "input": PARENT / "exact_input.txt",
    "exact_receipt": PARENT / "receipt.json",
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
cursor = 1713
sources = []
for rotation in (20, 30):
    assert lines[cursor] == "%d 64" % rotation
    cursor += 1
    block = []
    for line in lines[cursor:cursor + 64]:
        x, y, column, mask, branch, sign = map(int, line.split())
        raw = curve(dec(x), dec(y))
        transported = raw + curve(raw[0]**2, raw[1]**2)
        assert branch == 0 and transported != curve(0)
        assert 1 / transported[0] == dec(mask << 1)**(2**rotation)
        block.append((transported, column))
    sources.append(block)
    cursor += 64
assert cursor == len(lines)

selected = []
for block in sources:
    pairs = []
    for i in range(len(block)):
        for j in range(i + 1, len(block)):
            if block[i][1] == block[j][1]:
                continue
            point = block[i][0] + block[j][0]
            assert point != curve(0) and point[0] != 0
            pairs.append((i, j, point))
            if len(pairs) == 64:
                break
        if len(pairs) == 64:
            break
    assert len(pairs) == 64
    selected.append(pairs)

reciprocals = []
exceptional = 0
for _, _, left in selected[0]:
    for _, _, right in selected[1]:
        point = left + right
        if point == curve(0) or point[0] == 0:
            exceptional += 1
            continue
        reciprocal = enc(1 / point[0])
        assert dec(reciprocal).trace() == 0
        reciprocals.append(reciprocal)

bits = [[(value >> i) & 1 for i in range(41)] for value in reciprocals]
rank = int(matrix(GF(2), bits).rank())
positive = json.loads((PARENT / "receipt.json").read_text())["queries"][0]
assert positive["status"] == "EXACT_FOUR_ATOM_HIT"
assert positive["left_pair_point"][0] and positive["right_pair_point"][0]
result = {
    "status": "COMPLETE_N41_EXACT_SUFFIX_RECIPROCAL_SPAN",
    "candidate_id": None,
    "source_pair_policy": "first_64_canonical_distinct_column_pairs_per_rotation_20_30",
    "source_pairs_per_side": 64,
    "cartesian_sums": 4096,
    "exceptional_sums": exceptional,
    "valid_reciprocals": len(reciprocals),
    "distinct_reciprocals": len(set(reciprocals)),
    "all_trace_zero": True,
    "reciprocal_rank": rank,
    "field_dimension": 41,
    "reciprocals": reciprocals,
    "selected_pair_source_indices": [[[a, b] for a, b, _ in side] for side in selected],
    "positive_suffix_point": positive["target"],
}
(HERE / "suffix_analysis.json").write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
print(result["status"], len(reciprocals), rank, exceptional)
