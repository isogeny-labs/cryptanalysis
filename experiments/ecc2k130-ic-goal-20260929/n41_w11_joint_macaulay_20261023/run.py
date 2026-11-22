"""Whole-two-family Boolean Macaulay certificate for frozen W11 residuals."""
import hashlib
import itertools
import json
import resource
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PREVIOUS = ROOT / "n41_n131_macaulay_family_gate_20261019"
sys.path.insert(0, str(PREVIOUS))
from macaulay import Field, source_basis, source_value, evaluate_resultant

sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg = json.loads((HERE / "protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_N41_JOINT_MACAULAY"
for name, item in cfg["sources"].items():
    assert sha(item["path"]) == item["sha256"], name
assert cfg["curve_id"] == "EC1N41Ckb1h7d5e80d3c4d0"
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError("wall cap")))
signal.alarm(cfg["wall_cap_seconds"])
start = time.monotonic()

lines = Path(cfg["sources"]["resultant_input"]["path"]).read_text().splitlines()
assert lines[0] == "FREECODE 25 281 13"
valid = {}
for line in lines[1:282]:
    tag, code, p, q = line.split()
    assert tag == "P"
    valid[int(code)] = (int(p), int(q))
assert len(valid) == 281
terms = {0: {}, 1: {}}
for line in lines[282:]:
    parts = line.split()
    if parts[0] == "C" and int(parts[1]) in terms:
        terms[int(parts[1])][int(parts[2]), int(parts[3])] = int(parts[4])
assert len(terms[0]) == len(terms[1]) == 13

F = Field(41, (1 << 3) | 1)
seed = 112
bits = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10]
p_basis = source_basis(F, seed, bits, 12)
q_basis = source_basis(F, seed, bits, 24)
for code, (p, q) in valid.items():
    assert source_value(code, p_basis) == p
    assert source_value(code, q_basis) == q


def poly_mul(a, b):
    out = {}
    for ma, va in a.items():
        for mb, vb in b.items():
            m = ma | mb
            out[m] = out.get(m, 0) ^ F.mul(va, vb)
    return {m: v for m, v in out.items() if v}


def source_poly(basis, offset):
    return {1 << (j + offset): v for j, v in enumerate(basis)}


def powers(basis, offset):
    one = {0: 1}
    result = [one]
    source = source_poly(basis, offset)
    for _ in range(4):
        result.append(poly_mul(result[-1], source))
    return result


P = powers(p_basis, 0)
Q = powers(q_basis, 10)
assert all(max((m.bit_count() for m in P[i]), default=0) <= 2 for i in range(5))
assert all(max((m.bit_count() for m in Q[i]), default=0) <= 2 for i in range(5))


def joint_coefficients(terms_for_target):
    out = {}
    for (i, j), c in terms_for_target.items():
        product = poly_mul(P[i], Q[j])
        for m, v in product.items():
            out[m] = out.get(m, 0) ^ F.mul(c, v)
    return {m: v for m, v in out.items() if v}


def evaluate_coefficients(coeffs, assignment):
    out = 0
    for m, v in coeffs.items():
        if m & assignment == m:
            out ^= v
    return out


def monomial_list(max_degree):
    return [0] + [sum(1 << i for i in combo)
                  for d in range(1, max_degree + 1)
                  for combo in itertools.combinations(range(20), d)]


def span_certificate(coeffs, degree):
    mons = monomial_list(degree)
    positions = {m: i for i, m in enumerate(mons)}
    base = [0] * 41
    for m, v in coeffs.items():
        assert m.bit_count() <= 4
        while v:
            low = v & -v
            base[low.bit_length() - 1] ^= 1 << positions[m]
            v ^= low
    multipliers = monomial_list(degree - 4)
    row_specs = []
    rows = []
    for bit, row in enumerate(base):
        if row == 0:
            continue
        terms_for_bit = [m for m in coeffs if coeffs[m] >> bit & 1]
        for multiplier in multipliers:
            transformed = 0
            for m in terms_for_bit:
                transformed ^= 1 << positions[m | multiplier]
            row_specs.append((bit, multiplier))
            rows.append(transformed)
    pivots = {}
    for row_id, row in enumerate(rows):
        v = row
        comb = 1 << row_id
        while v:
            pivot = v.bit_length() - 1
            if pivot not in pivots:
                pivots[pivot] = (v, comb)
                break
            prior, prior_comb = pivots[pivot]
            v ^= prior
            comb ^= prior_comb
    v = 1
    comb = 0
    while v:
        pivot = v.bit_length() - 1
        if pivot not in pivots:
            break
        prior, prior_comb = pivots[pivot]
        v ^= prior
        comb ^= prior_comb
    selected = None
    if v == 0:
        selected = []
        replay = 0
        while comb:
            low = comb & -comb
            idx = low.bit_length() - 1
            selected.append(row_specs[idx])
            replay ^= rows[idx]
            comb ^= low
        assert replay == 1
    return {"reject": selected is not None, "rank": len(pivots),
            "monomials": len(mons), "equations": len(rows),
            "certificate_rows": selected}


results = []
for target_index in cfg["target_indexes"]:
    t0 = time.monotonic()
    coeffs = joint_coefficients(terms[target_index])
    expansion_seconds = time.monotonic() - t0
    assert max(m.bit_count() for m in coeffs) == 4
    for pcode, qcode in cfg["expansion_check_codes"]:
        packed = pcode | (qcode << 10)
        assert evaluate_coefficients(coeffs, packed) == evaluate_resultant(
            F, terms[target_index], source_value(pcode, p_basis), source_value(qcode, q_basis))
    positive = cfg["positive_codes"]
    if target_index == 0:
        assert evaluate_coefficients(coeffs, positive[0] | (positive[1] << 10)) == 0
    for degree in cfg["degrees"]:
        d0 = time.monotonic()
        cert = span_certificate(coeffs, degree)
        cert["target_index"] = target_index
        cert["degree"] = degree
        cert["coefficient_terms"] = len(coeffs)
        cert["expansion_seconds"] = expansion_seconds
        cert["certificate_seconds"] = time.monotonic() - d0
        cert["peak_rss_raw"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        assert not (target_index == 0 and cert["reject"])
        results.append(cert)
        print(json.dumps({k: cert[k] for k in ("target_index", "degree", "reject", "rank",
                                               "monomials", "equations", "certificate_seconds")},
                         sort_keys=True), flush=True)
        if cert["reject"]:
            break
        assert cert["peak_rss_raw"] <= cfg["rss_cap_bytes"]

signal.alarm(0)
out = {"status": "COMPLETE_N41_JOINT_MACAULAY_PANEL", "candidate_id": None,
       "curve_id": cfg["curve_id"], "rows": results,
       "wall_seconds": time.monotonic() - start,
       "peak_rss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       "protocol_sha256": sha(HERE / "protocol.json"),
       "script_sha256": sha(__file__)}
(HERE / "result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(json.dumps({k: out[k] for k in ("status", "wall_seconds", "peak_rss_raw")}, sort_keys=True))
