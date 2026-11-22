"""Quadratic RR-value certificate capacity on the frozen ascending W23 panel."""
import hashlib
import importlib.util
import json
import resource
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
protocol = json.loads((HERE / "run_protocol.json").read_text())
for path, digest in protocol["sources"].items():
    assert sha(path) == digest, path
assert sha(HERE / "run.py") == protocol["runner_sha256"]
panel = json.loads((HERE / "panel.json").read_text())
assert len(panel["variants"]) == 80
prior_path = ROOT / "n41_n131_sixpair_rr_root_span_20261016/run.py"
spec = importlib.util.spec_from_file_location("frozen_rr", prior_path)
rr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rr)
field = rr.Field(131, panel["field_modulus"])

N = 131
FEATURES = N * (N + 1) // 2

def values(coefficients):
    out = list(coefficients)
    for bit in range(6):
        for sign in range(64):
            if sign & (1 << bit):
                out[sign] ^= out[sign ^ (1 << bit)]
    return out

def quadratic_row(value):
    active = [i for i in range(N) if value >> i & 1]
    row = value
    for index, i in enumerate(active):
        base = N + (i * (2 * N - i - 1)) // 2
        for j in active[index + 1:]:
            row |= 1 << (base + j - i - 1)
    assert row.bit_length() <= FEATURES
    return row

def insert(basis, row, rhs=1):
    while row:
        pivot = row.bit_length() - 1
        if pivot not in basis:
            basis[pivot] = (row, rhs)
            return True
        old_row, old_rhs = basis[pivot]
        row ^= old_row
        rhs ^= old_rhs
    return rhs == 0

def solution(basis):
    out = 0
    for pivot in sorted(basis):
        row, rhs = basis[pivot]
        if rhs ^ ((row & out).bit_count() & 1):
            out |= 1 << pivot
    return out

start = time.monotonic()
basis = {}
records = []
coeff_records = []
first_failure = None
for ordinal, variant in enumerate(panel["variants"]):
    basis_before_code = dict(basis)
    charts = []
    zero_states = []
    for root in range(2):
        points = [variant["roots"][root][0]] + panel["fixed_points"]
        coeffs = rr.coefficients([point[0] for point in points],
                                 [point[1] for point in points],
                                 panel["target"], field)
        assert coeffs is not None
        truth = values(coeffs)
        charts.append(coeffs)
        zero_states.extend([[root, sign] for sign, value in enumerate(truth) if value == 0])
        if first_failure is None:
            for sign, value in enumerate(truth):
                if not insert(basis, quadratic_row(value)):
                    first_failure = {"ordinal": ordinal, "mask": variant["mask"],
                                     "root": root, "sign": sign,
                                     "reason": "ZERO_DETERMINANT" if value == 0 else
                                               "QUADRATIC_SYSTEM_INCONSISTENT"}
                    break
    coeff_records.append({"mask": variant["mask"], "coefficients": charts,
                          "zero_states": zero_states})
    records.append({"ordinal": ordinal, "mask": variant["mask"],
                    "quadratic_rank_after_code": len(basis),
                    "zero_states": zero_states,
                    "process_maxrss_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    "elapsed_seconds": time.monotonic() - start})
    if (ordinal + 1) % 10 == 0 or first_failure is not None:
        print(json.dumps({"codes": ordinal + 1, "rank": len(basis),
                          "first_failure": first_failure,
                          "elapsed_seconds": records[-1]["elapsed_seconds"]}, sort_keys=True), flush=True)
    if first_failure is not None:
        break

assert first_failure is not None or len(records) == len(panel["variants"])
certified_prefix_count = first_failure["ordinal"] if first_failure is not None else len(records)
certificate = solution(basis_before_code if first_failure is not None else basis) if certified_prefix_count else None
if certificate is not None:
    assert all((quadratic_row(value) & certificate).bit_count() & 1
               for record in coeff_records[:certified_prefix_count] for coeffs in record["coefficients"]
               for value in values(coeffs))
(HERE / "coefficients.json").write_text(json.dumps(coeff_records, indent=2, sort_keys=True) + "\n")
result = {"status": "COMPLETE_N131_W23_QUADRATIC_CAPACITY_SCREEN",
          "candidate_id": None, "field_degree": N, "feature_count": FEATURES,
          "frozen_code_count": len(panel["variants"]), "processed_code_count": len(records),
          "records": records, "first_failure": first_failure,
          "certified_prefix_code_count": certified_prefix_count,
          "certified_prefix_certificate_hex": hex(certificate) if certificate is not None else None,
          "coefficient_sha256": sha(HERE / "coefficients.json"),
          "run_protocol_sha256": sha(HERE / "run_protocol.json"),
          "process_maxrss_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "elapsed_seconds_exploratory": time.monotonic() - start}
(HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": result["status"], "processed": len(records),
                  "first_failure": first_failure,
                  "rank": len(basis), "elapsed_seconds": result["elapsed_seconds_exploratory"]}, sort_keys=True))
