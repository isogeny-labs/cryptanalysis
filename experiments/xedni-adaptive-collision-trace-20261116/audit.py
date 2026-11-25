"""Independent modular audit of every adaptive first-hit row."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "protocol.json").read_text())
result = json.loads((HERE / "result.json").read_text())
assert result["protocol_sha256"] == hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest()
assert result["source_sha256"] == hashlib.sha256((HERE / "run_sage.py").read_bytes()).hexdigest()
q, cap = protocol["subgroup_order"], protocol["new_form_cap"]
assert q == result["target_count"] == 331 and cap == result["new_form_cap"] == 24

forms = []
for i in range(cap):
    if i < 2:
        pair = (0, 1) if i == 0 else (1, 0)
    else:
        digest = hashlib.sha256(("xedni-adaptive-collision-v1|" +
            ",".join("0" for _ in range(i))).encode("ascii")).digest()
        pair = (int.from_bytes(digest[:4], "big") % q,
                int.from_bytes(digest[4:8], "big") % q)
    forms.append(pair)
assert forms == [tuple(x) for x in result["negative_path_forms"]]
pairs = [{"i": i, "j": j,
          "candidate": ((forms[j][1] - forms[i][1]) *
                        pow(forms[i][0] - forms[j][0], -1, q)) % q}
         for i in range(cap) for j in range(i) if forms[i][0] != forms[j][0]]
assert pairs == result["candidate_pairs"]
candidate_set = {x["candidate"] for x in pairs}
assert result["active_pairs"] == len(pairs)
assert result["distinct_candidates"] == len(candidate_set)

comparison_count = 0
form_count = 0
for w, row in enumerate(result["rows"]):
    first = None
    for i, (a, b) in enumerate(forms):
        for j in range(i):
            c, d = forms[j]
            if a == c:
                continue
            comparison_count += 1
            if (a * w + b - c * w - d) % q == 0:
                first = [i, j]
                break
        if first is not None:
            break
    assert row == {"w": w, "forms_created": i + 1, "first_hit": first}
    form_count += i + 1
assert result["hit_targets"] == len(candidate_set)
assert result["group_equality_tests"] == comparison_count
assert result["forms_created"] == form_count
print(json.dumps({"schema": "xedni-adaptive-collision-trace-audit-v1", "status": "PASS",
                  "result_sha256": hashlib.sha256((HERE / "result.json").read_bytes()).hexdigest(),
                  "targets": q, "active_pairs": len(pairs),
                  "distinct_candidates": len(candidate_set),
                  "hit_targets": result["hit_targets"],
                  "group_equality_tests": comparison_count,
                  "forms_created": form_count}, sort_keys=True))
