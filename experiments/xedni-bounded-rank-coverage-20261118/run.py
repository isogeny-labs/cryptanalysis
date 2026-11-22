#!/usr/bin/env python3
"""Exact coefficient-box images in the fresh panel's public cyclic subgroups."""
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "xedni-hensel-fresh-transfer-20261118" / "run-result.json.gz"
PROTOCOL = HERE / "protocol.json"


def canonical_bytes(obj):
    return (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode()


def main():
    source_bytes = SOURCE.read_bytes()
    source = json.loads(gzip.decompress(source_bytes))
    protocol_bytes = PROTOCOL.read_bytes()
    assert source["status"] == "complete" and source["eligible_count"] == 13
    hits = [h for h in source["public_hits"] if h["status"] == "eligible"]
    assert len(hits) == 13
    rows = []
    for index, hit in enumerate(hits):
        q, a, b = (hit[k] for k in ("q", "a", "b"))
        assert q > 1 and b % q != 0 and (a * b) % q != 0
        for H in (2, 4, 8):
            vals = {((b * u - a * v) % q) for u in range(-H, H + 1) for v in range(-H, H + 1)}
            box = (2 * H + 1) ** 2
            assert len(vals) <= min(q, box)
            rows.append({"hit_index": index, "p": hit["p"], "q": q, "a": a, "b": b,
                         "H": H, "box_size": box, "reachable": len(vals),
                         "unreachable": q - len(vals), "reachable_fraction": f"{len(vals)}/{q}",
                         "box_bound": min(q, box)})
    result = {"schema": "xedni-bounded-rank-coverage-result-v1", "status": "complete",
              "protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(),
              "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
              "rows": rows}
    (HERE / "result.json").write_bytes(canonical_bytes(result))
    print(json.dumps({"rows": len(rows), "q_values": sorted({r["q"] for r in rows}),
                      "unreachable_rows": sum(r["unreachable"] > 0 for r in rows),
                      "max_fraction": max(r["reachable"] / r["q"] for r in rows)}, sort_keys=True))


if __name__ == "__main__":
    main()
