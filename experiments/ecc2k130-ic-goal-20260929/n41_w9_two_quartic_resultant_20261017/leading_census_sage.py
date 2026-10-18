"""Check the exact degree-16 condition for every allowed code pair."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
p = json.loads((HERE / "leading_protocol.json").read_text())
for path, digest in p["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
assert not (HERE / "leading_result.json").exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError("leading census cap")))
signal.alarm(p["wall_cap_seconds"])
start = time.monotonic()
source = json.loads(Path(p["states"]).read_text())
table = json.loads(Path(p["w_table"]).read_text())
P = PolynomialRing(GF(2), "u")
u = P.gen()
F = GF(2**41, name="u", modulus=u**41+u**3+1)


def dec(n):
    return F(P([(int(n) >> i) & 1 for i in range(41)]))


seed_int = source["seed"] << 1
seed = dec(seed_int)
h0 = sum((seed ** (1 << (2*j)) for j in range(21)), F.zero())**2
h = h0 ** (1 << 12)
c = 1+h
bits = [i for i in range(9) if i != 5]
base = [dec((1 << bit) << 1)*dec(((1 << bit) << 1)^seed_int)
        for bit in bits]
codes = sorted({item["code"] for item in table})
assert len(codes) == 71 and len(table) == 284
w_values = {item["w"]:dec(item["w"]) for item in table}


def pair_product(code):
    return sum((a ** (1 << 12) for j,a in enumerate(base)
                if code >> j & 1), F.zero())


zero_factors = []
zero_pairs = 0
for code3 in codes:
    pp = pair_product(code3)
    for item in table:
        w = w_values[item["w"]]
        # [z^4] R3(z,w,p) = (w*p + h*w^2 + c)^2.
        lead_sqrt = w*pp + h*w**2 + c
        if lead_sqrt == 0:
            zero_factors.append([code3,item["code"],item["w"]])
    bad_final_codes = {row[1] for row in zero_factors if row[0] == code3}
    zero_pairs += len(bad_final_codes)

end = time.monotonic()
signal.alarm(0)
out = {"status":"PASS_ALL_CODE_PAIR_DEGREE_CENSUS",
       "candidate_id":None,"curve_id":source["curve_id"],
       "allowed_code_pairs":len(codes)**2,
       "individual_quartic_leads_checked":len(codes)*len(table),
       "zero_leading_factors":zero_factors,
       "code_pairs_with_degree_below_16":zero_pairs,
       "code_pairs_proved_degree_16":len(codes)**2-zero_pairs,
       "wall_seconds":end-start,
       "self_maxrss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       "protocol_sha256":hashlib.sha256((HERE / "leading_protocol.json").read_bytes()).hexdigest()}
(HERE / "leading_result.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
print(json.dumps(out,sort_keys=True))
