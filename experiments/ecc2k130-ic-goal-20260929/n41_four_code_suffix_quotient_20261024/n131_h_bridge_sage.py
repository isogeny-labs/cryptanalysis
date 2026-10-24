"""Derive the W23 first-two-pair resultant in the N131 1/x chart."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "n131_bridge_protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for source in CFG["sources"].values():
    assert sha(source["path"]) == source["sha256"]
assert not (HERE / "n131_h_bridge_result.json").exists()
fixture = json.loads(Path(CFG["sources"]["fixture"]["path"]).read_text())
assert fixture["curve_id"] == CFG["curve_id"]
started = time.monotonic()
signal.alarm(CFG["wall_cap_seconds"])
binary = PolynomialRing(GF(2), "t")
t = binary.gen()
field = GF(2**131, name="t", modulus=t**131+t**13+t**2+t+1)


def elem(value):
    return field(binary([(int(value) >> i) & 1 for i in range(131)]))


def integer(value):
    return sum(int(v) << i for i, v in enumerate(value.polynomial().list()))


seed = elem(fixture["seed_mask"] << 1)
half = field(0)
v = seed
for _ in range(66):
    half += v
    v = v**4
assert half**2+half == seed
h0 = half**2
h1 = h0**(2**fixture["rotations"][1])
c0, c1 = 1+h0, 1+h1
p0 = elem(fixture["pairs"][0]["source_product"])
p1 = elem(fixture["pairs"][1]["source_product"])**(2**fixture["rotations"][1])
z0 = elem(fixture["pairs"][0]["output_reciprocal"])
z1 = elem(fixture["pairs"][1]["output_reciprocal"])**(2**fixture["rotations"][1])
sum_z = elem(fixture["middle_reciprocals"][0])
assert c0*z0*z0+p0*z0+h0 == 0
assert c1*z1*z1+p1*z1+h1 == 0


def s3(a, b, z):
    return (a*b*z)**2+a*b*z+(a+b)**2+z**2


assert s3(z0, z1, sum_z) == 0
ring = PolynomialRing(GF(2), names=("h0", "h1", "p", "q", "z", "a", "b"))
hh0, hh1, p, q, z, a, b = ring.gens()
left = (1+hh0)*a*a+p*a+hh0
right = (1+hh1)*b*b+q*b+hh1
poly = left.resultant(right.resultant(s3(a,b,z), b), a)
terms = sorted([list(map(int, powers[:5])) for powers in poly.dict()])
assert all(powers[5:] == (0,0) for powers in poly.dict())
specialized = field(0)
for ea, eb, ep, eq, ez in terms:
    specialized += h0**ea*h1**eb*p0**ep*p1**eq*sum_z**ez
assert specialized == 0
out = {"status": "PASS_N131_W23_FIRST_TWO_RESULTANT_BRIDGE",
       "candidate_id": None, "curve_id": CFG["curve_id"],
       "field_modulus": [131, 13, 2, 1, 0],
       "chart": "standard reciprocal 1/x",
       "rotations": fixture["rotations"][:2],
       "seed_mask": fixture["seed_mask"],
       "term_count": len(terms), "terms": terms,
       "degree_z": max(term[4] for term in terms),
       "h_values": [integer(h0), integer(h1)],
       "product_values": [integer(p0), integer(p1)],
       "pair_reciprocals": [integer(z0), integer(z1)],
       "first_two_sum_reciprocal": integer(sum_z),
       "specialized_resultant_value": integer(specialized),
       "wall_seconds": time.monotonic()-started,
       "self_maxrss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       "protocol_sha256": sha(HERE / "n131_bridge_protocol.json")}
assert out["self_maxrss_raw"] < CFG["rss_cap_bytes"]
(HERE / "n131_h_bridge_result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
signal.alarm(0)
print(json.dumps({"status": out["status"], "term_count": len(terms),
                  "degree_z": out["degree_z"], "wall_seconds": out["wall_seconds"]}, sort_keys=True))
