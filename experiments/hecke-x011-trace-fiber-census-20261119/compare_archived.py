"""Retrospective exact-set comparison with two archived D79 class records."""
from pathlib import Path
import gzip
import hashlib
import json

H = Path(__file__).resolve().parent
R = json.loads((H / "result.json").read_text())
ledger = [json.loads(line) for line in gzip.decompress((H / "points.jsonl.gz").read_bytes()).splitlines()]
source = H / "archived-class-points.json"
archive = json.loads(source.read_text())
assert archive["schema"] == "x011-archived-class-points-v1"
rows = []
for item in archive["rows"]:
    p, t = item["p"], item["abs_trace"]
    found = {(row["x"], row["y"]) for row in ledger
             if row["p"] == p and row.get("abs_trace") == t}
    recorded = {tuple(point) for point in item["class_points"]}
    assert len(recorded) == len(item["class_points"])
    assert found == recorded
    summary = next(row for row in R["summary"] if row["p"] == p)
    assert summary["archived_trace_fiber"]["full_fiber_points"] == len(found)
    rows.append({"p": p, "abs_trace": t, "point_count": len(found),
                 "exact_set_match": True, "source_result_sha256": item["source_result_sha256"]})

out = {"schema": "x011-archived-class-comparison-v1", "status": "PASS",
       "comparison_kind": "retrospective", "rows": rows,
       "archive_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
       "census_result_sha256": hashlib.sha256((H / "result.json").read_bytes()).hexdigest()}
(H / "archived-comparison-result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(json.dumps(out, sort_keys=True, indent=2))
