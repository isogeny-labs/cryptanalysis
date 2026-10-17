"""Random cubic sign-polynomial controls preserving seven RR shear identities."""
import hashlib
import json
import time
from functools import reduce
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
protocol = json.loads((HERE / "protocol.json").read_text())
for path, digest in protocol["sources"].items():
    assert sha(path) == digest, path
assert sha(HERE / "run.py") == protocol["runner_sha256"]

N = 131
FEATURES = N * (N + 1) // 2
QUADRATIC = [mask for mask in range(64) if mask.bit_count() == 2]
CUBIC = [mask for mask in range(64) if mask.bit_count() == 3]

def cubic_column(mask):
    return sum(1 << i for i in range(6) if not mask >> i & 1)

def rank(bits):
    basis = {}
    for value in bits:
        while value:
            pivot = value.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = value
                break
            value ^= basis[pivot]
    return len(basis)

PIVOTS = []
for mask in CUBIC:
    candidate = PIVOTS + [mask]
    if rank([cubic_column(x) for x in candidate]) > len(PIVOTS):
        PIVOTS.append(mask)
    if len(PIVOTS) == 6:
        break
assert len(PIVOTS) == 6

def random_field(seed, chart, mask):
    label = b"N131-W23-RR-SHEAR-NULL-V1|" + bytes([seed]) + chart.to_bytes(2, "big") + bytes([mask])
    return int.from_bytes(hashlib.shake_256(label).digest(17), "little") & ((1 << N) - 1)

def generate(seed, chart):
    coeff = [0] * 64
    for mask in range(64):
        if mask.bit_count() <= 3 and mask not in PIVOTS and mask != QUADRATIC[0]:
            coeff[mask] = random_field(seed, chart, mask)
    coeff[QUADRATIC[0]] = 0
    for mask in QUADRATIC[1:]:
        coeff[QUADRATIC[0]] ^= coeff[mask]
    rhs = [0] * 6
    for mask in CUBIC:
        if mask in PIVOTS:
            continue
        for i in range(6):
            if not mask >> i & 1:
                rhs[i] ^= coeff[mask]
    matrix = [[(cubic_column(mask) >> row) & 1 for mask in PIVOTS] + [rhs[row]]
              for row in range(6)]
    for column in range(6):
        pivot = next(row for row in range(column, 6) if matrix[row][column])
        matrix[column], matrix[pivot] = matrix[pivot], matrix[column]
        for row in range(6):
            if row != column and matrix[row][column]:
                for j in range(column, 7):
                    matrix[row][j] ^= matrix[column][j]
    for index, mask in enumerate(PIVOTS):
        coeff[mask] = matrix[index][6]
    assert reduce(int.__xor__, (coeff[mask] for mask in QUADRATIC), 0) == 0
    for i in range(6):
        assert reduce(int.__xor__,
            (coeff[mask] for mask in CUBIC if not mask >> i & 1), 0) == 0
    return coeff

def truth(coeff):
    out = list(coeff)
    for bit in range(6):
        for sign in range(64):
            if sign >> bit & 1:
                out[sign] ^= out[sign ^ (1 << bit)]
    return out

def feature(value):
    active = [i for i in range(N) if value >> i & 1]
    row = value
    for index, i in enumerate(active):
        base = N + (i * (2 * N - i - 1)) // 2
        for j in active[index + 1:]:
            row |= 1 << (base + j - i - 1)
    return row

def insert(basis, vector, rhs=1):
    while vector:
        pivot = vector.bit_length() - 1
        if pivot not in basis:
            basis[pivot] = (vector, rhs)
            return True
        previous, previous_rhs = basis[pivot]
        vector ^= previous
        rhs ^= previous_rhs
    return rhs == 0

controls = []
coefficient_archive = []
start = time.monotonic()
for seed in protocol["seeds"]:
    basis = {}
    charts = []
    row_index = 0
    first_failure = None
    zero_values = 0
    for code_ordinal in range(68):
        for root in range(2):
            chart = 2 * code_ordinal + root
            coeff = generate(seed, chart)
            charts.append({"chart": chart, "coefficients": coeff})
            for sign, value in enumerate(truth(coeff)):
                zero_values += value == 0
                if not insert(basis, feature(value)):
                    first_failure = {"row_index": row_index, "code_ordinal": code_ordinal,
                                     "root": root, "sign": sign,
                                     "rank_before_failure": len(basis)}
                    break
                row_index += 1
            if first_failure is not None:
                break
        if first_failure is not None:
            break
    controls.append({"seed": seed, "first_failure": first_failure,
                     "rows_inserted": row_index, "rank": len(basis),
                     "zero_values_through_stop": zero_values,
                     "charts_generated": len(charts)})
    coefficient_archive.append({"seed": seed, "charts": charts})
    print(json.dumps(controls[-1], sort_keys=True), flush=True)

(HERE / "coefficients.json").write_text(json.dumps(coefficient_archive, sort_keys=True, indent=2) + "\n")
result = {"status": "COMPLETE_N131_SHEAR_PRESERVING_RANDOM_NULL",
          "candidate_id": None, "field_degree": N, "feature_count": FEATURES,
          "cubic_pivot_masks": PIVOTS, "seeds": protocol["seeds"],
          "controls": controls,
          "coefficients_sha256": sha(HERE / "coefficients.json"),
          "protocol_sha256": sha(HERE / "protocol.json"),
          "elapsed_seconds_exploratory": time.monotonic() - start}
(HERE / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(result["status"])
