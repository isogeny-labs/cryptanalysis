"""Derived candidate sets for each frozen visible transcript."""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / "xedni-adaptive-program-invariant-20261116"
protocol = json.loads((ROOT / "candidate-protocol.json").read_text())
assert hashlib.sha256((ROOT / "result.json").read_bytes()).hexdigest() == protocol["parent_transcript_result_sha256"]
assert hashlib.sha256((ROOT / "transcripts.jsonl.gz").read_bytes()).hexdigest() == protocol["parent_transcript_rows_sha256"]

candidate_rows = {}
size_counts = Counter()
with gzip.open(ROOT / "transcripts.jsonl.gz", "rt") as stream:
    for line in stream:
        row = json.loads(line)
        forms = row["forms"]
        candidates = set()
        active = 0
        for i in range(len(forms)):
            for j in range(i + 1, len(forms)):
                if forms[i] == forms[j] or forms[i][0] == forms[j][0]:
                    continue
                active += 1
                numerator = (forms[j][1] - forms[i][1]) % 7
                denominator = (forms[i][0] - forms[j][0]) % 7
                candidates.add(numerator * pow(denominator, -1, 7) % 7)
        key = tuple(row["labels"])
        candidate_rows[key] = {"labels": row["labels"], "candidates": sorted(candidates),
                               "active_pairs": active, "candidate_count": len(candidates)}
        assert len(candidates) <= active <= 10
        size_counts[str(len(candidates))] += 1

out = ROOT / "candidate-rows.jsonl.gz"
with out.open("wb") as raw:
    with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as stream:
        for key in sorted(candidate_rows):
            stream.write((json.dumps(candidate_rows[key], sort_keys=True, separators=(",", ":")) + "\n").encode())

cases = 0
informative = 0
uninformative_first = 0
for shard in sorted((PARENT / "rows").glob("w*.jsonl.gz")):
    with gzip.open(shard, "rt") as stream:
        for line in stream:
            row = json.loads(line)
            labels = tuple(row["encoding"][p] for p in row["points"])
            candidates = candidate_rows[labels]["candidates"]
            hits = [(i, j) for i in range(5) for j in range(i + 1, 5)
                    if row["points"][i] == row["points"][j]
                    and row["forms"][i] != row["forms"][j]]
            if hits:
                informative += 1
                assert row["w"] in candidates
            if row["first_collision_step"] is not None:
                k = row["first_collision_step"] + 1
                if any(row["points"][k] == row["points"][j]
                       and row["forms"][k] == row["forms"][j] for j in range(k)):
                    uninformative_first += 1
            cases += 1
result = {"schema": "xedni-transcript-candidate-result-v1", "status": "PASS",
          "transcripts": len(candidate_rows), "cases": cases,
          "candidate_size_counts": dict(sorted(size_counts.items())),
          "informative_hit_cases": informative,
          "first_collision_has_identical_form_cases": uninformative_first,
          "candidate_membership_mismatches": 0,
          "candidate_rows_sha256": hashlib.sha256(out.read_bytes()).hexdigest()}
(ROOT / "candidate-result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
