#!/usr/bin/env python3
"""Exact rational-root and pairwise determinant certificate."""

from __future__ import annotations

import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
protocol_bytes = (HERE / "plateau-protocol.json").read_bytes()
protocol = json.loads(protocol_bytes)
source_bytes = (HERE / protocol["source_protocol"]).read_bytes()
assert hashlib.sha256(source_bytes).hexdigest() == protocol["source_protocol_sha256"]
source = json.loads(source_bytes)
assert protocol["schema"] == "xedni-rational-root-plateau-v1"
roots = {
    Fraction(a * t1 + b * t2, a + b)
    for t1, t2 in itertools.permutations(source["offsets"], 2)
    for a, b in source["vectors"]
}
ordered = sorted((r.numerator, r.denominator) for r in roots)
assert all(d > 0 for _, d in ordered)
detmax = max(abs(n * e - m * d) for (n, d), (m, e) in itertools.combinations(ordered, 2))
maximum_denominator = max(d for _, d in ordered)
result = {
    "schema": "xedni-rational-root-plateau-result-v1",
    "protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(),
    "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
    "plateau_source_sha256": hashlib.sha256((HERE / "plateau.py").read_bytes()).hexdigest(),
    "plateau_audit_source_sha256": hashlib.sha256((HERE / "plateau-audit.py").read_bytes()).hexdigest(),
    "coefficient_offset_combinations": len(source["vectors"]) * len(source["offsets"]) * (len(source["offsets"]) - 1),
    "distinct_rational_roots": len(ordered),
    "distinct_nonzero_rational_roots": sum(n != 0 for n, _ in ordered),
    "maximum_denominator": maximum_denominator,
    "maximum_pairwise_cross_determinant": detmax,
    "prime_threshold": max(detmax, maximum_denominator),
    "canonical_root_list_sha256": hashlib.sha256(
        ("\n".join(f"{n}/{d}" for n, d in ordered) + "\n").encode()
    ).hexdigest(),
}
(HERE / "plateau-result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2, sort_keys=True))
