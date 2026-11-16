"""Independent transcript grouping and form-evaluation audit."""
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / "xedni-adaptive-program-invariant-20261116"
result = json.loads((ROOT / "result.json").read_text())
summary_path = ROOT / "transcripts.jsonl.gz"
assert hashlib.sha256(summary_path.read_bytes()).hexdigest() == result["transcripts_sha256"]
with gzip.open(summary_path, "rt") as stream:
    summaries = {tuple(item["labels"]): item for item in map(json.loads, stream)}
counts = defaultdict(int)
scalars = defaultdict(set)
cases = 0
for name in sorted((PARENT / "rows").glob("w*.jsonl.gz")):
    with gzip.open(name, "rt") as stream:
        for line in stream:
            row = json.loads(line)
            labels = tuple(row["encoding"][x] for x in row["points"])
            saved = summaries[labels]
            assert saved["forms"] == row["forms"]
            assert saved["commands"] == row["commands"]
            assert saved["first_collision_step"] == row["first_collision_step"]
            # Check the full group trace against each saved affine form.
            for point, (slope, intercept) in zip(row["points"], saved["forms"]):
                assert point == (slope * row["w"] + intercept) % 7
            counts[labels] += 1
            scalars[labels].add(row["w"])
            cases += 1
assert cases == result["cases"] == 30240
assert len(summaries) == result["distinct_transcripts"]
for labels, saved in summaries.items():
    assert saved["count"] == counts[labels]
    assert saved["scalar_count"] == len(scalars[labels])
assert result["shared_by_multiple_scalars"] == sum(len(scalars[x]) > 1 for x in summaries)
assert result["form_or_command_mismatches"] == 0
audit = {"schema": "xedni-transcript-determinism-audit-v1", "status": "PASS",
         "cases": cases, "distinct_transcripts": len(summaries),
         "result_sha256": hashlib.sha256((ROOT / "result.json").read_bytes()).hexdigest()}
(ROOT / "audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
print(json.dumps(audit, sort_keys=True))
