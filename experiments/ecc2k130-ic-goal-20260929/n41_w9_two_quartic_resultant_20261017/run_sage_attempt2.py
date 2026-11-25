"""Independently check the shared-root quartic gate on a frozen N41 panel."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "run_protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, digest in protocol["sources"].items():
    assert sha(path) == digest, path
assert not (HERE / "run_result.json").exists()


def alarm(_sig, _frame):
    raise TimeoutError("frozen two-quartic Sage cap")


signal.signal(signal.SIGALRM, alarm)
signal.alarm(protocol["wall_cap_seconds"])
start = time.monotonic()
panel = json.loads((HERE / "panel.json").read_text())
source = json.loads(Path(protocol["states"]).read_text())
fixture = json.loads(Path(protocol["fixture"]).read_text())
w_table = json.loads(Path(protocol["w_table"]).read_text())

P = PolynomialRing(GF(2), "u")
u = P.gen()
F = GF(2**41, name="u", modulus=u**41 + u**3 + 1)
W = PolynomialRing(F, "v")
v = W.gen()


def dec(n):
    return F(P([(int(n) >> i) & 1 for i in range(41)]))


def enc(a):
    return sum(int(c) << i for i, c in enumerate(a.polynomial().list()))


def frob(a, k):
    return a ** (1 << k)


def point(raw):
    return dec(raw[0]), dec(raw[1])


def add(A, B):
    if A is None:
        return B
    if B is None:
        return A
    x1, y1 = A
    x2, y2 = B
    if x1 == x2:
        if y1 + y2 == x1:
            return None
        assert A == B and x1
        slope = x1 + y1 / x1
        x3 = slope**2 + slope
        y3 = x1**2 + (slope + 1) * x3
    else:
        slope = (y1 + y2) / (x1 + x2)
        x3 = slope**2 + slope + x1 + x2
        y3 = slope * (x1 + x3) + x3 + y1
    return x3, y3


bits = [i for i in range(9) if i != 5]
seed = source["seed"] << 1
halftrace = sum((dec(seed) ** (1 << (2 * j)) for j in range(21)), F.zero())
h0 = halftrace**2
products = [dec((1 << bit) << 1) * dec(((1 << bit) << 1) ^ seed)
            for bit in bits]


def product(code, rotation):
    p = F.zero()
    for j, a in enumerate(products):
        if code >> j & 1:
            p += frob(a, rotation)
    return p


def quartic(x, p, rotation):
    h = frob(h0, rotation)
    c = 1 + h
    b = x * v
    a = 1 + b**2
    d = x**2 + v**2
    m = a * h + c * d
    return a * d * p**2 + b * m * p + m**2 + c * h * b**2


roots_by_code = {}
for item in w_table:
    roots_by_code.setdefault(item["code"], set()).add(item["w"])
assert len(roots_by_code) == 71 and all(len(x) == 4 for x in roots_by_code.values())
all_final_codes = {}
for code, frozen_roots in roots_by_code.items():
    q4 = quartic(dec(fixture["public_reciprocal"]), product(code, 24), 24)
    assert q4.degree() == 4 and q4.leading_coefficient()
    actual_roots = {enc(a) for a, multiplicity in q4.roots() if multiplicity == 1}
    assert actual_roots == frozen_roots
    all_final_codes[code] = q4
after_roots = time.monotonic()

rows = []
positive = 0
false_positive = 0
shared_root_counts = {}
for row in panel:
    z = dec(row["z"])
    q3 = quartic(z, product(row["code3"], 12), 12)
    q4 = all_final_codes[row["code4"]]
    gcd = q3.gcd(q4)
    resultant = q3.resultant(q4)
    field_roots = sorted(w for w in roots_by_code[row["code4"]] if q3(dec(w)) == 0)
    assert q3.degree() == 4 and q3.leading_coefficient()
    assert gcd.degree() == len(field_roots)
    assert (resultant == 0) == bool(field_roots)
    assert (q4(dec(row["w"])) == 0)
    assert row["w"] in roots_by_code[row["code4"]]
    first = None
    for slot, sid in enumerate(row["state_ids"][:3]):
        first = add(first, point(source["states"][slot][sid]["point"]))
    assert first is not None and first[0] and enc(1 / first[0]) == row["z"]
    total = first
    for slot, sid in enumerate(row["state_ids"][3:], start=3):
        total = add(total, point(source["states"][slot][sid]["point"]))
    full_relation = total == point(fixture["public_point"])
    if row["kind"] == "positive":
        assert full_relation and row["w"] in field_roots
        positive += 1
    else:
        assert not full_relation
        false_positive += bool(field_roots)
    shared_root_counts[str(len(field_roots))] = shared_root_counts.get(str(len(field_roots)), 0) + 1
    rows.append({"kind": row["kind"], "control_index": row.get("control_index"),
                 "code3": row["code3"], "code4": row["code4"],
                 "q3_degree": q3.degree(), "q4_degree": q4.degree(),
                 "gcd_degree": gcd.degree(), "resultant_zero": resultant == 0,
                 "shared_roots": field_roots, "full_relation": full_relation})

end = time.monotonic()
signal.alarm(0)
out = {"status": "PASS_TWO_QUARTIC_SHARED_ROOT_PANEL",
       "candidate_id": None, "curve_id": source["curve_id"],
       "final_codes_factorized": len(all_final_codes),
       "frozen_positive_rows": positive,
       "source_valid_control_rows": len(panel) - positive,
       "control_shared_root_false_positives": false_positive,
       "shared_root_count_histogram": shared_root_counts,
       "row_results": rows,
       "phase_seconds": {"quartic_root_audit": after_roots - start,
                         "panel_resultants": end - after_roots},
       "wall_seconds": end - start,
       "self_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       "protocol_sha256": sha(HERE / "run_protocol.json")}
(HERE / "run_result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(json.dumps({k: v for k, v in out.items() if k != "row_results"}, sort_keys=True))
