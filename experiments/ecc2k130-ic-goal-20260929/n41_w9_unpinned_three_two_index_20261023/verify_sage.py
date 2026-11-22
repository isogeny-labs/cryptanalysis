"""Independent complete left-pair group census for the S3 oracle panel."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
INPUT = HERE.parent / "n41_n131_fivepair_w9_w29_20261017/join_input.tsv"
R = PolynomialRing(GF(2), "v")
v = R.gen()
F = GF(2**41, name="v", modulus=v**41+v**3+1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(n):
    n = int(n)
    return F(R([(n >> i) & 1 for i in range(41)]))


def enc(x):
    return sum(int(c) << i for i, c in enumerate(x.polynomial().list()))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


protocol = json.loads((HERE / "protocol.json").read_text())
producer = json.loads((HERE / "result.json").read_text())
assert sha(INPUT) == protocol["input_sha256"]
assert producer["protocol_sha256"] == sha(HERE / "protocol.json")
assert not (HERE / "audit_result.json").exists()
states = [[None]*284 for _ in range(2)]
cols = [[None]*284 for _ in range(2)]
for line in INPUT.read_text().splitlines()[1:]:
    f = line.split()
    if f[0] == "S" and int(f[1]) < 2:
        slot, sid = map(int, f[1:3])
        states[slot][sid] = E(dec(f[9]), dec(f[10]))
        cols[slot][sid] = frozenset(map(int, f[7:9]))
assert all(all(p is not None for p in slot) for slot in states)

start = time.monotonic()
index = {}
eligible = 0
exceptions = 0
s3_checked = 0
for a_id, A in enumerate(states[0]):
    for b_id, B in enumerate(states[1]):
        if not cols[0][a_id].isdisjoint(cols[1][b_id]):
            continue
        eligible += 1
        S = A+B
        if S == E(0) or not A[0] or not B[0] or not S[0]:
            exceptions += 1
        else:
            a, b, t = 1/A[0], 1/B[0], 1/S[0]
            assert (1+(a*t)**2)*b**2 + a*t*b + a**2+t**2 == 0
            s3_checked += 1
        key = None if S == E(0) else (enc(S[0]), enc(S[1]))
        index.setdefault(key, []).append((a_id, b_id))
build_seconds = time.monotonic()-start

query_start = time.monotonic()
rows = []
for item, observed in zip(protocol["keys"], producer["queries"]):
    key = tuple(item["key"])
    expected = sorted(index.get(key, []))
    actual = [tuple(pair) for pair in observed["matches"]]
    assert expected == actual, (item["suffix_ids"], expected, actual)
    rows.append({"suffix_ids": item["suffix_ids"], "match_count": len(expected),
                 "matches": [list(pair) for pair in expected]})
query_seconds = time.monotonic()-query_start
assert rows[0]["matches"] == [[0, 130]]
assert all(row["match_count"] == 0 for row in rows[1:])
result = {"status": "PASS_INDEPENDENT_COMPLETE_PAIR_CENSUS",
          "candidate_id": None, "protocol_sha256": sha(HERE/"protocol.json"),
          "producer_sha256": sha(HERE/"result.json"),
          "auditor_sha256": sha(Path(__file__)),
          "eligible_pair_states": eligible, "exceptional_chart_pairs": exceptions,
          "s3_group_bridge_checks": s3_checked,
          "distinct_group_sum_keys": len(index),
          "build_seconds": build_seconds, "query_seconds": query_seconds,
          "self_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "queries": rows}
with (HERE/"audit_result.json").open("x") as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write("\n")
print(json.dumps({k: result[k] for k in ("status", "eligible_pair_states", "exceptional_chart_pairs", "s3_group_bridge_checks", "distinct_group_sum_keys", "build_seconds", "query_seconds")}, sort_keys=True))
