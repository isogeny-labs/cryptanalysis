"""Exhaustive adaptive fresh-step census for two Z/7 traces."""
import itertools
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TRACES = {"x": (1, 2), "y": (1, 3)}


def census(trace):
    result = Counter()
    branches = Counter()
    for labels in itertools.permutations(range(7)):
        first, second = labels[trace[0]], labels[trace[1]]
        pair = (0, 1) if first < second else (1, 1)
        output = (trace[pair[0]] + trace[pair[1]]) % 7
        assert output not in trace
        result[(pair, first, second, labels[output])] += 1
        branches[str(pair)] += 1
    return result, branches


x, xb = census(TRACES["x"])
y, yb = census(TRACES["y"])
assert x == y
assert xb == yb
assert sum(x.values()) == 5040
out = {
    "schema": "xedni-adaptive-oracle-coupling-result-v1",
    "status": "PASS",
    "encodings_per_trace": 5040,
    "branch_counts": xb,
    "distinct_branch_label_events": len(x),
    "histogram_equal": True,
    "histogram": [
        {"pair": list(pair), "labels": [a, b, c], "count": count}
        for (pair, a, b, c), count in sorted(x.items())
    ],
}
(ROOT / "result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(json.dumps({k: v for k, v in out.items() if k != "histogram"}, sort_keys=True))
