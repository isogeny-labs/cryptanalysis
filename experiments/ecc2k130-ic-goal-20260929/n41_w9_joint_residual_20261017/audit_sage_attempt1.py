"""Independent Sage group replay of every joint residual support row."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
p = json.loads((HERE / "audit_protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in p["sources"].items():
    assert sha(path) == expected, path
assert not (HERE / "audit_result.json").exists()


def timeout(_signal, _frame):
    raise TimeoutError("frozen independent Sage joint-support audit cap")


signal.signal(signal.SIGALRM, timeout)
signal.alarm(p["wall_cap_seconds"])
started = time.monotonic()
producer = json.loads((HERE / "protocol.json").read_text())
result = json.loads((HERE / "result.json").read_text())
source = json.loads(Path(producer["states"]).read_text())
fixture = json.loads(Path(producer["fixture"]).read_text())
records = json.loads((HERE / "support.json").read_text())
controls = json.loads((HERE / "controls.json").read_text())
assert len(records) == 79424 and len(controls) == 2048

R = PolynomialRing(GF(2), "u")
u = R.gen()
F = GF(2**41, name="u", modulus=u**41+u**3+1)


def dec(value):
    return F(R([(int(value) >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(coef) << i for i, coef in enumerate(value.polynomial().list()))


def point(raw):
    return dec(raw[0]), dec(raw[1])


def neg(P):
    return P[0], P[0]+P[1]


def add(P, Q):
    if P is None:
        return Q
    if Q is None:
        return P
    x1,y1 = P
    x2,y2 = Q
    if x1 == x2:
        if y1+y2 == x1:
            return None
        assert P == Q and x1
        slope = x1+y1/x1
        x3 = slope**2+slope
        y3 = x1**2+(slope+1)*x3
    else:
        slope = (y1+y2)/(x1+x2)
        x3 = slope**2+slope+x1+x2
        y3 = slope*(x1+x3)+x3+y1
    return x3,y3


Q = point(fixture["public_point"])
residuals = [add(Q, neg(point(state["point"])))
             for state in source["states"][4]]
assert all(value is not None and value[0] for value in residuals)
w_by_id = {last_id:enc(1/value[0]) for last_id,value in enumerate(residuals)}
expected = []
collisions = 0
for last_id, residual in enumerate(residuals):
    last_cols = set(source["states"][4][last_id]["columns"])
    for prior_id, prior in enumerate(source["states"][3]):
        if last_cols.intersection(prior["columns"]):
            collisions += 1
            continue
        value = add(residual, neg(point(prior["point"])))
        assert value is not None and value[0]
        expected.append((w_by_id[last_id],enc(1/value[0]),prior_id,last_id))
expected.sort()
assert expected == [tuple(row) for row in records]
assert collisions == result["column_collision_pairs"] == 1232
support_end = time.monotonic()

support = {(w,z) for w,z,_,_ in expected}
assert len(support) == result["distinct_w_z_pairs"]
prefix_sets = {bits:{(w,z & ((1 << bits)-1)) for w,z in support}
               for bits in producer["prefix_bits"]}
hits = {str(bits):0 for bits in producer["prefix_bits"]}
exact_hits = 0
for w,z,i0,i1,i2,last_id in controls:
    first = None
    chosen = [source["states"][slot][sid]
              for slot,sid in enumerate((i0,i1,i2))]
    columns = [col for state in chosen+[source["states"][4][last_id]]
               for col in state["columns"]]
    assert len(columns) == len(set(columns))
    for state in chosen:
        first = add(first, point(state["point"]))
    assert first is not None and first[0]
    assert enc(1/first[0]) == z and w_by_id[last_id] == w
    exact_hits += (w,z) in support
    for bits in producer["prefix_bits"]:
        hits[str(bits)] += (w,z & ((1 << bits)-1)) in prefix_sets[bits]
assert exact_hits == result["reachable_exact_hits"]
assert hits == result["reachable_prefix_hits"]
finished = time.monotonic()
signal.alarm(0)
audit = {"status":"PASS_SAGE_FULL_JOINT_RESIDUAL_REPLAY",
         "candidate_id":None,"curve_id":p["curve_id"],
         "support_rows_checked":len(expected),"column_collision_pairs":collisions,
         "reachable_controls_checked":len(controls),
         "reachable_prefix_hits":hits,"reachable_exact_hits":exact_hits,
         "phase_seconds":{"support":support_end-started,
                          "controls":finished-support_end},
         "total_seconds":finished-started,
         "self_maxrss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         "protocol_sha256":sha(HERE / "audit_protocol.json")}
(HERE / "audit_result.json").write_text(json.dumps(audit,sort_keys=True,indent=2)+"\n")
print(json.dumps(audit,sort_keys=True))
