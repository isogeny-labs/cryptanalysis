"""Exact target-conditioned block norm over free first-code families."""
import hashlib
import json
import resource
import sys
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CASE = sys.argv[1]
assert CASE in ("n41", "n131")
CFG = json.loads((HERE / f"protocol_{CASE}.json").read_text())
assert CFG["status"] == f"FROZEN_BEFORE_{CASE.upper()}_BLOCK_NORM"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for item in CFG["sources"].values():
    assert sha(item["path"]) == item["sha256"]


def balanced_product(items, one):
    if not items:
        return one
    level = list(items)
    while len(level) > 1:
        level = [level[i] * level[i + 1] if i + 1 < len(level) else level[i]
                 for i in range(0, len(level), 2)]
    return level[0]


def quartic(P, terms, p):
    z = P.gen()
    powers = [p**i for i in range(5)]
    return sum((c * powers[i] * z**j for i, j, c in terms), P.zero())


def linearized_coefficients(F, basis):
    coefficients = [F.one()]
    for value in basis:
        w = F.zero()
        x = value
        for c in coefficients:
            w += c * x
            x *= x
        assert w
        next_coefficients = [w * coefficients[0]]
        for j in range(1, len(coefficients)):
            next_coefficients.append(coefficients[j - 1]**2 + w * coefficients[j])
        next_coefficients.append(coefficients[-1]**2)
        coefficients = next_coefficients
    return coefficients


def linearized_remainder(P, coefficients, modulus):
    z = P.gen()
    x = z % modulus
    remainder = P.zero()
    for c in coefficients:
        remainder = (remainder + c * x) % modulus
        x = (x * x) % modulus
    return remainder


def block_gate(P, quartics, vanisher=None, linearized=None):
    if any(not h for h in quartics):
        return {"retain": True, "zero_quartic": True, "norm_degree": -1,
                "gcd_degree": -1}
    norm = balanced_product(quartics, P.one())
    remainder = vanisher % norm if vanisher is not None else linearized_remainder(P, linearized, norm)
    gcd = norm.gcd(remainder)
    return {"retain": gcd.degree() > 0, "zero_quartic": False,
            "norm_degree": int(norm.degree()), "gcd_degree": int(gcd.degree())}


def n41():
    B = PolynomialRing(GF(2), "u")
    u = B.gen()
    F = GF(2**41, name="u", modulus=u**41 + u**3 + 1)
    P = PolynomialRing(F, "z")
    dec = F.from_integer
    lines = Path(CFG["sources"]["n41_input"]["path"]).read_text().splitlines()
    assert lines[0] == "FREECODE 25 281 13"
    source = {}
    for line in lines[1:282]:
        tag, code, p, q = line.split()
        assert tag == "P"
        source[int(code)] = (dec(int(p)), dec(int(q)))
    assert len(source) == 281
    first_codes = [c for c in CFG["first_codes"] if c in source]
    assert 253 in first_codes and len(first_codes) > 0
    right = [q for _, q in source.values()]
    assert len(set(right)) == len(right)
    prepared = time.monotonic()
    vanisher = balanced_product([P.gen() + q for q in right], P.one())
    assert vanisher.degree() == 281
    prep_seconds = time.monotonic() - prepared
    rows = []
    for target_index in CFG["target_indexes"]:
        pos = 282 + target_index * 14
        fields = lines[pos].split()
        assert fields[:2] == ["T", str(target_index)]
        terms = []
        for line in lines[pos + 1:pos + 14]:
            tag, row, i, j, value = line.split()
            assert tag == "C" and int(row) == target_index
            terms.append((int(i), int(j), dec(int(value))))
        assert len(terms) == 13
        h = [quartic(P, terms, source[code][0]) for code in first_codes]
        begin = time.monotonic()
        gate = block_gate(P, h, vanisher=vanisher)
        gate_seconds = time.monotonic() - begin
        direct = [(code, other) for code in first_codes for other, q in source.items()
                  if h[first_codes.index(code)](q[1]) == 0]
        assert gate["retain"] == bool(direct)
        rows.append({"target_index": target_index, "first_codes": first_codes,
                     "direct_hits": direct, "gate": gate, "gate_seconds": gate_seconds})
    assert rows[0]["direct_hits"] and not rows[1]["direct_hits"]
    return {"rows": rows, "vanisher_degree": 281, "setup_seconds": prep_seconds}


