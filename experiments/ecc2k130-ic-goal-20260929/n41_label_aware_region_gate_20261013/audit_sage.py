"""Independent checked-Sage eight-family basis and exact-link replay."""

import hashlib
import json
from pathlib import Path

from sage.all import GF, PolynomialRing, matrix

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "audit_protocol.json").read_text())
assert protocol["status"] == "FROZEN"
for path, expected in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
build = json.loads((HERE / "build_result.json").read_text())
exact = json.loads((HERE / "exact_result.json").read_text())

binary = GF(2)
ring = PolynomialRing(binary, "X")
X = ring.gen()
field = GF(2**41, name="X", modulus=X**41 + X**3 + 1)


def decode(number):
    return field(ring([(number >> i) & 1 for i in range(41)]))


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def halftrace(value):
    total = field(0)
    for _ in range(21):
        total += value
        value = value**4
    return total


def family_basis(code):
    product = decode(code << 2)
    columns = []
    for i in range(41):
        c = decode(1 << i)
        columns.append((halftrace(c*c) + product*c, int((c*c).trace())))
    for i in range(6):
        s = decode(1 << (i+1))
        columns.append((halftrace(s*s), int((s*s).trace())))
    columns.append((field(1), 0))
    equations = matrix(binary, 42, 48)
    for j, (value, trace_bit) in enumerate(columns):
        word = encode(value)
        for i in range(41):
            equations[i, j] = (word >> i) & 1
        equations[41, j] = trace_bit
    result = []
    for vector in equations.right_kernel().basis():
        c = decode(sum(int(vector[i]) << i for i in range(41)))
        assert c != 0
        result.append(c)
    return result


def output_set(codes):
    result = set()
    dimensions = []
    for code in codes:
        basis = family_basis(code)
        dimensions.append(len(basis))
        for mask in range(1, 1 << len(basis)):
            value = sum((basis[i] for i in range(len(basis)) if mask >> i & 1), field(0))
            result.add(encode(value))
    return result, dimensions


left_codes = list(range(816, 820))
right_codes = list(range(176, 180))
left, left_dims = output_set(left_codes)
right, right_dims = output_set(right_codes)
assert len(left) == exact["cases"][0]["left_unique_outputs"] == 316
assert len(right) == exact["cases"][0]["right_unique_outputs"] == 252
assert left_dims == build["cases"][0]["left_family_dimensions"]
assert right_dims == build["cases"][0]["right_family_dimensions"]

audit_cases = []
for case, expected in zip(build["cases"], exact["cases"]):
    t = decode(case["target_reciprocal"])
    hits = []
    for c_word in sorted(left):
        c = decode(c_word)
        for d_word in sorted(right):
            d = decode(d_word)
            z = t*c*d
            if z*z + z + c*c + d*d + t*t == 0:
                hits.append([c_word, d_word])
    expected_hits = [[item["c"], item["d"]] for item in expected["hits"]]
    assert hits == expected_hits
    audit_cases.append({"name": case["name"], "coordinate_hits": hits,
                        "left_outputs": len(left), "right_outputs": len(right)})

result = {"status": "PASS_INDEPENDENT_EIGHT_FAMILY_SAGE_REPLAY",
          "cases": audit_cases,
          "source_sha256": {"protocol": hashlib.sha256((HERE / "audit_protocol.json").read_bytes()).hexdigest(),
                            "script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                            "exact_result": hashlib.sha256((HERE / "exact_result.json").read_bytes()).hexdigest()}}
with (HERE / "audit_result.json").open("x") as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(result["status"], [len(row["coordinate_hits"]) for row in audit_cases])
