"""Extract prior p317 degree-13 outside-trace equations for exact matching."""
from pathlib import Path
import hashlib
import json
import os

H = Path(__file__).resolve().parent
archive = Path(os.environ.get("ARCHIVE_ROOT", "/Volumes/SSD990/cryptanalysis"))
source = archive/"experiments/hecke-d79-conductor4-20261027/result.json"
expected = "d65d744fa291b1a90df7a43209ecc38d74075e458125604c3e8f42e49560de15"
blob = source.read_bytes()
assert hashlib.sha256(blob).hexdigest() == expected
doc = json.loads(blob)
rows = [{"source":r["source"],"outside_traces":r["outside_traces"],
         "class_part":r["class_part"]} for r in doc["degree13_sources"]
        if r["status"] == "OUTSIDE_CLASS_TRACE"]
assert len(rows) == 34
out = {"schema":"x011-p317-archived-outside-v1","source_sha256":expected,"rows":rows}
(H/"archived-outside.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
print(json.dumps({"outside_sources":len(rows)},sort_keys=True))
