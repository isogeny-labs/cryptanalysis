"""Reduce the joint resultant by the two exact source-pair quadratics."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
cfg = json.loads((HERE / "reduction_protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_N41_SOURCE_QUADRATIC_REDUCTION"
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
for item in cfg["sources"].values():
    assert sha(item["path"]) == item["sha256"]
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("symbolic reduction cap")))
signal.alarm(cfg["wall_cap_seconds"])
start = time.monotonic()
B = PolynomialRing(GF(2), "r")
r = B.gen()
F = GF(2**41, name="r", modulus=r**41 + r**3 + 1)
dec = F.from_integer
enc = lambda value: sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))
S = PolynomialRing(F, names=("u", "v", "p", "q", "z"), order="lex")
u, v, p, q, z = S.gens()
fixture = json.loads(Path(cfg["sources"]["fixture"]["path"]).read_text())
states = json.loads(Path(cfg["sources"]["states"]["path"]).read_text())
panel = json.loads(Path(cfg["sources"]["panel"]["path"]).read_text())
join = json.loads(Path(cfg["sources"]["join_rows"]["path"]).read_text())
seed = dec(states["seed"] << 1)


def halftrace(value):
    out = F.zero()
    for _ in range(21):
        out += value
        value = value**4
    return out


h0 = halftrace(seed)**2
h3 = h0**(2**12)
h4 = h0**(2**24)
c3, c4 = F.one() + h3, F.one() + h4
assert c3 and c4
t = dec(fixture["public_reciprocal"])
uv = u*v
zt = z*t
A, C = 1 + uv**2, (u+v)**2
D, G = 1 + zt**2, (z+t)**2
joint = (A*G+C*D)**2 + (A*zt+uv*D)*(uv*G+C*zt)
pair3 = u**2 + (p/c3)*u + h3/c3
pair4 = v**2 + (q/c4)*v + h4/c4
gb = S.ideal([pair3,pair4]).groebner_basis()
remainder = joint.reduce(gb)
assert remainder.degree(u) <= 1 and remainder.degree(v) <= 1
assert joint.reduce(gb) == remainder
terms = [(list(exp), enc(coeff)) for exp, coeff in remainder.dict().items()]
terms.sort()
rows = []
for row, reference in zip(panel, join["rows"]):
    assert row["state_ids"] == reference["state_ids"]
    state3 = states["states"][3][row["state_ids"][3]]
    state4 = states["states"][4][row["state_ids"][4]]
    pval = (dec(state3["masks"][0] << 1) * dec(state3["masks"][1] << 1))**(2**12)
    qval = (dec(state4["masks"][0] << 1) * dec(state4["masks"][1] << 1))**(2**24)
    vals = (dec(reference["pair3_reciprocal"]), dec(reference["pair4_reciprocal"]),
            pval, qval, dec(row["z"]))
    assert pair3(*vals) == pair4(*vals) == 0
    original = joint(*vals)
    reduced = remainder(*vals)
    assert original == reduced
    assert (reduced == 0) == (row["kind"] == "positive")
    rows.append({"kind": row["kind"], "control_index": row.get("control_index"),
                 "original": enc(original), "reduced": enc(reduced)})
signal.alarm(0)
result = {"status": "PASS_N41_SOURCE_QUADRATIC_REDUCTION", "candidate_id": None,
          "curve_id": cfg["curve_id"], "field_degree": 41,
          "source_constants": {"h3": enc(h3), "c3": enc(c3), "h4": enc(h4), "c4": enc(c4),
                               "target_reciprocal": enc(t)},
          "original_terms": len(joint.dict()), "reduced_terms": len(terms),
          "reduced_total_degree": int(remainder.total_degree()),
          "reduced_degree_by_variable": {str(name): int(remainder.degree(var)) for name,var in
                                         zip(("u","v","p","q","z"),(u,v,p,q,z))},
          "remainder_terms": terms, "rows": rows,
          "wall_seconds": time.monotonic() - start,
          "peak_self_rss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "protocol_sha256": sha(HERE / "reduction_protocol.json"),
          "script_sha256": sha(__file__)}
(HERE / "reduction_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps({k: result[k] for k in ("status","original_terms","reduced_terms",
                                        "reduced_total_degree","reduced_degree_by_variable",
                                        "wall_seconds","peak_self_rss_raw")}, sort_keys=True))
