"""Replay all two-code propagation fixed points with independent full scans."""

import hashlib
import json
import resource
import signal
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
PREVIOUS = BASE.parent / "n41_sixpair_code_propagation_20261115"
sys.path.insert(0, str(PREVIOUS))
import audit as reference  # noqa: E402

RESULT = BASE / "result.json"
PROTOCOL = BASE / "protocol.json"
AUDIT = BASE / "audit_result.json"
XCNF = BASE.parent / "n41_sixpair_shared_target_20261017" / "public.xcnf"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    result = json.loads(RESULT.read_text())
    protocol = json.loads(PROTOCOL.read_text())
    assert result["protocol_sha256"] == sha(PROTOCOL)
    assert result["public_xcnf_sha256"] == sha(XCNF)
    assert protocol["source_sha256"]["public_xcnf"] == sha(XCNF)
    assert len(result["rows"]) == 1600
    wires = tuple(result["first_slot_code_wires"] + result["second_slot_code_wires"])
    assert len(wires) == 14 and len(set(wires)) == 14
    clauses, xors = reference.scan_input()
    signal.alarm(900)
    start = time.monotonic_ns()
    rows = []
    for expected in result["rows"]:
        left, right = expected["first_code"], expected["second_code"]
        status, assigned, passes = reference.full_scan(
            clauses, xors, wires, left | (right << 7))
        assert status == expected["status"], (
            left, right, status, expected["status"])
        if status == "OPEN":
            assert assigned == expected["assigned_variables"], (
                left, right, assigned, expected["assigned_variables"])
        rows.append({"first_code": left, "second_code": right,
                     "status": status, "assigned_variables": assigned,
                     "passes": passes})
    signal.alarm(0)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    assert peak <= 4 * 1024**3
    assert (result["witness_codes"] == [6, 100] and
            next(row for row in rows if (row["first_code"], row["second_code"]) == (6, 100))["status"] == "OPEN")
    output = {
        "kind": "n41_sixpair_two_code_independent_propagation_audit_v1",
        "status": "PASS_INDEPENDENT_FULL_SCAN_TWO_CODE_REPLAY",
        "input_sha256": {"public_xcnf": sha(XCNF), "protocol": sha(PROTOCOL),
                         "result": sha(RESULT), "auditor": sha(Path(__file__)),
                         "reference_full_scan": sha(PREVIOUS / "audit.py")},
        "code_pair_count": len(rows),
        "conflicts": sum(row["status"] == "CONFLICT" for row in rows),
        "rows": rows,
        "wall_ns": time.monotonic_ns() - start,
        "peak_self_rss_bytes": peak,
    }
    with AUDIT.open("x") as stream:
        json.dump(output, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(output["status"], output["code_pair_count"], output["conflicts"])


if __name__ == "__main__":
    main()
