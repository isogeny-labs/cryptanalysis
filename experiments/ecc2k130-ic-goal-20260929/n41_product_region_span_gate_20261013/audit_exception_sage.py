"""Independent Sage replay of the exceptional four-family region pair."""

import hashlib
import json
from pathlib import Path

from sage.all import GF, PolynomialRing, matrix

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "exception_audit_protocol.json").read_text())
assert protocol["status"] == "FROZEN"
for path, expected in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
source = json.loads((HERE / "exception_result.json").read_text())

F2 = GF(2)
ring = PolynomialRing(F2, "x")
x = ring.gen()
field = GF(2**41, name="x", modulus=x**41+x**3+1)


def decode(value):
    return field(ring([(int(value) >> i) & 1 for i in range(41)]))


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def halftrace(value):
    result = field(0)
    for _ in range(21):
        result += value
        value = value**4
    return result


def rank_words(values):
    pivots = {}
    for value in values:
        while value:
            bit = value.bit_length()-1
            if bit in pivots:
                value ^= pivots[bit]
            else:
                pivots[bit] = value
                break
    return len(pivots)


def family_basis(code):
    product = decode(code << 2)
    columns = []
    for i in range(41):
        c = decode(1 << i)
        columns.append((halftrace(c*c)+product*c, int((c*c).trace())))
    for i in range(6):
        s = decode(1 << (i+1))
        columns.append((halftrace(s*s), int((s*s).trace())))
    columns.append((field(1), 0))
    equations = matrix(F2, 42, 48)
    for j, (value, trace) in enumerate(columns):
        code = encode(value)
        for i in range(41):
            equations[i, j] = (code >> i) & 1
        equations[41, j] = trace
    basis = []
    for vector in equations.right_kernel().basis():
        c = decode(sum(int(vector[i]) << i for i in range(41)))
        assert c != 0
        basis.append(c)
    assert len(basis) in (6, 7)
    return basis


family_bases = [family_basis(code) for code in source["product_codes"]]
pivots = {}
for basis in family_bases:
    for value in basis:
        word = encode(value)
        while word:
            bit = word.bit_length()-1
            if bit in pivots:
                word ^= pivots[bit]
            else:
                pivots[bit] = word
                break
coordinates = [decode(word) for word in pivots.values()]
assert len(coordinates) == source["output_union_rank"] == 19
target = decode(source["target_reciprocal"])
cross_words = []
for c in coordinates:
    for d in coordinates:
        z = target*c*d
        value = z*z+z
        assert int(value.trace()) == 0
        cross_words.append(encode(value))
assert rank_words(cross_words) == source["cross_rank"] == 40
assert int(target.trace()) == 0

result = {
    "status": "PASS_INDEPENDENT_FOUR_FAMILY_EXCEPTION_REPLAY",
    "product_codes": source["product_codes"],
    "output_union_rank": len(coordinates),
    "cross_span_rank": rank_words(cross_words),
    "public_target_trace": int(target.trace()),
    "source_sha256": {
        "protocol": hashlib.sha256((HERE / "exception_audit_protocol.json").read_bytes()).hexdigest(),
        "script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "native_result": hashlib.sha256((HERE / "exception_result.json").read_bytes()).hexdigest(),
    },
}
with (HERE / "exception_audit_result.json").open("x") as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(result["status"], result["cross_span_rank"])

