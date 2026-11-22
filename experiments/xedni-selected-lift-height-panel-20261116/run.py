"""Replay the sealed p47 selection rows and measure every admitted point height."""

import gzip
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, QQ, RealField


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "xedni-varying-curve-selection-20261115" / "rows-v2.jsonl.gz"
EXPECTED = "9a594d96f369fb14f1a4cf6270b1c811ceda515e1c2a7eccab4d011ca8f3f322"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert digest(PARENT) == EXPECTED
rows = [json.loads(line) for line in gzip.open(PARENT, "rt")]
assert len(rows) == 1722
assert sum(row["accepted"] for row in rows) == 20

curves = {}
for index, row in enumerate(rows):
    if not row["accepted"]:
        continue
    key = (row["A"], row["B"])
    E = curves.setdefault(key, EllipticCurve(QQ, [QQ(row["A"]), QQ(row["B"])]))
    heights = []
    for x, y in row["lifted_points"]:
        P = E(QQ(x), QQ(y))
        heights.append(str(P.height(precision=128, algorithm="pari")))
    row["canonical_heights"] = heights
    row["curve_discriminant"] = str(E.discriminant())
    row["parent_row_index"] = index

out = HERE / "rows.jsonl.gz"
with out.open("wb") as raw:
    with gzip.GzipFile(fileobj=raw, mode="wb", filename="", compresslevel=9, mtime=0) as stream:
        for row in rows:
            stream.write((json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode())

summary = {"schema": "xedni-selected-lift-height-panel-result-v1",
           "parent_rows_sha256": EXPECTED, "rows_sha256": digest(out),
           "population": len(rows), "accepted": 20, "curves": []}
for (A, B), E in sorted(curves.items(), key=lambda kv: (QQ(kv[0][0]), QQ(kv[0][1]))):
    subset = [r for r in rows if r["accepted"] and (r["A"], r["B"]) == (A, B)]
    RR = RealField(128)
    hs = [RR(h) for r in subset for h in r["canonical_heights"]]
    positive = [h for h in hs if h > 0]
    summary["curves"].append({"A": A, "B": B, "model_discriminant": str(E.discriminant()),
                               "ordered_rows": len(subset), "positive_height_points": len(positive),
                               "min_selected_height": str(min(positive)) if positive else None,
                               "max_selected_height": str(max(hs)),
                               "observed_ratio": str(max(hs) / min(positive)) if positive else None})
(HERE / "result.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
print(json.dumps(summary, indent=2, sort_keys=True))
