"""Independent exhaustive check of candidate sets and group equalities."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / "xedni-adaptive-program-invariant-20261116"
result = json.loads((ROOT / "candidate-result.json").read_text())
with gzip.open(ROOT / "candidate-rows.jsonl.gz", "rt") as stream:
    candidates = {tuple(row["labels"]): row for row in map(json.loads, stream)}
assert len(candidates) == result["transcripts"]
assert hashlib.sha256((ROOT / "candidate-rows.jsonl.gz").read_bytes()).hexdigest() == result["candidate_rows_sha256"]
for row in candidates.values():
    assert len(row["labels"]) == 5
    assert row["candidate_count"] == len(row["candidates"])
    assert row["candidate_count"] <= row["active_pairs"] <= 10

cases = 0
informative = 0
checked_transcripts = set()
for shard in sorted((PARENT / "rows").glob("w*.jsonl.gz")):
    with gzip.open(shard, "rt") as stream:
        for line in stream:
            row = json.loads(line)
            labels = tuple(row["encoding"][p] for p in row["points"])
            candidate_set = set(candidates[labels]["candidates"])
            forms = row["forms"]
            if labels not in checked_transcripts:
                # Enumerate every possible scalar, so both soundness and
                # completeness of the saved candidate set are checked.
                expected = {
                    value for value in range(7)
                    if any(forms[i] != forms[j]
                           and (forms[i][0] * value + forms[i][1]) % 7 ==
                               (forms[j][0] * value + forms[j][1]) % 7
                           for i in range(5) for j in range(i + 1, 5))}
                assert candidate_set == expected
                assert candidates[labels]["active_pairs"] == sum(
                    forms[i][0] != forms[j][0]
                    for i in range(5) for j in range(i + 1, 5))
                checked_transcripts.add(labels)
            hit = any(row["points"][i] == row["points"][j]
                      and forms[i] != forms[j]
                      for i in range(5) for j in range(i + 1, 5))
            informative += hit
            if hit:
                assert row["w"] in candidate_set
            cases += 1
assert cases == result["cases"] == 30240
assert len(checked_transcripts) == result["transcripts"]
assert informative == result["informative_hit_cases"]
assert result["candidate_membership_mismatches"] == 0
audit = {"schema": "xedni-transcript-candidate-audit-v1", "status": "PASS",
         "cases": cases, "transcripts": len(candidates),
         "result_sha256": hashlib.sha256((ROOT / "candidate-result.json").read_bytes()).hexdigest()}
(ROOT / "candidate-audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
print(json.dumps(audit, sort_keys=True))
