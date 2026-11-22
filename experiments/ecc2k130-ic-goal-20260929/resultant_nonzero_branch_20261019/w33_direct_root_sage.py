"""Recover the W33 second source code from an exact specialized quartic GCD."""
import hashlib
import itertools
import json
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, matrix, vector

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg = json.loads((HERE / "w33_direct_root_protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_DIRECT_ROOT"
for label, entry in cfg["sources"].items():
    assert sha(entry["path"]) == entry["sha256"], label
source = json.loads(Path(cfg["sources"]["coefficients"]["path"]).read_text())
gcd_audit = json.loads(Path(cfg["sources"]["w33_gcd_result"]["path"]).read_text())
assert gcd_audit["status"] == "COMPLETE_W33_GCD_AUDIT"
assert [r["p_code"] for r in gcd_audit["rows"] if r["target_index"] == 0 and not r["reject"]] == [3]

started = time.monotonic()
B = PolynomialRing(GF(2), "u")
u = B.gen()
F = GF(2**131, name="u", modulus=u**131+u**13+u**2+u+1)
P = PolynomialRing(F, "z")
z = P.gen()
E = EllipticCurve(F, [1, 0, 0, 0, 1])
dec = lambda value: F.from_integer(value)
enc = lambda value: sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))
seed_mask = 898618
bits = [i for i in range(33) if i != seed_mask.bit_length()-1]
assert len(bits) == 32
seed = dec(seed_mask << 1)


def product(code, rotation):
    a = sum((dec(1 << (bit+1)) for j, bit in enumerate(bits) if code >> j & 1), F.zero())
    return (a*a+seed*a)**(1 << rotation)


def linearized(coefficients, value):
    result = F.zero()
    for coefficient in coefficients:
        result += coefficient*value
        value *= value
    return result


qbasis = [product(1 << j, 18) for j in range(32)]
coefficients = [F.one()]
for basis in qbasis:
    w = linearized(coefficients, basis)
    assert w
    following = [w*coefficients[0]]
    for j in range(1, len(coefficients)):
        following.append(coefficients[j-1]*coefficients[j-1]+w*coefficients[j])
    following.append(coefficients[-1]*coefficients[-1])
    coefficients = following
assert len(coefficients) == 33
code = 3
p = product(code, 0)
terms = [(i, j, dec(c)) for i, j, c in source["rows"][0]["terms"]]
h = sum((c*p**i*z**j for i, j, c in terms), P.zero())
assert h.degree() == 4
x = z % h
remainder = P.zero()
for coefficient in coefficients:
    remainder = (remainder+coefficient*x) % h
    x = x*x % h
common = h.gcd(remainder)
assert common.degree() == 1
q = common[0]/common[1]
assert h(q) == 0 and linearized(coefficients, q) == 0
q_int = enc(q)
qbits = [enc(value) for value in qbasis]
M = matrix(GF(2), 131, 32, lambda row, col: (qbits[col] >> row) & 1)
assert M.rank() == 32
rhs = vector(GF(2), [(q_int >> row) & 1 for row in range(131)])
solution = M.solve_right(rhs)
second_code = sum(int(solution[j]) << j for j in range(32))
assert product(second_code, 18) == q


def halftrace(value):
    result = F.zero()
    term = value
    for _ in range(66):
        result += term
        term = term**4
    assert result*result+result == value
    return result


def source_options(source_code, rotation):
    mask = sum(1 << bits[j] for j in range(32) if source_code >> j & 1)
    companion = mask ^ seed_mask
    options = []
    for chosen_mask in (mask, companion):
        a = dec(chosen_mask << 1)
        assert a and a.trace() == 0 and (1/a).trace() == 0
        root = halftrace(a)
        xcoord = 1+1/root
        points = sorted(E.lift_x(xcoord, all=True), key=lambda point: enc(point[1]))
        assert len(points) == 2
        options.append(points)
    out = []
    for i, j in itertools.product(range(2), repeat=2):
        pair = options[0][i]+options[1][j]
        assert pair != E(0)
        out.append(E(pair[0]**(1 << rotation), pair[1]**(1 << rotation)))
    return out


first_options = source_options(code, 0)
second_options = source_options(second_code, 18)
target_point = source["rows"][0]["point"]
target = E(*(dec(value) for value in target_point))
matches = [[i, j] for i, j in itertools.product(range(4), repeat=2)
           if first_options[i]+second_options[j] == target]
assert matches
result = {"status": "PASS_W33_DIRECT_ROOT_AND_CURVE_REPLAY", "candidate_id": None,
          "curve_id": source["curve_id"], "first_code": code, "second_code": second_code,
          "second_product": q_int, "gcd_degree": int(common.degree()),
          "matching_branch_pairs": matches, "target_point": target_point,
          "wall_seconds": time.monotonic()-started,
          "protocol_sha256": sha(HERE/"w33_direct_root_protocol.json"),
          "script_sha256": sha(Path(__file__))}
(HERE/"w33_direct_root_result.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
print(json.dumps(result, sort_keys=True), flush=True)
