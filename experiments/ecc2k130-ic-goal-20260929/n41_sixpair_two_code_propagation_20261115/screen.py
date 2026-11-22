"""Screen every pair of first-two source codes by CNF/XOR propagation."""

import hashlib
import json
import resource
import signal
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
PREVIOUS = BASE.parent / "n41_sixpair_code_propagation_20261115"
SOURCE = BASE.parent / "n41_sixpair_shared_target_20261017"
sys.path.insert(0, str(PREVIOUS))
import screen as previous  # noqa: E402

PROTOCOL = BASE / "protocol.json"
RESULT = BASE / "result.json"
XCNF = SOURCE / "public.xcnf"
WITNESS = SOURCE / "join_audit_result.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes():
    return {"screen": sha(Path(__file__)), "propagator": sha(PREVIOUS / "screen.py"),
            "public_xcnf": sha(XCNF), "witness": sha(WITNESS)}


def save_new(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def mask_code(mask):
    source_bits = [bit for bit in range(8) if bit != 5]
    return sum(((mask >> bit) & 1) << index
               for index, bit in enumerate(source_bits))


def main(mode):
    if mode == "freeze":
        save_new(PROTOCOL, {
            "kind": "n41_sixpair_two_code_cnf_xor_propagation_v1",
            "candidate_id": None,
            "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
            "input_law": "all 40 by 40 valid first-two source-code pairs on the archived ordinary public point",
            "target_count": 1,
            "one_worker": True,
            "wall_cap_seconds": 180,
            "rss_cap_bytes": 4 * 1024**3,
            "source_sha256": source_hashes(),
        })
        return
    protocol = json.loads(PROTOCOL.read_text())
    assert protocol["source_sha256"] == source_hashes()
    signal.alarm(protocol["wall_cap_seconds"])
    start = time.monotonic_ns()
    nvars, clauses, xors, groups = previous.parse()
    assert len(groups) == 6
    first, second = groups[:2]
    assert set(first).isdisjoint(second)
    first_codes = previous.allowed_codes(clauses, first)
    second_codes = previous.allowed_codes(clauses, second)
    witness = json.loads(WITNESS.read_text())
    assert witness["status"] == "PASS_INDEPENDENT_N41_SIXPAIR_PUBLIC_RELATION"
    witness_codes = [mask_code(witness["pair_rows"][slot]["masks"][0])
                     for slot in (0, 1)]
    assert witness_codes[0] in first_codes and witness_codes[1] in second_codes
    cnf_occ, xor_occ = previous.incidence(nvars, clauses, xors)
    rows = []
    for left in first_codes:
        for right in second_codes:
            item_start = time.monotonic_ns()
            status, assigned, reason = previous.propagate(
                nvars, clauses, xors, cnf_occ, xor_occ, first + second,
                left | (right << 7))
            rows.append({"first_code": left, "second_code": right,
                         "status": status, "assigned_variables": assigned,
                         "conflict_reason": reason,
                         "elapsed_ns": time.monotonic_ns() - item_start})
    signal.alarm(0)
    assert len(rows) == 1600
    witness_row = next(row for row in rows
                       if (row["first_code"], row["second_code"]) == tuple(witness_codes))
    assert witness_row["status"] == "OPEN"
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    assert peak <= protocol["rss_cap_bytes"]
    save_new(RESULT, {
        "kind": "n41_sixpair_two_code_cnf_xor_propagation_result_v1",
        "status": "PASS_BOUNDED_TWO_CODE_PROPAGATION_SCREEN",
        "protocol_sha256": sha(PROTOCOL),
        "public_xcnf_sha256": sha(XCNF),
        "first_slot_code_wires": first,
        "second_slot_code_wires": second,
        "witness_codes": witness_codes,
        "code_pair_count": len(rows),
        "conflicts": sum(row["status"] == "CONFLICT" for row in rows),
        "open_families": sum(row["status"] == "OPEN" for row in rows),
        "rows": rows,
        "total_wall_ns": time.monotonic_ns() - start,
        "peak_self_rss_bytes": peak,
    })
    print("PASS_BOUNDED_TWO_CODE_PROPAGATION_SCREEN", len(rows),
          sum(row["status"] == "CONFLICT" for row in rows),
          witness_codes)


if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] in ("freeze", "run")
    main(sys.argv[1])
