"""Independently replay all first-code propagation fixed points by full scans."""

import hashlib
import json
import resource
import signal
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
XCNF = HERE.parent / "n41_sixpair_shared_target_20261017" / "public.xcnf"
RESULT = HERE / "result.json"
PROTOCOL = HERE / "protocol.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scan_input():
    clauses, xors = [], []
    with XCNF.open() as stream:
        header = stream.readline().split()
        assert header == ["p", "cnf", "31533", "86646"]
        for line in stream:
            if not line.strip() or line.startswith("c"):
                continue
            if line.startswith("x"):
                terms = list(map(int, line[1:].split()))
                assert terms[-1] == 0
                xors.append((tuple(abs(x) for x in terms[:-1]),
                             1 ^ (sum(x < 0 for x in terms[:-1]) & 1)))
            else:
                terms = list(map(int, line.split()))
                assert terms[-1] == 0
                clauses.append(tuple(terms[:-1]))
    assert len(clauses) == 82957 and len(xors) == 3689
    return clauses, xors


def full_scan(clauses, xors, code_group, code):
    assignment = {v: (code >> i) & 1 for i, v in enumerate(code_group)}
    passes = 0
    while True:
        passes += 1
        changed = False
        for clause in clauses:
            if any(abs(v) in assignment and assignment[abs(v)] == (v > 0)
                   for v in clause):
                continue
            unknown = [v for v in clause if abs(v) not in assignment]
            if not unknown:
                return "CONFLICT", len(assignment), passes
            if len(unknown) == 1:
                literal = unknown[0]
                assignment[abs(literal)] = int(literal > 0)
                changed = True
        for row, rhs in xors:
            parity = sum(assignment.get(v, 0) for v in row if v in assignment) & 1
            unknown = [v for v in row if v not in assignment]
            if not unknown:
                if parity != rhs:
                    return "CONFLICT", len(assignment), passes
            elif len(unknown) == 1:
                assignment[unknown[0]] = rhs ^ parity
                changed = True
        if not changed:
            return "OPEN", len(assignment), passes


def main():
    signal.alarm(180)
    result = json.loads(RESULT.read_text())
    protocol = json.loads(PROTOCOL.read_text())
    assert result["protocol_sha256"] == sha(PROTOCOL)
    assert result["public_xcnf_sha256"] == sha(XCNF)
    assert protocol["source_sha256"]["public_xcnf"] == sha(XCNF)
    clauses, xors = scan_input()
    codes = result["first_slot_code_wires"]
    assert len(codes) == 7 and len(result["rows"]) == 40
    start = time.monotonic_ns()
    rows = []
    for expected in result["rows"]:
        code = expected["code"]
        status, assigned, passes = full_scan(clauses, xors, codes, code)
        assert (status, assigned) == (expected["status"], expected["assigned_variables"])
        rows.append({"code": code, "status": status,
                     "assigned_variables": assigned, "passes": passes})
    signal.alarm(0)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    assert peak < 4 * 1024**3
    output = {"status": "PASS_INDEPENDENT_FULL_SCAN_PROPAGATION_REPLAY",
              "input_sha256": {"public_xcnf": sha(XCNF), "protocol": sha(PROTOCOL),
                               "result": sha(RESULT), "auditor": sha(Path(__file__))},
              "code_count": len(rows), "conflicts": sum(r["status"] == "CONFLICT" for r in rows),
              "rows": rows, "wall_ns": time.monotonic_ns() - start,
              "peak_self_rss_bytes": peak}
    with (HERE / "audit_result.json").open("x") as stream:
        json.dump(output, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(output["status"], output["code_count"], output["conflicts"])


if __name__ == "__main__":
    main()
