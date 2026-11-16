"""Independent scalar-field replay of the saved public group experiment."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "protocol.json").read_text())
result = json.loads((HERE / "result.json").read_text())
q = protocol["subgroup_order"]
cap = protocol["query_count_cap"]
assert result["status"] == "PASS"
assert result["protocol_sha256"] == hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest()
assert result["source_sha256"] == hashlib.sha256((HERE / "run_sage.py").read_bytes()).hexdigest()

queries = []
for i in range(cap):
    payload = b"xedni-zero-test-v1|" + b",".join([b"0"] * i)
    words = [int.from_bytes(hashlib.sha256(payload).digest()[j:j+4], "big")
             for j in (0, 4, 8, 12)]
    a, b = 1 + words[0] % (q - 1), 1 + words[1] % (q - 1)
    t1, t2 = words[2] % q, words[3] % q
    while (a + b) % q == 0:
        b = b % q + 1
    while t2 == t1:
        t2 = (t2 + 1) % q
    assert a != 0 and b != 0 and (a + b) % q != 0 and t1 != t2
    queries.append((a, b, t1, t2))

assert queries == [tuple(x) for x in result["negative_path_queries"]]
candidates = [((a * t1 + b * t2) * pow(a + b, -1, q)) % q
              for a, b, t1, t2 in queries]
assert candidates == result["negative_path_candidates"]
expected_hits = set(candidates)
assert len(result["rows"]) == q
tests = 0
for w, row in enumerate(result["rows"]):
    assert row["w"] == w
    first = next((i for i, (a, b, t1, t2) in enumerate(queries)
                  if (a * (w - t1) + b * (w - t2)) % q == 0), None)
    assert row["hit_index_zero_based"] == first
    assert row["hit"] == (w in expected_hits)
    assert row["tests"] == (cap if first is None else first + 1)
    tests += row["tests"]
assert result["hit_targets"] == len(expected_hits)
assert result["distinct_candidates"] == len(expected_hits)
assert result["group_relation_tests"] == tests
print(json.dumps({"schema": "xedni-adaptive-zero-test-audit-v1", "status": "PASS",
                  "result_sha256": hashlib.sha256((HERE / "result.json").read_bytes()).hexdigest(),
                  "targets": q, "cap": cap, "distinct_candidates": len(expected_hits),
                  "hit_targets": len(expected_hits), "group_relation_tests": tests}, sort_keys=True))
