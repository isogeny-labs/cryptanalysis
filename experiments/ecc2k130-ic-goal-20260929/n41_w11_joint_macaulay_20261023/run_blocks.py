"""Exact Macaulay rejection after restricting a first-code block."""
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
sys.path.insert(0, str(ROOT / "n41_n131_macaulay_family_gate_20261019"))
from macaulay import Field, source_basis, source_value, evaluate_resultant

sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg = json.loads((HERE / "block_protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_N41_MACAULAY_BLOCK_PANEL"
for name, item in cfg["sources"].items():
    assert sha(item["path"]) == item["sha256"], name
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError("wall cap")))
signal.alarm(cfg["wall_cap_seconds"])
start = time.monotonic()

lines = Path(cfg["sources"]["resultant_input"]["path"]).read_text().splitlines()
assert lines[0] == "FREECODE 25 281 13"
valid = {}
for line in lines[1:282]:
    _, code, p, q = line.split()
    valid[int(code)] = (int(p), int(q))
assert len(valid) == 281
terms = {0: {}, 1: {}}
for line in lines[282:]:
    parts = line.split()
    if parts[0] == "C" and int(parts[1]) in terms:
        terms[int(parts[1])][int(parts[2]), int(parts[3])] = int(parts[4])
assert len(terms[0]) == len(terms[1]) == 13
F = Field(41, 9)
bits = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10]
pb = source_basis(F, 112, bits, 12)
qb = source_basis(F, 112, bits, 24)


def multiply(a, b):
    out = {}
    for ma, va in a.items():
        for mb, vb in b.items():
            m = ma | mb
            out[m] = out.get(m, 0) ^ F.mul(va, vb)
    return {m: v for m, v in out.items() if v}


def powers(basis, offset):
    x = {1 << (i + offset): v for i, v in enumerate(basis)}
    out = [{0: 1}]
    for _ in range(4):
        out.append(multiply(out[-1], x))
    return out


P, Q = powers(pb, 0), powers(qb, 10)


def expand(target_index):
    out = {}
    for (i, j), c in terms[target_index].items():
        for m, v in multiply(P[i], Q[j]).items():
            out[m] = out.get(m, 0) ^ F.mul(c, v)
    return {m: v for m, v in out.items() if v}


def restrict(coeffs, width, base):
    low = (1 << width) - 1
    fixed_zero = ((~base) & 1023) & ~low
    out = {}
    for m, v in coeffs.items():
        if m & fixed_zero:
            continue
        new_m = (m & low) | ((m >> 10) << width)
        out[new_m] = out.get(new_m, 0) ^ v
    return {m: v for m, v in out.items() if v}


def masks(count, degree):
    return [0] + [sum(1 << j for j in combo)
                  for d in range(1, degree + 1)
                  for combo in itertools.combinations(range(count), d)]


def certificate(coeffs, vars_count, degree):
    base_degree = max(m.bit_count() for m in coeffs)
    assert degree >= base_degree
    mon = masks(vars_count, degree)
    pos = {m: i for i, m in enumerate(mon)}
    by_bit = [[m for m, v in coeffs.items() if v >> bit & 1] for bit in range(41)]
    multipliers = masks(vars_count, degree - base_degree)
    specs, rows = [], []
    for bit, terms_for_bit in enumerate(by_bit):
        if not terms_for_bit:
            continue
        for mul in multipliers:
            row = 0
            for m in terms_for_bit:
                row ^= 1 << pos[m | mul]
            specs.append((bit, mul))
            rows.append(row)
    pivots = {}
    for row_id, row in enumerate(rows):
        v, combination = row, 1 << row_id
        while v:
            key = v.bit_length() - 1
            if key not in pivots:
                pivots[key] = (v, combination)
                break
            prior, prior_comb = pivots[key]
            v ^= prior
            combination ^= prior_comb
    v, combination = 1, 0
    while v:
        key = v.bit_length() - 1
        if key not in pivots:
            break
        prior, prior_comb = pivots[key]
        v ^= prior
        combination ^= prior_comb
    selected = None
    if v == 0:
        selected, replay = [], 0
        while combination:
            low = combination & -combination
            i = low.bit_length() - 1
            selected.append(specs[i])
            replay ^= rows[i]
            combination ^= low
        assert replay == 1
    return {"reject": selected is not None,
            "certificate_rows": selected,
            "rank": len(pivots), "equations": len(rows),
            "monomials": len(mon), "base_degree": base_degree,
            "source_terms": len(coeffs)}


expanded = {target: expand(target) for target in cfg["target_indexes"]}
results = []
for width in cfg["block_widths"]:
    base = cfg["positive_code"] & ~((1 << width) - 1)
    block_codes = [p for p in valid if base <= p < base + (1 << width)]
    for target_index in cfg["target_indexes"]:
        coeffs = restrict(expanded[target_index], width, base)
        # Frozen controls include the actual positive pair and a public miss.
        expected_hits = [[p, q] for p in block_codes for q in valid
                         if evaluate_resultant(F, terms[target_index], valid[p][0], valid[q][1]) == 0]
        assert expected_hits == ([[253, 63]] if target_index == 0 else [])
        first_degree = max(m.bit_count() for m in coeffs)
        for degree in cfg["degrees"]:
            if degree < first_degree:
                continue
            t0 = time.monotonic()
            cert = certificate(coeffs, 10 + width, degree)
            cert.update({"target_index": target_index, "block_width": width,
                         "block_start": base, "source_valid_first_codes": len(block_codes),
                         "valid_hits": expected_hits, "degree": degree,
                         "certificate_seconds": time.monotonic() - t0,
                         "peak_rss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
            assert not (expected_hits and cert["reject"])
            results.append(cert)
            print(json.dumps({k: cert[k] for k in ("target_index", "block_width", "degree",
                                                   "reject", "rank", "monomials", "equations",
                                                   "certificate_seconds")}, sort_keys=True), flush=True)
            if cert["reject"]:
                break
        assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss <= cfg["rss_cap_bytes"]

signal.alarm(0)
out = {"status": "COMPLETE_N41_MACAULAY_BLOCK_PANEL", "candidate_id": None,
       "curve_id": cfg["curve_id"], "rows": results,
       "wall_seconds": time.monotonic() - start,
       "peak_rss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       "protocol_sha256": sha(HERE / "block_protocol.json"),
       "script_sha256": sha(__file__)}
(HERE / "block_result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(json.dumps({k: out[k] for k in ("status", "wall_seconds", "peak_rss_raw")}, sort_keys=True))
