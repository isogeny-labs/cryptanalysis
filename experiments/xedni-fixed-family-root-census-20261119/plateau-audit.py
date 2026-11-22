#!/usr/bin/env python3
"""Independent gcd-normalized root replay and determinant audit."""

from __future__ import annotations

import hashlib
import itertools
import json
from math import gcd
from pathlib import Path

HERE = Path(__file__).resolve().parent
result = json.loads((HERE / "plateau-result.json").read_text())
protocol_bytes = (HERE / "plateau-protocol.json").read_bytes()
protocol = json.loads(protocol_bytes)
source_bytes = (HERE / protocol["source_protocol"]).read_bytes()
source = json.loads(source_bytes)
assert result["protocol_sha256"] == hashlib.sha256(protocol_bytes).hexdigest()
assert result["source_sha256"] == hashlib.sha256(source_bytes).hexdigest()
assert result["plateau_source_sha256"] == hashlib.sha256((HERE / "plateau.py").read_bytes()).hexdigest()
assert result["plateau_audit_source_sha256"] == hashlib.sha256((HERE / "plateau-audit.py").read_bytes()).hexdigest()

canonical = set()
combinations = 0
for a, b in source["vectors"]:
    for t1 in source["offsets"]:
        for t2 in source["offsets"]:
            if t1 == t2:
                continue
            combinations += 1
            n, d = a * t1 + b * t2, a + b
            assert d != 0
            common = gcd(n, d)
            n, d = n // common, d // common
            if d < 0:
                n, d = -n, -d
            assert d > 0 and gcd(n, d) == 1
            canonical.add((n, d))

ordered = sorted(canonical)
maxdet = 0
for i, (n, d) in enumerate(ordered):
    for m, e in ordered[i + 1 :]:
        det = abs(n * e - m * d)
        assert det > 0
        maxdet = max(maxdet, det)

assert combinations == result["coefficient_offset_combinations"]
assert len(ordered) == result["distinct_rational_roots"]
assert sum(n != 0 for n, _ in ordered) == result["distinct_nonzero_rational_roots"]
assert max(d for _, d in ordered) == result["maximum_denominator"]
assert maxdet == result["maximum_pairwise_cross_determinant"]
assert result["prime_threshold"] == max(maxdet, result["maximum_denominator"])
digest = hashlib.sha256(("\n".join(f"{n}/{d}" for n, d in ordered) + "\n").encode()).hexdigest()
assert digest == result["canonical_root_list_sha256"]
print(f"rational roots={len(ordered)}, nonzero={sum(n != 0 for n, _ in ordered)}")
print(f"maximum denominator={max(d for _, d in ordered)}, maximum cross-determinant={maxdet}")
print("independent gcd and pairwise determinant replay passed")
