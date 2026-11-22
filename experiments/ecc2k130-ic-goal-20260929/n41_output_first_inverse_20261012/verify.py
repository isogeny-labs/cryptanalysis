"""Independent binary-row elimination over the archived Sage reciprocal list."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n41_full_firsthalf_exact_20261011"
protocol = json.loads((HERE / "protocol.json").read_text())
result = json.loads((HERE / "analysis.json").read_text())
assert protocol["status"] == "FROZEN_N41_RESIDUAL_LINEAR_SPAN_CENSUS"
for name, path in {
    "source": HERE / "analyze_sage.py",
    "input": PARENT / "exact_input.txt",
    "exact_receipt": PARENT / "receipt.json",
    "s3_receipt": PARENT / "s3_receipt.json",
    "runtime": HERE / "sage_runtime_info.json",
}.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == protocol["sha256"][name]


def rank(rows):
    pivots = {}
    for row in rows:
        while row:
            leading = row.bit_length() - 1
            if leading not in pivots:
                pivots[leading] = row
                break
            row ^= pivots[leading]
    return len(pivots)


values = result["reciprocals"]
assert result["status"] == "COMPLETE_N41_RESIDUAL_LINEAR_SPAN_CENSUS"
assert len(values) == result["count"] == 1712 and len(set(values)) == 1712
assert all(0 < value < 1 << 41 for value in values)
modulus = (1 << 41) | (1 << 3) | 1
mask = (1 << 41) - 1


def multiply(a, b):
    product = 0
    while b:
        if b & 1:
            product ^= a
        b >>= 1
        a <<= 1
        if a & (1 << 41):
            a ^= modulus
    return product & mask


lines = (PARENT / "exact_input.txt").read_text().splitlines()
assert int(lines[0]) == 1712
for index, line in enumerate(lines[1:1713]):
    label, x, _ = line.split()
    assert label == ("positive" if index == 0 else "control_%d" % (index - 1))
    assert multiply(int(x), values[index]) == 1
assert rank(values) == result["reciprocal_linear_rank"]
assert rank([value ^ values[0] for value in values[1:]]) == result["reciprocal_affine_rank"]
trace_mask = sum(bit << i for i, bit in enumerate(result["trace_functional_coefficients"]))
assert trace_mask and all(bin(value & trace_mask).count("1") % 2 == 0 for value in values)
for bit in range(41):
    value = 1 << bit
    trace = 0
    for _ in range(41):
        trace ^= value
        value = multiply(value, value)
    assert trace in (0, 1) and trace == result["trace_functional_coefficients"][bit]
exact = json.loads((PARENT / "receipt.json").read_text())
assert sum(q["status"] == "EXACT_FOUR_ATOM_HIT" for q in exact["queries"]) == 1
assert sum(q["status"] == "COMPLETE_EXACT_NO_SUM" for q in exact["queries"]) == 1711

suffix_protocol = json.loads((HERE / "suffix_protocol.json").read_text())
assert suffix_protocol["status"] == "FROZEN_N41_EXACT_SUFFIX_RECIPROCAL_SPAN"
for name, path in {
    "source": HERE / "suffix_span_sage.py",
    "input": PARENT / "exact_input.txt",
    "exact_receipt": PARENT / "receipt.json",
    "runtime": HERE / "sage_runtime_info.json",
}.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == suffix_protocol["sha256"][name]
suffix = json.loads((HERE / "suffix_analysis.json").read_text())
assert suffix["status"] == "COMPLETE_N41_EXACT_SUFFIX_RECIPROCAL_SPAN"
assert suffix["cartesian_sums"] == 4096 and suffix["exceptional_sums"] == 0
assert suffix["valid_reciprocals"] == len(suffix["reciprocals"]) == 4096
assert suffix["reciprocal_rank"] == rank(suffix["reciprocals"]) == 40
assert all(bin(value & trace_mask).count("1") % 2 == 0 for value in suffix["reciprocals"])
assert suffix["positive_suffix_point"] == exact["queries"][0]["target"]
source_lines = lines[1713:]
cursor = 0
for side, rotation in zip(suffix["selected_pair_source_indices"], (20, 30)):
    assert source_lines[cursor] == "%d 64" % rotation
    cursor += 1
    columns = [int(row.split()[2]) for row in source_lines[cursor:cursor + 64]]
    cursor += 64
    expected = [(i, j) for i in range(64) for j in range(i + 1, 64)
                if columns[i] != columns[j]][:64]
    assert [tuple(pair) for pair in side] == expected
assert cursor == len(source_lines)
print("PASS_N41_OUTPUT_FIRST_LINEAR_SPAN_AUDIT", len(values), rank(values),
      suffix["valid_reciprocals"], suffix["reciprocal_rank"])
