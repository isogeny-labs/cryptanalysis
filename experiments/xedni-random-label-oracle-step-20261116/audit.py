"""Independently recompute transition labels and cardinalities."""
import hashlib
import itertools
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
result = json.loads((HERE / "result.json").read_text())
protocol = json.loads((HERE / "protocol.json").read_text())
assert result["protocol_sha256"] == hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest()
assert result["source_sha256"] == hashlib.sha256((HERE / "run.py").read_bytes()).hexdigest()
q = 5
x, y = tuple(protocol["initial_traces"]["x"]), tuple(protocol["initial_traces"]["y"])
traces = {
    "initial_x": x, "initial_y": y,
    "fresh_x": x + ((2 * x[2]) % q,),
    "fresh_y": y + ((2 * y[2]) % q,),
    "boundary_x": x + ((x[1] + x[2]) % q,),
    "boundary_y": y + ((y[1] + y[2]) % q,),
}
assert result["fresh_traces"] == [list(traces["fresh_x"]), list(traces["fresh_y"])]
assert result["boundary_traces"] == [list(traces["boundary_x"]), list(traces["boundary_y"])]
for key, trace in traces.items():
    tally = defaultdict(int)
    for encoding in itertools.permutations(range(q)):
        tally[tuple(encoding[g] for g in trace)] += 1
    encoded = {",".join(map(str, labels)): count for labels, count in sorted(tally.items())}
    assert result["histograms"][key] == encoded
    assert result["tuple_counts"][key] == len(tally)
    assert sum(tally.values()) == 120
assert result["tuple_counts"] == {
    "initial_x": 60, "initial_y": 60,
    "fresh_x": 120, "fresh_y": 120,
    "boundary_x": 120, "boundary_y": 60,
}
assert result["histograms"]["initial_x"] == result["histograms"]["initial_y"]
assert result["histograms"]["fresh_x"] == result["histograms"]["fresh_y"]
assert result["histograms"]["boundary_x"] != result["histograms"]["boundary_y"]
assert result["encodings"] == result["paired_encodings"] == 120
sigma = result["coupling_permutation"]
assert sorted(sigma) == list(range(q))
assert all(sigma[a] == b for a, b in zip(traces["fresh_x"], traces["fresh_y"]))
print(json.dumps({"schema": "xedni-random-label-oracle-step-audit-v1", "status": "PASS",
                  "result_sha256": hashlib.sha256((HERE / "result.json").read_bytes()).hexdigest(),
                  "encodings": 120, "tuple_counts": result["tuple_counts"]}, sort_keys=True))
