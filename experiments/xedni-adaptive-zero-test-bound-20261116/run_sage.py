"""Replay a one-bit adaptive relation strategy on every p=313 subgroup scalar."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF

HERE = Path(__file__).resolve().parent
P = json.loads((HERE / "protocol.json").read_text())
assert P["field_prime"] == 313 and P["subgroup_order"] == 331
p, q, cap = 313, 331, P["query_count_cap"]
E = EllipticCurve(GF(p), [-1, -2])
G = E(P["generator"])
assert q * G == E(0) and G != E(0)


def query(history):
    payload = "xedni-zero-test-v1|" + ",".join("1" if bit else "0" for bit in history)
    digest = hashlib.sha256(payload.encode("ascii")).digest()
    words = [int.from_bytes(digest[4 * i:4 * i + 4], "big") for i in range(4)]
    a, b = 1 + words[0] % (q - 1), 1 + words[1] % (q - 1)
    t1, t2 = words[2] % q, words[3] % q
    while (a + b) % q == 0:
        b = b % q + 1
    while t2 == t1:
        t2 = (t2 + 1) % q
    return a, b, t1, t2


negative_path = []
for i in range(cap):
    negative_path.append(query([False] * i))
candidates = [((a * t1 + b * t2) * pow(a + b, -1, q)) % q
              for a, b, t1, t2 in negative_path]

rows = []
for w in range(q):
    Q = w * G
    history = []
    hit_index = None
    for i in range(cap):
        a, b, t1, t2 = query(history)
        U, V = Q - t1 * G, Q - t2 * G
        hit = a * U + b * V == E(0)
        assert hit == (w == candidates[i])
        if hit:
            hit_index = i
            break
        history.append(False)
    rows.append({"w": w, "hit_index_zero_based": hit_index,
                 "tests": i + 1, "hit": hit_index is not None})

result = {
    "schema": "xedni-adaptive-zero-test-result-v1",
    "status": "PASS",
    "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest(),
    "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "field_prime": p,
    "subgroup_order": q,
    "query_count_cap": cap,
    "negative_path_queries": negative_path,
    "negative_path_candidates": candidates,
    "distinct_candidates": len(set(candidates)),
    "hit_targets": sum(row["hit"] for row in rows),
    "group_relation_tests": sum(row["tests"] for row in rows),
    "rows": rows,
}
print(json.dumps(result, sort_keys=True, indent=2))
