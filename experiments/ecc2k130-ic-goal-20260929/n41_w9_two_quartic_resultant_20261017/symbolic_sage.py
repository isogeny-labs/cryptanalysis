"""Measure fixed-code degree and sparsity of the implicit joint polynomial."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
p = json.loads((HERE / "symbolic_protocol.json").read_text())
for path, digest in p["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
assert not (HERE / "symbolic_result.json").exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError("symbolic cap")))
signal.alarm(p["wall_cap_seconds"])
start = time.monotonic()
panel = json.loads((HERE / "panel.json").read_text())
source = json.loads(Path(p["states"]).read_text())
fixture = json.loads(Path(p["fixture"]).read_text())
w_table = json.loads(Path(p["w_table"]).read_text())
P = PolynomialRing(GF(2), "u")
u = P.gen()
F = GF(2**41, name="u", modulus=u**41+u**3+1)
Z = PolynomialRing(F, "z")
z = Z.gen()


def dec(n):
    return F(P([(int(n) >> i) & 1 for i in range(41)]))


seed = dec(source["seed"] << 1)
ht = sum((seed ** (1 << (2*j)) for j in range(21)), F.zero())
h0 = ht**2
bits = [i for i in range(9) if i != 5]
products = [dec((1 << bit) << 1) * dec(((1 << bit) << 1) ^ (source["seed"] << 1))
            for bit in bits]


def product(code, rotation):
    return sum((a ** (1 << rotation) for j, a in enumerate(products)
                if code >> j & 1), F.zero())


def r3_for_w(w, code3):
    h = h0 ** (1 << 12)
    c = 1 + h
    p3 = product(code3, 12)
    w = dec(w)
    b = z*w
    a = 1 + b**2
    d = z**2 + w**2
    m = a*h + c*d
    return a*d*p3**2 + b*m*p3 + m**2 + c*h*b**2


roots_by_code = {}
for item in w_table:
    roots_by_code.setdefault(item["code"], []).append(item["w"])
assert len(roots_by_code) == 71
cache = {}
rows = []
for row in panel:
    key = row["code3"], row["code4"]
    if key not in cache:
        poly = Z.one()
        for w in roots_by_code[key[1]]:
            poly *= r3_for_w(w, key[0])
        cache[key] = poly
    poly = cache[key]
    assert poly(dec(row["z"])) == 0 if row["kind"] == "positive" else poly(dec(row["z"])) != 0
    roots = poly.roots()
    rows.append({"kind": row["kind"], "codes": list(key),
                 "degree": int(poly.degree()),
                 "nonzero_coefficients": len(poly.dict()),
                 "distinct_field_roots": len(roots),
                 "root_multiplicities": sorted(int(mult) for _root,mult in roots),
                 "panel_zero": bool(poly(dec(row["z"])) == 0)})

end = time.monotonic()
signal.alarm(0)
out = {"status": "PASS_FIXED_CODE_JOINT_POLYNOMIAL",
       "candidate_id": None, "curve_id": source["curve_id"],
       "panel_rows": len(rows), "unique_code_pairs": len(cache),
       "degrees": sorted(set(r["degree"] for r in rows)),
       "nonzero_coefficient_counts": sorted(set(r["nonzero_coefficients"] for r in rows)),
       "field_root_counts": sorted(set(r["distinct_field_roots"] for r in rows)),
       "rows": rows, "wall_seconds": end-start,
       "self_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       "protocol_sha256": hashlib.sha256((HERE / "symbolic_protocol.json").read_bytes()).hexdigest()}
(HERE / "symbolic_result.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
print(json.dumps({k:v for k,v in out.items() if k != "rows"},sort_keys=True))
