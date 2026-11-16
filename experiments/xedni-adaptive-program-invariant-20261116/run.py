"""Complete three-step adaptive add/sub group and affine replay on Z/7."""
import gzip
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ROWS = ROOT / "rows"
ROWS.mkdir(exist_ok=True)


def command(step, labels):
    last = len(labels) - 1
    if step == 0:
        return ("add", 0, 1) if labels[0] < labels[1] else ("sub", 1, 0)
    if step == 1:
        return ("sub", last, 0) if labels[-1] in labels[:-1] else ("add", last, 1)
    return ("add", last, last) if (labels[0] + labels[-1]) % 2 == 0 else ("sub", 1, last)


first_counts = Counter()
op_counts = Counter()
shards = []
cases = 0
for w in (0, 2, 3, 4, 5, 6):
    shard = ROWS / f"w{w}.jsonl.gz"
    with shard.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as out:
            for enc in itertools.permutations(range(7)):
                points = [1, w]
                forms = [(0, 1), (1, 0)]
                commands = []
                first_collision = None
                for step in range(3):
                    labels = [enc[p] for p in points]
                    op, i, j = command(step, labels)
                    sign = 1 if op == "add" else -1
                    point = (points[i] + sign * points[j]) % 7
                    form = ((forms[i][0] + sign * forms[j][0]) % 7,
                            (forms[i][1] + sign * forms[j][1]) % 7)
                    assert point == (form[0] * w + form[1]) % 7
                    if first_collision is None and point in points:
                        first_collision = step + 1
                    points.append(point)
                    forms.append(form)
                    commands.append([op, i, j])
                    op_counts[op] += 1
                first_counts[str(first_collision)] += 1
                row = {"w": w, "encoding": list(enc), "commands": commands,
                       "points": points, "forms": [list(x) for x in forms],
                       "first_collision_step": first_collision, "status": "verified"}
                out.write((json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode())
                cases += 1
    shards.append({"path": str(shard.relative_to(ROOT)),
                   "sha256": hashlib.sha256(shard.read_bytes()).hexdigest()})
result = {"schema": "xedni-adaptive-program-invariant-result-v1", "status": "PASS",
          "cases": cases, "commands": cases * 3,
          "first_collision_step_counts": dict(sorted(first_counts.items())),
          "operation_counts": dict(sorted(op_counts.items())), "invariant_mismatches": 0,
          "shards": shards}
(ROOT / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps({k: v for k, v in result.items() if k != "shards"}, sort_keys=True))
