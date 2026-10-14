"""Independent Sage replay of the global N41 cross-span pivot certificate."""

import hashlib
import json
from pathlib import Path

from sage.all import GF, PolynomialRing, matrix

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "audit_protocol.json").read_text())
assert protocol["status"] == "FROZEN"
for path, expected in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
source = json.loads((HERE / "result.json").read_text())

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


family_codes = sorted(set(row[1] for row in source["union_basis"]))
families = {code: [encode(value) for value in family_basis(code)] for code in family_codes}
union_words = []
for word, code in source["union_basis"]:
    basis = families[code]
    assert rank_words(basis + [word]) == len(basis)
    union_words.append(word)
assert len(union_words) == rank_words(union_words) == 40

target = decode(source["target_reciprocal"])
cross_words = []
for value, c, d, left_code, right_code in source["cross_basis"]:
    assert rank_words(families[left_code] + [c]) == len(families[left_code])
    assert rank_words(families[right_code] + [d]) == len(families[right_code])
    z = target*decode(c)*decode(d)
    assert encode(z*z+z) == value
    assert int(decode(value).trace()) == 0
    cross_words.append(value)
assert len(cross_words) == rank_words(cross_words) == 40

trace_pairing_rows = []
for i in range(41):
    row = sum(int((decode(1 << i)*decode(1 << j)).trace()) << j for j in range(41))
    trace_pairing_rows.append(row)
assert rank_words(trace_pairing_rows) == 41

result = {
    "status": "PASS_INDEPENDENT_N41_GLOBAL_CROSS_SPAN_REPLAY",
    "witness_families_rebuilt": len(family_codes),
    "union_pivots_checked": len(union_words),
    "union_rank": rank_words(union_words),
    "cross_pivots_checked": len(cross_words),
    "cross_rank": rank_words(cross_words),
    "trace_pairing_rank": rank_words(trace_pairing_rows),
    "source_sha256": {"protocol": hashlib.sha256((HERE / "audit_protocol.json").read_bytes()).hexdigest(),
                      "script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      "native_result": hashlib.sha256((HERE / "result.json").read_bytes()).hexdigest()},
}
with (HERE / "audit_result.json").open("x") as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(result["status"], result["cross_rank"])
