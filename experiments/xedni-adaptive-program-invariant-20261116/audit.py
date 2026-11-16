"""Independent replay of every saved finite adaptive group trace."""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
result = json.loads((ROOT / "result.json").read_text())
first_counts = Counter()
op_counts = Counter()
cases = 0
for shard in result["shards"]:
    path = ROOT / shard["path"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == shard["sha256"]
    with gzip.open(path, "rt") as rows:
        for line in rows:
            row = json.loads(line)
            w = row["w"]
            enc = row["encoding"]
            assert sorted(enc) == list(range(7))
            assert w in (0, 2, 3, 4, 5, 6)
            points = [1, w]
            forms = [[0, 1], [1, 0]]
            first = None
            for step, saved in enumerate(row["commands"]):
                labels = [enc[x] for x in points]
                last = len(points) - 1
                if step == 0:
                    expected = ["add", 0, 1] if labels[0] < labels[1] else ["sub", 1, 0]
                elif step == 1:
                    expected = ["sub", last, 0] if labels[-1] in labels[:-1] else ["add", last, 1]
                else:
                    expected = ["add", last, last] if (labels[0] + labels[-1]) % 2 == 0 else ["sub", 1, last]
                assert saved == expected
                op, i, j = saved
                coefficient = 1 if op == "add" else 6
                new_point = (points[i] + coefficient * points[j]) % 7
                new_form = [(forms[i][0] + coefficient * forms[j][0]) % 7,
                            (forms[i][1] + coefficient * forms[j][1]) % 7]
                assert new_point == (new_form[0] * w + new_form[1]) % 7
                if first is None and new_point in points:
                    first = step + 1
                points.append(new_point)
                forms.append(new_form)
                op_counts[op] += 1
            assert row["points"] == points
            assert row["forms"] == forms
            assert row["first_collision_step"] == first
            assert row["status"] == "verified"
            first_counts[str(first)] += 1
            cases += 1
assert cases == result["cases"] == 6 * 5040
assert cases * 3 == result["commands"]
assert dict(sorted(first_counts.items())) == result["first_collision_step_counts"]
assert dict(sorted(op_counts.items())) == result["operation_counts"]
assert result["invariant_mismatches"] == 0
audit = {"schema": "xedni-adaptive-program-invariant-audit-v1", "status": "PASS",
         "result_sha256": hashlib.sha256((ROOT / "result.json").read_bytes()).hexdigest(),
         "cases": cases, "commands": cases * 3}
(ROOT / "audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
print(json.dumps(audit, sort_keys=True))
