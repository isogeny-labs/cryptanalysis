"""Exact left-code ANF of the right-subspace eliminant on frozen N41 rows."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg = json.loads((HERE / "protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_N41_NORM_ANF"
for label, source in cfg["sources"].items():
    assert sha(source["path"]) == source["sha256"], label

lines = Path(cfg["sources"]["resultant_input"]["path"]).read_text().splitlines()
assert lines[0] == "FREECODE 25 281 13"
valid = {}
for line in lines[1:282]:
    tag, code, p, q = line.split()
    assert tag == "P"
    valid[int(code)] = (int(p), int(q))
terms = {index: [] for index in cfg["target_indexes"]}
for line in lines[282:]:
    words = line.split()
    if words[0] == "C" and int(words[1]) in terms:
        terms[int(words[1])].append((int(words[2]), int(words[3]), int(words[4])))
assert all(len(row) == 13 for row in terms.values())

R = PolynomialRing(GF(2), "u")
u = R.gen()
F = GF(2**41, name="u", modulus=u**41 + u**3 + 1)
S = PolynomialRing(F, "z")
z = S.gen()
enc = lambda value: sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))
dec = lambda value: F.from_integer(value)
bits = cfg["free_bit_positions"]
assert bits == [0, 1, 2, 3, 4, 6, 7, 8, 9, 10]


def source_product(code, rotation):
    a = sum((dec(1 << (bit + 1)) for j, bit in enumerate(bits) if code >> j & 1), F.zero())
    seed = dec(112)
    p = a * a + seed * a
    for _ in range(rotation):
        p *= p
    return p


for code, (p, q) in valid.items():
    assert enc(source_product(code, 12)) == p
    assert enc(source_product(code, 24)) == q


def linearized_eval(coeffs, value):
    out = F.zero()
    for coefficient in coeffs:
        out += coefficient * value
        value *= value
    return out


started = time.monotonic()
qbasis = [source_product(1 << j, 24) for j in range(len(bits))]
coeffs = [F.one()]
for basis in qbasis:
    w = linearized_eval(coeffs, basis)
    assert w
    next_coeffs = [w * coeffs[0]]
    for j in range(1, len(coeffs)):
        next_coeffs.append(coeffs[j-1] * coeffs[j-1] + w * coeffs[j])
    next_coeffs.append(coeffs[-1] * coeffs[-1])
    coeffs = next_coeffs
assert len(coeffs) == 11
assert all(linearized_eval(coeffs, basis) == 0 for basis in qbasis)
prepared = time.monotonic()

rows = []
status = "COMPLETE_N41_NORM_ANF"
for target_index in cfg["target_indexes"]:
    values = []
    zeros = []
    curve_terms = [(i, j, dec(c)) for i, j, c in terms[target_index]]
    row_started = time.monotonic()
    for code in range(1 << len(bits)):
        if time.monotonic() - started >= cfg["wall_cap_seconds"]:
            status = "WALL_CAP_PARTIAL_NORM_ANF"
            break
        p = source_product(code, 12)
        powers = [F.one(), p, p*p, p*p*p, p*p*p*p]
        h = S.zero()
        for i, j, c in curve_terms:
            h += c * powers[i] * z**j
        if h == 0:
            norm = F.zero()
        else:
            x = z % h
            remainder = S.zero()
            for c in coeffs:
                remainder = (remainder + c*x) % h
                x = (x*x) % h
            norm = h.resultant(remainder)
            if code in cfg["gcd_check_codes"] or code in valid:
                assert (norm == 0) == (h.gcd(remainder).degree() > 0)
        values.append(enc(norm))
        if norm == 0:
            zeros.append(code)
    if status != "COMPLETE_N41_NORM_ANF":
        rows.append({"target_index": target_index, "status": status, "codes_checked": len(values),
                     "zero_codes": zeros, "wall_seconds": time.monotonic()-row_started})
        break
    anf = values[:]
    for j in range(len(bits)):
        for mask in range(1 << len(bits)):
            if mask >> j & 1:
                anf[mask] ^= anf[mask ^ (1 << j)]
    reconstructed = anf[:]
    for j in range(len(bits)):
        for mask in range(1 << len(bits)):
            if mask >> j & 1:
                reconstructed[mask] ^= reconstructed[mask ^ (1 << j)]
    assert reconstructed == values
    support = [mask for mask, coefficient in enumerate(anf) if coefficient]
    row = {"target_index": target_index, "status": "COMPLETE_ROW", "codes_checked": len(values),
           "zero_codes": zeros, "valid_zero_codes": [code for code in zeros if code in valid],
           "anf_nonzero_coefficients": len(support), "anf_degree": max(mask.bit_count() for mask in support),
           "anf_degree_histogram": {str(d): sum(mask.bit_count()==d for mask in support)
                                    for d in range(len(bits)+1)},
           "anf_coefficients_sha256": hashlib.sha256(json.dumps(anf,separators=(",",":")).encode()).hexdigest(),
           "wall_seconds": time.monotonic()-row_started}
    rows.append(row)
    print(json.dumps({k: row[k] for k in ("target_index","valid_zero_codes","anf_nonzero_coefficients","anf_degree","wall_seconds")},sort_keys=True),flush=True)
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > cfg["rss_cap_bytes"]:
        status = "RSS_CAP_PARTIAL_NORM_ANF"
        break

result = {"status": status, "candidate_id": None, "rows": rows,
          "requested_rows": len(cfg["target_indexes"]), "precompute_seconds": prepared-started,
          "wall_seconds": time.monotonic()-started,
          "peak_rss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "protocol_sha256": sha(HERE / "protocol.json"), "script_sha256": sha(Path(__file__))}
(HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
print(json.dumps({k:result[k] for k in ("status","requested_rows","wall_seconds","peak_rss_raw")},sort_keys=True),flush=True)
