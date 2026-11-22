#!/usr/bin/env python3
"""Independent forward-equation replay of the fixed-family root census."""

from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "protocol.json").read_text())
result = json.loads((HERE / "result.json").read_text())
assert result["protocol_sha256"] == hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest()
assert result["run_source_sha256"] == hashlib.sha256((HERE / "run.py").read_bytes()).hexdigest()
assert result["audit_source_sha256"] == hashlib.sha256((HERE / "audit.py").read_bytes()).hexdigest()
pairs = list(itertools.permutations(protocol["offsets"], 2))
vectors = protocol["vectors"]

for row in result["rows"]:
    q = row["q"]
    hit = [False] * q
    zero_count = 0
    solutions = 0
    for t1, t2 in pairs:
        for a, b in vectors:
            rhs = (a * t1 + b * t2) % q
            lhs_factor = (a + b) % q
            matches = 0
            for w in range(q):
                if (lhs_factor * w) % q == rhs:
                    matches += 1
                    hit[w] = True
                    zero_count += w == 0
            assert matches == 1
            solutions += matches
    nonzero_hits = sum(hit[1:])
    assert nonzero_hits == row["distinct_nonzero_roots"]
    assert q - 1 - nonzero_hits == row["missed_nonzero_targets"]
    assert zero_count == row["zero_roots"]
    assert solutions == row["capacity"]
    assert solutions - sum(hit) == row["duplicate_pair_roots"]
    print(f"q={q}: exact forward replay passed; hits={nonzero_hits}; missed={q-1-nonzero_hits}")
