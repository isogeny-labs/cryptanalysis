"""Extract the frozen p317 39-column relation rows from a full checkout."""
from pathlib import Path
import hashlib
import json
import os

H = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("ARCHIVE_ROOT", H.parent.parent))
P = json.loads((H / "protocol.json").read_text())
SOURCES = {
    "class": ("experiments/hecke-d79-conductor4-20261027/result.json", P["archived_class_result_sha256"]),
    "search": ("experiments/hecke-d79-conductor4-20261027/search-result.json", P["archived_search_result_sha256"]),
    "direct": ("experiments/hecke-d79-class-generic-rank-20261027/result.json", P["archived_direct_result_sha256"]),
}
docs = {}
for key, (name, digest) in SOURCES.items():
    blob = (ROOT / name).read_bytes()
    assert hashlib.sha256(blob).hexdigest() == digest
    docs[key] = json.loads(blob)
class_doc, search_doc, direct_doc = (docs[k] for k in ("class", "search", "direct"))
assert len(class_doc["class_points"]) == len(search_doc["projection_coordinates_mod61"]) == direct_doc["class_size"] == 39
extracted = {
    "schema": "x011-p317-archived-inputs-v1",
    "source_sha256": {k: v[1] for k,v in SOURCES.items()},
    "class_points": class_doc["class_points"],
    "base_rows": [x["row"] for x in class_doc["base_rows"]],
    "closed_rows": [x["class_part"] for x in class_doc["degree13_sources"] if x["status"] == "CLASS_CLOSED"],
    "short_cancellation_rows": [x["row"] for x in search_doc["candidates"]],
    "projection_coordinates_mod61": search_doc["projection_coordinates_mod61"],
    "projection_generator": search_doc["projection_generator"],
    "direct_candidate_count": len(direct_doc["candidates"]),
}
assert [len(extracted[k]) for k in ("base_rows", "closed_rows", "short_cancellation_rows")] == [18, 5, 80]
(H / "archived-inputs.json").write_text(json.dumps(extracted, sort_keys=True, indent=2) + "\n")
print(json.dumps({"points": 39, "base_rows": 18, "closed_rows": 5, "short_rows": 80}, sort_keys=True))
