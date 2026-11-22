"""Recheck every literal in both archived XCNFs against the declared bijection."""

import hashlib
import itertools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "n41_w8_tenpair_functional_20261012"
sys.path.insert(0, str(SOURCE))
import build  # noqa: E402


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / "protocol.json").read_text())
for path, digest in protocol["sources"].items():
    assert sha(path) == digest, path
lists, targets = build.source()
chart = json.loads((SOURCE / "positive_chart.json").read_text())
circuit, wires = build.build(lists, targets, chart, False)
count = circuit.next_var - 1
ordered = wires["branches"] + [v for row in wires["selectors"] for v in row] + wires["flags"]
assert len(ordered) == len(set(ordered)) == 1413
chosen = set(ordered)
permutation = ordered + [var for var in range(1, count + 1) if var not in chosen]
assert len(permutation) == len(set(permutation)) == count
mapping = [0] * (count + 1)
for new, old in enumerate(permutation, 1):
    mapping[old] = new

rows = xor = 0
with (SOURCE / "ordinary.xcnf").open() as original, (HERE / "ordered.xcnf").open() as changed:
    assert original.readline() == changed.readline() == "p cnf 289065 731771\n"
    for left, right in itertools.zip_longest(original, changed):
        assert left is not None and right is not None
        lterms, rterms = left.split(), right.split()
        assert (lterms[0] == "x") == (rterms[0] == "x")
        is_xor = lterms[0] == "x"
        a = list(map(int, lterms[1:-1] if is_xor else lterms[:-1]))
        b = list(map(int, rterms[1:-1] if is_xor else rterms[:-1]))
        assert len(a) == len(b)
        assert lterms[-1] == rterms[-1] == "0"
        for old, new in zip(a, b):
            assert new == mapping[abs(old)] * (1 if old > 0 else -1)
        rows += 1
        xor += is_xor
assert (rows, xor) == (731771, 127245)
result = {
    "status": "PASS_INDEPENDENT_COMPLETE_XCNF_PERMUTATION_AUDIT",
    "rows": rows, "xor_rows": xor, "variables": count,
    "primary_variables": len(ordered),
    "old_xcnf_sha256": sha(SOURCE / "ordinary.xcnf"),
    "ordered_xcnf_sha256": sha(HERE / "ordered.xcnf"),
    "protocol_sha256": sha(HERE / "protocol.json"),
    "audit_source_sha256": sha(__file__),
}
with (HERE / "permutation_audit_result.json").open("x") as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write("\n")
print(result["status"], rows)
