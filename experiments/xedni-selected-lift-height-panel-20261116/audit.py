"""Independently replay the archived selection status and admitted heights."""
import gzip
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, QQ, RealField

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "xedni-varying-curve-selection-20261115" / "rows-v2.jsonl.gz"
with gzip.open(PARENT, "rt") as stream:
    source = [json.loads(line) for line in stream]
with gzip.open(HERE / "rows.jsonl.gz", "rt") as stream:
    measured = [json.loads(line) for line in stream]
assert len(source) == len(measured) == 1722
count = 0
for i, (original, row) in enumerate(zip(source, measured)):
    preserved = {key: value for key, value in row.items()
                 if key not in {"canonical_heights", "curve_discriminant", "parent_row_index"}}
    assert original == preserved, i
    if not original["accepted"]:
        assert "canonical_heights" not in row, i
        continue
    assert row["parent_row_index"] == i
    E = EllipticCurve(QQ, [QQ(row["A"]), QQ(row["B"])] )
    assert str(E.discriminant()) == row["curve_discriminant"]
    for (x, y), recorded in zip(row["lifted_points"], row["canonical_heights"]):
        replay = E(QQ(x), QQ(y)).height(precision=192, algorithm="pari")
        assert abs(RealField(192)(recorded) - replay) < RealField(192)("1e-30")
        count += 1
assert count == 40
result = {"status": "PASS", "parent_rows": 1722, "accepted_rows": 20,
          "replayed_point_heights": count, "precision_bits": 192,
          "absolute_agreement_threshold": "1e-30",
          "measured_rows_sha256": hashlib.sha256((HERE / "rows.jsonl.gz").read_bytes()).hexdigest()}
(HERE / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, sort_keys=True))
