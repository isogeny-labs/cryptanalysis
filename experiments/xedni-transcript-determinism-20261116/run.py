"""Reconstruct forms from visible labels across the frozen complete replay."""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / "xedni-adaptive-program-invariant-20261116"
protocol = json.loads((ROOT / "protocol.json").read_text())
assert hashlib.sha256((PARENT / "result.json").read_bytes()).hexdigest() == protocol["parent_result_sha256"]
source = json.loads((PARENT / "result.json").read_text())


def reconstruct(labels):
    forms = [[0, 1], [1, 0]]
    commands = []
    for step in range(3):
        visible = labels[: len(forms)]
        last = len(forms) - 1
        if step == 0:
            command = ["add", 0, 1] if visible[0] < visible[1] else ["sub", 1, 0]
        elif step == 1:
            command = ["sub", last, 0] if visible[-1] in visible[:-1] else ["add", last, 1]
        else:
            command = ["add", last, last] if (visible[0] + visible[-1]) % 2 == 0 else ["sub", 1, last]
        op, i, j = command
        sign = 1 if op == "add" else -1
        forms.append([(forms[i][0] + sign * forms[j][0]) % 7,
                      (forms[i][1] + sign * forms[j][1]) % 7])
        commands.append(command)
    return forms, commands


table = {}
cases = 0
first_counts = Counter()
for shard in source["shards"]:
    path = PARENT / shard["path"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == shard["sha256"]
    with gzip.open(path, "rt") as rows:
        for line in rows:
            row = json.loads(line)
            labels = tuple(row["encoding"][point] for point in row["points"])
            forms, commands = reconstruct(labels)
            assert forms == row["forms"]
            assert commands == row["commands"]
            key = tuple(labels)
            if key not in table:
                table[key] = {"labels": list(labels), "forms": forms,
                              "commands": commands, "count": 0, "scalars": set(),
                              "first_collision_step": row["first_collision_step"]}
            entry = table[key]
            assert entry["forms"] == forms
            assert entry["commands"] == commands
            assert entry["first_collision_step"] == row["first_collision_step"]
            entry["count"] += 1
            entry["scalars"].add(row["w"])
            first_counts[str(row["first_collision_step"])] += 1
            cases += 1
out = ROOT / "transcripts.jsonl.gz"
with out.open("wb") as raw:
    with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as stream:
        for key in sorted(table):
            entry = table[key]
            entry["scalar_count"] = len(entry.pop("scalars"))
            stream.write((json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n").encode())
result = {"schema": "xedni-transcript-determinism-result-v1", "status": "PASS",
          "cases": cases, "distinct_transcripts": len(table),
          "shared_by_multiple_scalars": sum(x["scalar_count"] > 1 for x in table.values()),
          "first_collision_step_counts": dict(sorted(first_counts.items())),
          "form_or_command_mismatches": 0,
          "transcripts_sha256": hashlib.sha256(out.read_bytes()).hexdigest()}
(ROOT / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
