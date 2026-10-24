"""Independent exact group-sum lookup for all frozen batch keys."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
INPUT = HERE.parent/"n41_n131_fivepair_w9_w29_20261017/join_input.tsv"
R = PolynomialRing(GF(2), "w")
w = R.gen()
F = GF(2**41, name="w", modulus=w**41+w**3+1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(n):
    n = int(n)
    return F(R([(n >> i) & 1 for i in range(41)]))


def enc(x):
    return sum(int(c) << i for i, c in enumerate(x.polynomial().list()))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE/"batch_protocol.json").read_text())
producer = json.loads((HERE/"batch_result.json").read_text())
assert sha(INPUT) == protocol["input_sha256"]
assert producer["protocol_sha256"] == sha(HERE/"batch_protocol.json")
assert not (HERE/"batch_audit_result.json").exists()
states = [[None]*284 for _ in range(2)]
columns = [[None]*284 for _ in range(2)]
for line in INPUT.read_text().splitlines()[1:]:
    f = line.split()
    if f[0] == "S" and int(f[1]) < 2:
        slot, sid = map(int, f[1:3])
        states[slot][sid] = E(dec(f[9]), dec(f[10]))
        columns[slot][sid] = {int(f[7]), int(f[8])}
assert all(all(p is not None for p in slot) for slot in states)

start = time.monotonic()
index = {}
count = 0
for aid, A in enumerate(states[0]):
    for bid, B in enumerate(states[1]):
        if not columns[0][aid].isdisjoint(columns[1][bid]):
            continue
        count += 1
        S = A+B
        key = None if S == E(0) else (enc(S[0]), enc(S[1]))
        index.setdefault(key, []).append((aid,bid))
build_seconds = time.monotonic()-start

lookup_start = time.monotonic()
positive_rows = []
for idx, (item, row) in enumerate(zip(protocol["keys"], producer["rows"])):
    assert item["suffix_ids"] == row["suffix_ids"]
    expected = sorted(index.get(tuple(item["key"]), []))
    observed = [tuple(ids) for ids in row["matches"]]
    assert expected == observed, (idx, expected, observed)
    if expected:
        positive_rows.append({"index": idx, "matches": [list(v) for v in expected]})
lookup_seconds = time.monotonic()-lookup_start
assert positive_rows[0] == {"index": 0, "matches": [[0,130]]}
result = {"status": "PASS_BATCH_INDEPENDENT_GROUP_CENSUS",
          "candidate_id": None,
          "protocol_sha256": sha(HERE/"batch_protocol.json"),
          "producer_sha256": sha(HERE/"batch_result.json"),
          "auditor_sha256": sha(Path(__file__)),
          "eligible_pair_states": count, "distinct_group_sum_keys": len(index),
          "query_count": len(protocol["keys"]), "positive_rows": positive_rows,
          "build_seconds": build_seconds, "lookup_seconds": lookup_seconds,
          "self_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
with (HERE/"batch_audit_result.json").open("x") as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write("\n")
print(json.dumps({k:result[k] for k in ("status", "eligible_pair_states", "query_count", "positive_rows", "build_seconds", "lookup_seconds")}))
