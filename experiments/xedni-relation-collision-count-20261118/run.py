#!/usr/bin/env python3
"""Evaluate the primitive-relation collision formula on frozen public rows."""
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "xedni-bounded-rank-coverage-20261118" / "result.json"
PROTOCOL = HERE / "protocol.json"


def canonical(obj):
    return (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode()


def main():
    source_bytes = SOURCE.read_bytes()
    source = json.loads(source_bytes)
    assert source["schema"] == "xedni-bounded-rank-coverage-result-v1"
    assert len(source["rows"]) == 39
    rows = []
    for row in source["rows"]:
        a, b, H, q = (row[k] for k in ("a", "b", "H", "q"))
        A, B, L = abs(a), abs(b), 2 * H + 1
        primitive = math.gcd(A, B) == 1
        no_wrap = q > 2 * H * (A + B)
        predicted = L * L - max(0, L - A) * max(0, L - B) if primitive and no_wrap else None
        rows.append({"hit_index": row["hit_index"], "H": H, "q": q, "a": a, "b": b,
                     "primitive": primitive, "no_wrap": no_wrap,
                     "wrap_margin": q - 2 * H * (A + B),
                     "predicted_reachable": predicted,
                     "enumerated_reachable": row["reachable"],
                     "match": predicted == row["reachable"] if predicted is not None else None})
    result = {"schema": "xedni-relation-collision-count-result-v1", "status": "complete",
              "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
              "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
              "rows": rows,
              "assumption_passes": sum(r["primitive"] and r["no_wrap"] for r in rows),
              "matches": sum(r["match"] is True for r in rows),
              "mismatches": sum(r["match"] is False for r in rows)}
    (HERE / "result.json").write_bytes(canonical(result))
    print(json.dumps({k: result[k] for k in ("assumption_passes", "matches", "mismatches")}, sort_keys=True))


if __name__ == "__main__":
    main()