def n131():
    prior = json.loads((HERE / "n41_result.json").read_text())
    assert prior["status"] == "PASS_N41_BLOCK_NORM_GATE"
    B = PolynomialRing(GF(2), "u")
    u = B.gen()
    F = GF(2**131, name="u", modulus=u**131 + u**13 + u**2 + u + 1)
    P = PolynomialRing(F, "z")
    dec = F.from_integer
    data = json.loads(Path(CFG["sources"]["n131_coefficients"]["path"]).read_text())
    reference = json.loads(Path(CFG["sources"]["n131_reference"]["path"]).read_text())
    assert reference["status"] == "COMPLETE_W33_GCD_AUDIT"
    assert CFG["first_codes"] == list(range(16))
    seed_mask = 898618
    bits = [i for i in range(33) if i != seed_mask.bit_length() - 1]
    assert len(bits) == 32
    seed = dec(seed_mask << 1)

    def product(code, rotation):
        a = sum((dec(1 << (bit + 1)) for j, bit in enumerate(bits)
                 if code >> j & 1), F.zero())
        return (a * a + seed * a)**(1 << rotation)

    prepared = time.monotonic()
    right_basis = [product(1 << j, 18) for j in range(32)]
    coefficients = linearized_coefficients(F, right_basis)
    assert len(coefficients) == 33
    prep_seconds = time.monotonic() - prepared
    rows = []
    for target_index in CFG["target_indexes"]:
        terms = [(i, j, dec(c)) for i, j, c in data["rows"][target_index]["terms"]]
        assert len(terms) == 13
        quartics = [quartic(P, terms, product(code, 0)) for code in CFG["first_codes"]]
        if target_index == 0:
            begin = time.monotonic()
            gate = block_gate(P, quartics, linearized=coefficients)
            block_seconds = time.monotonic() - begin
            begin = time.monotonic()
            individual = [block_gate(P, [h], linearized=coefficients) for h in quartics]
            individual_seconds = time.monotonic() - begin
        else:
            begin = time.monotonic()
            individual = [block_gate(P, [h], linearized=coefficients) for h in quartics]
            individual_seconds = time.monotonic() - begin
            begin = time.monotonic()
            gate = block_gate(P, quartics, linearized=coefficients)
            block_seconds = time.monotonic() - begin
        archived = [r for r in reference["rows"] if r["target_index"] == target_index]
        assert len(archived) == 16
        assert all(g["retain"] == (not r["reject"]) for g, r in zip(individual, archived))
        assert gate["retain"] == any(g["retain"] for g in individual)
        rows.append({"target_index": target_index, "gate": gate,
                     "individual_retained_codes": [r["p_code"] for r in archived if not r["reject"]],
                     "block_seconds": block_seconds,
                     "individual_seconds": individual_seconds,
                     "individual_gcd_degrees": [g["gcd_degree"] for g in individual]})
    assert rows[0]["individual_retained_codes"] == [3]
    assert rows[1]["individual_retained_codes"] == []
    return {"rows": rows, "linearized_coefficients": len(coefficients),
            "setup_seconds": prep_seconds}


start = time.monotonic()
data = n41() if CASE == "n41" else n131()
result = {"status": f"PASS_{CASE.upper()}_BLOCK_NORM_GATE", "candidate_id": None,
          "curve_id": CFG["curve_id"], "case": CASE, "data": data,
          "total_worker_seconds": time.monotonic() - start,
          "peak_self_rss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "protocol_sha256": sha(HERE / f"protocol_{CASE}.json"),
          "script_sha256": sha(__file__)}
(HERE / f"{CASE}_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": result["status"], "total_worker_seconds": result["total_worker_seconds"],
                  "rows": data["rows"]}, sort_keys=True), flush=True)
