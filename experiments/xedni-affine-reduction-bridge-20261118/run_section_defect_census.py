#!/usr/bin/env python3
"""Exhaustive integer-section defect census for frozen Z/331Z inputs."""

import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "section-defect-protocol.json"
RESULT = HERE / "section-defect-result.json"


def main() -> None:
    raw = PROTOCOL.read_bytes()
    spec = json.loads(raw)
    q = spec["subgroup_order"]
    assert q == 331
    counts = Counter()
    witnesses = {}
    reduction_failures = 0
    formula_failures = 0
    for x in range(q):
        for y in range(q):
            defect = (x + y) % q - x - y
            counts[defect] += 1
            witnesses.setdefault(str(defect), [x, y])
            reduction_failures += defect % q != 0
            formula_failures += defect != (-q if x + y >= q else 0)
    expected = {0: q * (q + 1) // 2, -q: q * (q - 1) // 2}
    assert counts == expected
    assert reduction_failures == formula_failures == 0
    result = {
        "schema": "xedni-section-defect-result-v1",
        "protocol_sha256": hashlib.sha256(raw).hexdigest(),
        "subgroup_order": q,
        "ordered_pairs": q * q,
        "defect_histogram": {str(k): counts[k] for k in sorted(counts)},
        "expected_analytic_counts": {str(k): expected[k] for k in sorted(expected)},
        "reduction_failures": reduction_failures,
        "formula_failures": formula_failures,
        "witnesses": {"zero": [0, 1], "wrap": [q - 1, 1]},
        "observed_first_witnesses": witnesses,
        "status": "complete_exact_census",
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
