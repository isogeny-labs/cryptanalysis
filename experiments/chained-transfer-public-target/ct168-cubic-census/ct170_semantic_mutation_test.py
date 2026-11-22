#!/usr/bin/env python3
"""CT170: real, synchronized counter manipulations that conserve point/field totals.
These are *negative* controls: valid totals alone must not certify frozen records.
"""
import argparse
import copy
import json
import tempfile
from pathlib import Path

from ct168_trace_audit import audit


def replay(a, b, path):
    with tempfile.TemporaryDirectory(prefix="ct170-") as tmp:
        p = Path(tmp) / "direct.json"
        s = Path(tmp) / "generic.json"
        p.write_text(json.dumps(a, separators=(",", ":")))
        s.write_text(json.dumps(b, separators=(",", ":")))
        return audit(p, s)


def source_same_trace(a, b):
    # Points and q stay unchanged even though three source census buckets differ.
    v = a["source_cubic"]
    v["zero_rhs_x"] -= 2
    v["nonzero_square_x"] += 1
    v["nonsquare_x"] += 1
    w = b["counts"][0]
    w["zero"] -= 2
    w["nonzero_square"] += 1


def mutant_synchronized(a, b):
    # Mutant point count is not a trace checked by the old auditor.
    v = a["mutated_twist"]
    v["points"] += 2
    v["nonzero_square_x"] += 1
    v["nonsquare_x"] -= 1
    w = b["counts"][2]
    w["n"] += 2
    w["nonzero_square"] += 1


def run(direct, generic, expose_prepatch=False):
    original_a = json.loads(Path(direct).read_text())
    original_b = json.loads(Path(generic).read_text())
    canonical = replay(original_a, original_b, "canonical")
    if canonical["minimal_isogeny_extension_degree_over_K"] != 6:
        raise RuntimeError("canonical reference does not match CT168")
    cases = [
        ("source-counts-preserve-trace", source_same_trace),
        ("mutant-row-coordinated", mutant_synchronized),
    ]
    outcomes = []
    for name, transform in cases:
        a = copy.deepcopy(original_a)
        b = copy.deepcopy(original_b)
        transform(a, b)
        try:
            replay(a, b, name)
        except (ValueError, KeyError, TypeError):
            outcome = "rejected"
        else:
            outcome = "accepted"
        outcomes.append({"case": name, "outcome": outcome})
    result = {"schema": "ct170-semantic-mutation-v1",
              "standing": "pcc:unverified", "cases": outcomes,
              "canonical_degree_over_K": 6}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    expected = "accepted" if expose_prepatch else "rejected"
    if any(row["outcome"] != expected for row in outcomes):
        raise RuntimeError(f"CT170 expected all {expected}: {outcomes}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("direct")
    parser.add_argument("generic")
    parser.add_argument("--expose-prepatch", action="store_true")
    args = parser.parse_args()
    run(args.direct, args.generic, args.expose_prepatch)
