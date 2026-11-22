"""Census degree and coefficient sparsity for every allowed code pair."""
import hashlib
import json
import resource
import signal
import time
from collections import Counter
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
p = json.loads((HERE / "census_protocol.json").read_text())
for path, digest in p["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
assert not (HERE / "census_result.json").exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError("census cap")))
signal.alarm(p["wall_cap_seconds"])
start = time.monotonic()
source = json.loads(Path(p["states"]).read_text())
table = json.loads(Path(p["w_table"]).read_text())
P = PolynomialRing(GF(2), "u")
u = P.gen()
F = GF(2**41, name="u", modulus=u**41+u**3+1)
Z = PolynomialRing(F,"z")
z = Z.gen()


def dec(n):
    return F(P([(int(n) >> i) & 1 for i in range(41)]))


seed = dec(source["seed"] << 1)
h0 = sum((seed ** (1 << (2*j)) for j in range(21)), F.zero())**2
h = h0 ** (1 << 12)
c = 1 + h
bits = [i for i in range(9) if i != 5]
base = [dec((1 << bit) << 1) * dec(((1 << bit) << 1) ^ (source["seed"] << 1))
        for bit in bits]
codes = sorted({item["code"] for item in table})
roots_by_code = {code: sorted(item["w"] for item in table if item["code"] == code)
                 for code in codes}
assert len(codes) == 71 and all(len(v) == 4 for v in roots_by_code.values())


def pair_product(code):
    return sum((a ** (1 << 12) for j,a in enumerate(base) if code >> j & 1), F.zero())


def factor(w, pp):
    w = dec(w)
    b = z*w
    a = 1 + b**2
    d = z**2 + w**2
    m = a*h + c*d
    return a*d*pp**2 + b*m*pp + m**2 + c*h*b**2


hist = Counter()
leading_zero_factors = 0
pair_count = 0
for code3 in codes:
    pp = pair_product(code3)
    factors = {item["w"]: factor(item["w"], pp) for item in table}
    leading_zero_factors += sum(f.degree() < 4 for f in factors.values())
    for code4 in codes:
        poly = Z.one()
        for w in roots_by_code[code4]:
            poly *= factors[w]
        hist[(int(poly.degree()),len(poly.dict()))] += 1
        pair_count += 1

end = time.monotonic()
signal.alarm(0)
out = {"status":"PASS_FULL_CODE_PAIR_SPARSITY_CENSUS",
       "candidate_id":None,"curve_id":source["curve_id"],
       "allowed_codes":len(codes),"code_pairs":pair_count,
       "individual_quartics":len(codes)*len(table),
       "degree_below_four_factors":leading_zero_factors,
       "degree_nonzero_coefficient_histogram":
           {f"{degree},{nonzero}":count for (degree,nonzero),count in sorted(hist.items())},
       "wall_seconds":end-start,
       "self_maxrss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       "protocol_sha256":hashlib.sha256((HERE / "census_protocol.json").read_bytes()).hexdigest()}
(HERE / "census_result.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
print(json.dumps(out,sort_keys=True))
