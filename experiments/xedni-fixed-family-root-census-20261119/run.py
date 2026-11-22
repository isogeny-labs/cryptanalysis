#!/usr/bin/env python3
"""Exact root-index census for the frozen fixed-family public relation law."""

from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PROTOCOL = HERE / "protocol.json"
RESULT = HERE / "result.json"


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    for d in range(2, int(n**0.5) + 1):
        if n % d == 0:
            return False
    return True


def main() -> None:
    protocol = json.loads(PROTOCOL.read_text())
    source_path = REPO / protocol["source_protocol"]
    source_bytes = source_path.read_bytes()
    assert hashlib.sha256(source_bytes).hexdigest() == protocol["source_protocol_sha256"]
    source = json.loads(source_bytes)
    assert protocol["offsets"] == source["offsets"]
    assert protocol["vectors"] == source["vectors"]
    assert protocol["schema"] == "xedni-fixed-family-root-census-v1"
    assert protocol["offset_pair_law"].startswith("all ordered distinct pairs")
    offsets = protocol["offsets"]
    vectors = protocol["vectors"]
    pairs = list(itertools.permutations(offsets, 2))
    assert len(pairs) == 56 and len(vectors) == 13
    capacity = len(pairs) * len(vectors)
    rows = []
    for q in protocol["prime_orders"]:
        assert is_prime(q) and q > capacity
        roots = []
        for t1, t2 in pairs:
            for a, b in vectors:
                assert (a + b) % q != 0
                w = ((a * t1 + b * t2) * pow((a + b) % q, -1, q)) % q
                assert ((a + b) * w - a * t1 - b * t2) % q == 0
                roots.append(w)
        nonzero = {w for w in roots if w}
        row = {
            "q": q,
            "nonzero_targets": q - 1,
            "coefficient_count": len(vectors),
            "offset_pair_count": len(pairs),
            "capacity": capacity,
            "distinct_nonzero_roots": len(nonzero),
            "missed_nonzero_targets": q - 1 - len(nonzero),
            "zero_roots": roots.count(0),
            "duplicate_pair_roots": len(roots) - len(set(roots)),
            "capacity_missed_lower_bound": q - 1 - capacity,
        }
        assert row["missed_nonzero_targets"] >= row["capacity_missed_lower_bound"]
        rows.append(row)
    result = {
        "schema": "xedni-fixed-family-root-census-result-v1",
        "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
        "run_source_sha256": hashlib.sha256((HERE / "run.py").read_bytes()).hexdigest(),
        "audit_source_sha256": hashlib.sha256((HERE / "audit.py").read_bytes()).hexdigest(),
        "rows": rows,
    }
    RESULT.write_bytes(canonical_bytes(result))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
