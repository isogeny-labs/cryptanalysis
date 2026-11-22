"""Produce an explicit odd XOR dependency for the first N131 failure."""
import hashlib
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
freeze = json.loads((HERE / "certificate_protocol.json").read_text())
for path, digest in freeze["sources"].items():
    assert sha(path) == digest, path
assert sha(HERE / "certify.py") == freeze["producer_sha256"]
records = json.loads((HERE / "coefficients.json").read_text())
result = json.loads((HERE / "result.json").read_text())
assert len(records) == result["processed_code_count"] == 68

def truth(coeffs):
    out = list(coeffs)
    for index in range(6):
        step = 1 << index
        for sign in range(64):
            if sign & step:
                out[sign] ^= out[sign ^ step]
    return out

def row(value):
    on = [i for i in range(131) if value >> i & 1]
    output = value
    for pos, i in enumerate(on):
        first = 131 + (i * (261 - i)) // 2
        for j in on[pos + 1:]:
            output |= 1 << (first + j - i - 1)
    return output

start = time.monotonic()
basis = {}
positions = []
conflict = None
for ordinal, record in enumerate(records):
    for root, coeffs in enumerate(record["coefficients"]):
        for sign, value in enumerate(truth(coeffs)):
            index = len(positions)
            positions.append([ordinal, record["mask"], root, sign])
            vector = row(value)
            combination = 1 << index
            rhs = 1
            while vector:
                pivot = (vector & -vector).bit_length() - 1
                if pivot not in basis:
                    basis[pivot] = (vector, rhs, combination)
                    break
                old_vector, old_rhs, old_combination = basis[pivot]
                vector ^= old_vector
                rhs ^= old_rhs
                combination ^= old_combination
            else:
                if rhs:
                    conflict = combination
                    break
        if conflict is not None:
            break
    if conflict is not None:
        break

assert conflict is not None
indices = [i for i in range(len(positions)) if conflict >> i & 1]
assert len(indices) & 1
assert positions[-1] == [67, 274, 1, 2]
assert len(basis) == 8642
certificate = {"status": "EXACT_ODD_XOR_CONTRADICTION",
               "result_sha256": sha(HERE / "result.json"),
               "coefficient_sha256": sha(HERE / "coefficients.json"),
               "certificate_protocol_sha256": sha(HERE / "certificate_protocol.json"),
               "first_failure_index": len(positions) - 1,
               "first_failure_position": positions[-1],
               "rank_before_failure": len(basis),
               "dependency_row_indices": indices,
               "dependency_size": len(indices),
               "elapsed_seconds_exploratory": time.monotonic() - start}
(HERE / "certificate.json").write_text(json.dumps(certificate, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": certificate["status"],
                  "first_failure_index": certificate["first_failure_index"],
                  "dependency_size": len(indices),
                  "elapsed_seconds": certificate["elapsed_seconds_exploratory"]}, sort_keys=True))
