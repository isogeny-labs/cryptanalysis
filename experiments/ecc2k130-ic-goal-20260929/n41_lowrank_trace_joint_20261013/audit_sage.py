"""Independent Sage replay of selected trace cuts and complete output domains."""

import hashlib
import json
import sys
from pathlib import Path

from sage.all import GF, PolynomialRing, matrix

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "audit_protocol.json").read_text())
assert protocol["status"] == "FROZEN"
for path, expected in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
cases = [json.loads(line) for line in (HERE / "cases.jsonl").read_text().splitlines()]

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
        encoded = encode(value)
        for i in range(41):
            equations[i, j] = (encoded >> i) & 1
        equations[41, j] = trace
    basis = []
    for vector in equations.right_kernel().basis():
        c = decode(sum(int(vector[i]) << i for i in range(41)))
        assert c != 0
        basis.append(c)
    assert len(basis) in (6, 7)
    return basis


def domain(basis):
    output = []
    for mask in range(1 << len(basis)):
        value = field(0)
        for i, element in enumerate(basis):
            if mask & (1 << i):
                value += element
        output.append(value)
    assert len(set(output)) == len(output)
    return output


def dual_lambda(value):
    return sum(int((value*decode(1 << i)).trace()) << i for i in range(41))


def bitrank(rows):
    basis = {}
    for row in rows:
        while row:
            pivot = row.bit_length()-1
            if pivot in basis:
                row ^= basis[pivot]
            else:
                basis[pivot] = row
                break
    return len(basis)


audited = []
for index in protocol["audited_case_indices"]:
    case = cases[index]
    left = family_basis(case["left_product"])
    right = family_basis(case["right_product"])
    assert len(left) == case["left_dimension"]
    assert len(right) == case["right_dimension"]
    target = decode(case["target"])
    cross = [[(target*u*v)**2 + target*u*v for v in right] for u in left]
    for label in ("low", "ordinary"):
        lambdas = case[f"{label}_lambdas"]
        assert bitrank(lambdas) == 12
        ranks = []
        for value in lambdas:
            lam = decode(value)
            rows = [sum(int((lam*cross[i][j]).trace()) << j
                        for j in range(len(right))) for i in range(len(left))]
            ranks.append(bitrank(rows))
        if label == "low":
            assert ranks == case["low_rank_values"]
            assert max(ranks) <= 3
    low_masks = [dual_lambda(decode(value)) for value in case["low_lambdas"]]
    ordinary_masks = [dual_lambda(decode(value)) for value in case["ordinary_lambdas"]]
    survivors = {"low": [0]*13, "ordinary": [0]*13}
    exact_hits = 0
    for c in domain(left):
        for d in domain(right):
            z = target*c*d
            s3 = z*z + z + c*c + d*d + target*target
            if c != 0 and d != 0 and s3 == 0:
                exact_hits += 1
            word = encode(s3)
            for label, masks in (("low", low_masks), ("ordinary", ordinary_masks)):
                prefix = 0
                for mask in masks:
                    if (mask & word).bit_count() & 1:
                        break
                    prefix += 1
                for k in range(prefix+1):
                    survivors[label][k] += 1
    assert exact_hits == case["exact_hits"]
    assert survivors["low"] == case["low_survivors"]
    assert survivors["ordinary"] == case["ordinary_survivors"]
    audited.append({"case": index, "left_dimension": len(left),
                    "right_dimension": len(right), "exact_hits": exact_hits,
                    "low_final_survivors": survivors["low"][12],
                    "ordinary_final_survivors": survivors["ordinary"][12],
                    "low_rank_values": case["low_rank_values"]})

result = {
    "status": "PASS_INDEPENDENT_SAGE_TRACE_PROJECTION_AUDIT",
    "audited_cases": audited,
    "source_sha256": {"protocol": hashlib.sha256((HERE / "audit_protocol.json").read_bytes()).hexdigest(),
                      "script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      "cases": hashlib.sha256((HERE / "cases.jsonl").read_bytes()).hexdigest()},
}
with (HERE / "audit_result.json").open("x") as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(result["status"], [row["case"] for row in audited])
