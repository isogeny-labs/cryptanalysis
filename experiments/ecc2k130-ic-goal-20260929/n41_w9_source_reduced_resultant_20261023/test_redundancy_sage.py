"""Check whether the joint resultant is implied by existing S3 links."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
cfg = json.loads((HERE / "redundancy_protocol.json").read_text())
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert sha(__file__) == cfg["script_sha256"]
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError("wall cap")))
signal.alarm(cfg["wall_cap_seconds"])
start = time.monotonic()

S = PolynomialRing(GF(2), names=("z", "u", "v", "w", "t"), order="degrevlex")
z, u, v, w, t = S.gens()


def s3(a, b, c):
    ab = a * b
    return (1 + ab**2) * c**2 + ab * c + (a + b)**2


f = s3(z, u, w)
g = s3(w, v, t)
A = 1 + (u * v)**2
B = u * v
C = (u + v)**2
D = 1 + (z * t)**2
E = z * t
G = (z + t)**2
R = (A * G + C * D)**2 + (A * E + B * D) * (B * G + C * E)
gb = S.ideal([f, g]).groebner_basis()
remainder = R.reduce(gb)
out = {
    "status": "RESULTANT_REDUNDANCY_CHECK_COMPLETE",
    "candidate_id": None,
    "base_field": "GF(2)",
    "variable_order": list(S.variable_names()),
    "term_order": "degrevlex",
    "left_s3_terms": len(f.dict()),
    "right_s3_terms": len(g.dict()),
    "resultant_terms": len(R.dict()),
    "groebner_basis_count": len(gb),
    "groebner_basis_term_counts": [len(h.dict()) for h in gb],
    "remainder_terms": [([int(n) for n in e], int(c)) for e, c in remainder.dict().items()],
    "resultant_in_ideal": remainder == 0,
    "wall_seconds": time.monotonic() - start,
    "self_maxrss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    "protocol_sha256": sha(HERE / "redundancy_protocol.json"),
}
(HERE / "redundancy_result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(json.dumps(out, sort_keys=True))
