"""Exact quadratic Boolean certificates for frozen N41 RR determinant values."""
import hashlib
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n41_rr_pairwise_certificate_20261017"

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

protocol = json.loads((HERE / "protocol.json").read_text())
for path, digest in protocol["sources"].items():
    assert sha(path) == digest, path
assert sha(HERE / "run.py") == protocol["runner_sha256"]
root0 = json.loads((PARENT / "result.json").read_text())["charts"]
root1 = json.loads((PARENT / "fullroot_result.json").read_text())["rows"]
assert len(root0) == len(root1) == 35
assert [a["mask"] for a in root0] == [b["mask"] for b in root1]

N = 41
FEATURES = N * (N + 1) // 2

def values(coefficients):
    """Subset zeta transform of the Boolean ANF, over GF(2^41)."""
    out = list(coefficients)
    assert len(out) == 64
    for bit in range(6):
        for mask in range(64):
            if mask & (1 << bit):
                out[mask] ^= out[mask ^ (1 << bit)]
    return out

def features(value):
    """All squarefree Boolean monomials of degree one or two, no constant."""
    active = [i for i in range(N) if value >> i & 1]
    out = 0
    for i in active:
        out |= 1 << i
    p = N
    for i in range(N):
        for j in range(i + 1, N):
            if value >> i & 1 and value >> j & 1:
                out |= 1 << p
            p += 1
    assert p == FEATURES
    return out

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
    result = 0
    for pivot in sorted(basis):
        row, rhs = basis[pivot]
        if rhs ^ ((row & result).bit_count() & 1):
            result |= 1 << pivot
    return result

codes = []
start = time.monotonic()
for a, b in zip(root0, root1):
    raw0 = values(a["coefficients"])
    raw1 = values(b["root1_coefficients"])
    raw = raw0 + raw1
    codes.append({"mask": a["mask"], "values": raw,
                  "features": [features(v) for v in raw],
                  "zero_states": [[root, sign] for root, panel in enumerate((raw0, raw1))
                                  for sign, value in enumerate(panel) if value == 0]})

rows = []
for code in codes:
    basis = {}
    ok = True
    for row in code["features"]:
        if not insert(basis, row):
            ok = False
            break
    witness = solution(basis) if ok else None
    if ok:
        assert all((row & witness).bit_count() & 1 for row in code["features"])
    rows.append({"mask": code["mask"], "zero_states": code["zero_states"],
                 "single_code_certifiable": ok, "single_code_rank": len(basis),
                 "certificate_hex": hex(witness) if witness is not None else None})

greedy = []
basis = {}
for code in codes:
    trial = dict(basis)
    if all(insert(trial, row) for row in code["features"]):
        basis = trial
        greedy.append(code["mask"])
greedy_witness = solution(basis)
selected = {code["mask"] for code in codes if code["mask"] in greedy}
assert all((row & greedy_witness).bit_count() & 1
           for code in codes if code["mask"] in selected for row in code["features"])
extension = []
for code in codes:
    if code["mask"] in selected:
        continue
    trial = dict(basis)
    possible = all(insert(trial, row) for row in code["features"])
    extension.append({"mask": code["mask"], "can_extend_greedy_certificate": possible})
assert not any(item["can_extend_greedy_certificate"] for item in extension)

prefix_buckets = []
for depth in range(9):
    groups = {}
    for code in codes:
        groups.setdefault(code["mask"] >> (8 - depth), []).append(code)
    for prefix, group in sorted(groups.items()):
        bucket_basis = {}
        possible = all(insert(bucket_basis, row)
                       for code in group for row in code["features"])
        bucket_witness = solution(bucket_basis) if possible else None
        if possible:
            assert all((row & bucket_witness).bit_count() & 1
                       for code in group for row in code["features"])
        prefix_buckets.append({"prefix_bits": depth, "prefix": prefix,
                               "code_masks": [code["mask"] for code in group],
                               "certifiable": possible, "rank_until_decision": len(bucket_basis),
                               "certificate_hex": hex(bucket_witness) if possible else None})

result = {"status": "COMPLETE_N41_QUADRATIC_RR_VALUE_SCREEN", "candidate_id": None,
          "field_degree": N, "feature_count": FEATURES, "code_count": len(codes),
          "states_per_code": 128, "rows": rows,
          "single_code_certifiable_count": sum(row["single_code_certifiable"] for row in rows),
          "greedy_certified_codes": greedy, "greedy_rank": len(basis),
          "greedy_certificate_hex": hex(greedy_witness),
          "greedy_extension_checks": extension,
          "prefix_buckets": prefix_buckets,
          "elapsed_seconds_exploratory": time.monotonic() - start,
          "protocol_sha256": sha(HERE / "protocol.json")}
(HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": result["status"],
                  "single_code_certifiable_count": result["single_code_certifiable_count"],
                  "greedy_certified_code_count": len(greedy),
                  "zero_code_count": sum(bool(row["zero_states"]) for row in rows),
                  "elapsed_seconds": result["elapsed_seconds_exploratory"]}, sort_keys=True))
