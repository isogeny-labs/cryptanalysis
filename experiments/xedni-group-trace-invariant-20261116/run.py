"""Replay every adaptive group step and symbolic form on Z/7."""
import hashlib
import itertools
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / "xedni-label-conditioned-collision-20261116" / "result.json"
assert hashlib.sha256(PARENT.read_bytes()).hexdigest() == json.loads(
    (ROOT / "protocol.json").read_text())["parent_result_sha256"]
parent = json.loads(PARENT.read_text())
rows = defaultdict(lambda: {"attempts": 0, "group_hits": 0, "symbolic_hits": 0,
                           "mismatches": 0})
for w in range(7):
    if w == 1:
        continue
    prior = (1, w)
    for enc in itertools.permutations(range(7)):
        visible = (enc[prior[0]], enc[prior[1]])
        row = rows[visible]
        row["attempts"] += 1
        if visible[0] < visible[1]:
            group_next = (prior[0] + prior[1]) % 7
            affine_next = (1 + w) % 7
        else:
            group_next = (prior[1] + prior[1]) % 7
            affine_next = (2 * w) % 7
        group_hit = group_next in prior
        symbolic_hit = affine_next in prior
        row["group_hits"] += group_hit
        row["symbolic_hits"] += symbolic_hit
        row["mismatches"] += group_hit != symbolic_hit
out_rows = [{"labels": list(labels), **values} for labels, values in sorted(rows.items())]
parent_rows = {tuple(row["labels"]): row for row in parent["rows"]}
for row in out_rows:
    ref = parent_rows[tuple(row["labels"])]
    assert row["attempts"] == ref["eligible_encodings"]
    assert row["group_hits"] == row["symbolic_hits"] == ref["collision_encodings"]
    assert row["mismatches"] == 0
result = {"schema": "xedni-group-trace-invariant-result-v1", "status": "PASS",
          "scalar_encoding_pairs": sum(x["attempts"] for x in out_rows),
          "group_hits": sum(x["group_hits"] for x in out_rows),
          "symbolic_hits": sum(x["symbolic_hits"] for x in out_rows),
          "mismatches": sum(x["mismatches"] for x in out_rows),
          "rows": out_rows}
(ROOT / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({k: v for k, v in result.items() if k != "rows"}, sort_keys=True))
