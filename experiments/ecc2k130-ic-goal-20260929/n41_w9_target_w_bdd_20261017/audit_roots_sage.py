"""Independent Sage comparison of every quartic root with target-translated states."""
import hashlib
import json
import resource
import time
from collections import Counter, defaultdict
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "audit_protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol["sources"].items():
    assert sha(path) == expected, path
assert not (HERE / "audit_result.json").exists()
start = time.monotonic()
build_protocol = json.loads((HERE / "build_protocol.json").read_text())
build = json.loads((HERE / "build_result.json").read_text())
source = json.loads(Path(build_protocol["states"]).read_text())
fixture = json.loads(Path(build_protocol["fixture"]).read_text())
wires = json.loads(Path(build_protocol["wires"]).read_text())
table = json.loads((HERE / "w_table.json").read_text())
assert build["table_sha256"] == sha(HERE / "w_table.json")
assert build["formula_sha256"] == sha(HERE / "formula.xcnf")

K = PolynomialRing(GF(2), "u")
u = K.gen()
F = GF(2**41, name="u", modulus=u**41 + u**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])
Wring = PolynomialRing(F, "W")
W = Wring.gen()


def dec(number):
    return F(K([(int(number) >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(coef) << i for i, coef in enumerate(value.polynomial().list()))


seed = dec(source["seed"] << 1)
half = F(0)
term = seed
for _ in range(21):
    half += term
    term = term**4
assert half**2+half == seed
H = (half**2)**(2**24)
C = 1+H
t = dec(fixture["public_reciprocal"])
bits = [i for i in range(9) if i != 5]
basis = [(dec((1 << bit) << 1) * dec(((1 << bit) << 1) ^
          (source["seed"] << 1))) ** (2**24) for bit in bits]
Q = E(dec(fixture["public_point"][0]), dec(fixture["public_point"][1]))


def code_of_state(state):
    mask = state["masks"][0]
    return sum(((mask >> bit) & 1) << j for j, bit in enumerate(bits))


translated = []
for state_id, state in enumerate(source["states"][4]):
    x, y = state["point"]
    residual = Q - E(dec(x), dec(y))
    assert residual != E(0) and residual[0]
    translated.append((enc(1/residual[0]), code_of_state(state), state_id))
assert sorted(translated) == sorted((row["w"], row["code"], row["final_state_id"])
                                    for row in table)
assert len({row[0] for row in translated}) == 284
expected = defaultdict(set)
for w, code, _ in translated:
    expected[code].add(w)

A = 1+(t*W)**2
B = t*W
D = t**2+W**2
M = A*H+C*D
a = A*D
b = B*M
q = M**2+C*H*B**2
degrees = Counter()
root_counts = Counter()
for code in sorted(wires["allowed_code_words"]):
    product = sum((basis[j] for j in range(8) if code >> j & 1), F(0))
    polynomial = a*product**2+b*product+q
    roots = {enc(root) for root in polynomial.roots(multiplicities=False)}
    assert roots == expected[code], (code, roots, expected[code])
    degrees[int(polynomial.degree())] += 1
    root_counts[len(roots)] += 1
assert sum(k*v for k,v in root_counts.items()) == 284

audit = {"status": "PASS_ALL_CODE_QUARTIC_ROOTS_EQUAL_TARGET_TABLE",
         "candidate_id": None, "curve_id": build["curve_id"],
         "codes_checked": len(expected), "translated_states_checked": len(translated),
         "distinct_target_w": len({w for w,_,_ in translated}),
         "polynomial_degree_counts": dict(degrees),
         "roots_per_code_counts": dict(root_counts),
         "elapsed_seconds": time.monotonic()-start,
         "self_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         "protocol_sha256": sha(HERE / "audit_protocol.json")}
(HERE / "audit_result.json").write_text(json.dumps(audit,sort_keys=True,indent=2)+"\n")
print(json.dumps(audit,sort_keys=True))
