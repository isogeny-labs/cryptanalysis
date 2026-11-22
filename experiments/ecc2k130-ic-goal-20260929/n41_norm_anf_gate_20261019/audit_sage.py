"""Independent product-vanisher and Sylvester-determinant audit of N41 norm ANF."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import GF, Matrix, PolynomialRing

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg = json.loads((HERE / "audit_protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_INDEPENDENT_N41_NORM_AUDIT"
for label, source in cfg["sources"].items():
    assert sha(source["path"]) == source["sha256"], label
producer = json.loads((HERE / "result.json").read_text())
assert producer["status"] == "COMPLETE_N41_NORM_ANF"
lines = Path(cfg["sources"]["resultant_input"]["path"]).read_text().splitlines()
assert lines[0] == "FREECODE 25 281 13"

B = PolynomialRing(GF(2), "u")
u = B.gen()
F = GF(2**41, name="u", modulus=u**41 + u**3 + 1)
P = PolynomialRing(F, "z")
z = P.gen()
dec = lambda value: F.from_integer(value)
enc = lambda value: sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))
positions = cfg["free_bit_positions"]
seed = dec(112)


def product_from_mask(mask, rotation):
    a = F.zero()
    for j in range(10):
        if mask & (1 << j):
            a += dec(1 << (positions[j]+1))
    out = a * (a + seed)
    return out ** (1 << rotation)


def balanced_product(polynomials):
    while len(polynomials) > 1:
        polynomials = [polynomials[j] * polynomials[j+1] if j+1 < len(polynomials)
                       else polynomials[j] for j in range(0,len(polynomials),2)]
    return polynomials[0]


def sylvester_determinant(f, g):
    if not f or not g:
        return F.zero()
    m, n = int(f.degree()), int(g.degree())
    if m+n == 0:
        return f[0] ** n * g[0] ** m
    rows = []
    for offset in range(n):
        row = [F.zero()] * (m+n)
        for j in range(m+1):
            row[offset+j] = f[j]
        rows.append(row)
    for offset in range(m):
        row = [F.zero()] * (m+n)
        for j in range(n+1):
            row[offset+j] = g[j]
        rows.append(row)
    return Matrix(F, rows).det()


started = time.monotonic()
right_values = [product_from_mask(code,24) for code in range(1024)]
assert len(set(right_values)) == 1024
vanisher = balanced_product([z+value for value in right_values])
assert vanisher.degree() == 1024
assert sum(1 for c in vanisher.list() if c) == 11
prepared = time.monotonic()

terms = {index: [] for index in cfg["target_indexes"]}
for line in lines[282:]:
    fields = line.split()
    if fields[0] == "C" and int(fields[1]) in terms:
        terms[int(fields[1])].append((int(fields[2]),int(fields[3]),dec(int(fields[4]))))
assert all(len(row)==13 for row in terms.values())

rows = []
status = "PASS_INDEPENDENT_N41_NORM_ANF_AUDIT"
for target_index in cfg["target_indexes"]:
    row_started = time.monotonic()
    values = []
    zero_codes = []
    for code in range(1024):
        if time.monotonic()-started >= cfg["wall_cap_seconds"]:
            status = "WALL_CAP_PARTIAL_AUDIT"
            break
        p = product_from_mask(code,12)
        powers = [F.one()]
        for _ in range(4):
            powers.append(powers[-1]*p)
        h = sum((c*powers[i]*z**j for i,j,c in terms[target_index]),P.zero())
        r = vanisher % h if h else P.zero()
        determinant = sylvester_determinant(h,r)
        values.append(enc(determinant))
        if determinant == 0:
            zero_codes.append(code)
    if status != "PASS_INDEPENDENT_N41_NORM_ANF_AUDIT":
        rows.append({"target_index":target_index,"codes_checked":len(values),"status":status})
        break
    anf = values[:]
    for j in range(10):
        stride = 1 << j
        for mask in range(1024):
            if mask & stride:
                anf[mask] ^= anf[mask ^ stride]
    support = [mask for mask,c in enumerate(anf) if c]
    digest = hashlib.sha256(json.dumps(anf,separators=(",",":")).encode()).hexdigest()
    expected = next(row for row in producer["rows"] if row["target_index"]==target_index)
    assert digest == expected["anf_coefficients_sha256"]
    assert zero_codes == expected["zero_codes"]
    assert len(support) == expected["anf_nonzero_coefficients"]
    assert max(mask.bit_count() for mask in support) == expected["anf_degree"]
    row = {"target_index":target_index,"codes_checked":1024,"zero_codes":zero_codes,
           "anf_nonzero_coefficients":len(support),"anf_degree":max(mask.bit_count() for mask in support),
           "anf_coefficients_sha256":digest,"wall_seconds":time.monotonic()-row_started}
    rows.append(row)
    print(json.dumps(row,sort_keys=True),flush=True)
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > cfg["rss_cap_bytes"]:
        status = "RSS_CAP_PARTIAL_AUDIT"
        break

result = {"status":status,"candidate_id":None,"rows":rows,"requested_rows":len(cfg["target_indexes"]),
          "precompute_seconds":prepared-started,"wall_seconds":time.monotonic()-started,
          "peak_rss_raw":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "audit_protocol_sha256":sha(HERE/"audit_protocol.json"),"auditor_sha256":sha(Path(__file__))}
(HERE/"audit_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:result[k] for k in ("status","requested_rows","wall_seconds","peak_rss_raw")},sort_keys=True),flush=True)
