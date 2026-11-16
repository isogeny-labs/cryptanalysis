"""Replay an equality-adaptive symbolic group trace on every p=313 target."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "protocol.json").read_text())
assert (protocol["field_prime"], protocol["subgroup_order"]) == (313, 331)
q, cap = 331, protocol["new_form_cap"]
E = EllipticCurve(GF(313), [-1, -2])
G = E(protocol["generator"])
assert G != E(0) and q * G == E(0)


def form(history):
    i = len(history)
    if i == 0:
        return (0, 1)
    if i == 1:
        return (1, 0)
    payload = "xedni-adaptive-collision-v1|" + ",".join(
        "1" if bit else "0" for bit in history)
    digest = hashlib.sha256(payload.encode("ascii")).digest()
    return tuple(int.from_bytes(digest[j:j + 4], "big") % q for j in (0, 4))


negative_forms = [form([False] * i) for i in range(cap)]
candidate_pairs = []
for i, (a, b) in enumerate(negative_forms):
    for j in range(i):
        c, d = negative_forms[j]
        if a != c:
            candidate_pairs.append({"i": i, "j": j,
                                    "candidate": ((d - b) * pow(a - c, -1, q)) % q})

rows = []
comparisons = 0
forms_created = 0
for w in range(q):
    Q = w * G
    history = []
    prior = []
    first_hit = None
    for i in range(cap):
        a, b = form(history)
        point = a * Q + b * G
        forms_created += 1
        for j, (c, other) in enumerate(prior):
            if a == c:
                continue
            comparisons += 1
            if point == other:
                first_hit = [i, j]
                break
        if first_hit is not None:
            break
        prior.append((a, point))
        history.append(False)
    rows.append({"w": w, "forms_created": i + 1,
                 "first_hit": first_hit})

result = {"schema": "xedni-adaptive-collision-trace-result-v1", "status": "PASS",
          "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest(),
          "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          "target_count": q, "new_form_cap": cap,
          "negative_path_forms": negative_forms,
          "active_pairs": len(candidate_pairs), "distinct_candidates": len({x["candidate"] for x in candidate_pairs}),
          "hit_targets": sum(row["first_hit"] is not None for row in rows),
          "forms_created": forms_created, "group_equality_tests": comparisons,
          "candidate_pairs": candidate_pairs, "rows": rows}
print(json.dumps(result, sort_keys=True, indent=2))
