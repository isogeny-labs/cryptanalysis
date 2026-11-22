"""Reclassify all source triples and replay sampled fixed points by full scans."""

import hashlib
import json
import resource
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
PREVIOUS = EXP / "n41_sixpair_code_propagation_20261115"
SOURCE = EXP / "n41_sixpair_shared_target_20261017"
sys.path.insert(0, str(PREVIOUS))
import audit as reference  # noqa: E402

PROTOCOL = HERE / "audit_protocol.json"
ROWS = HERE / "rows.jsonl"
RESULT = HERE / "result.json"
AUDIT = HERE / "audit_result.json"
JOIN = SOURCE / "join_input.tsv"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def code(mask):
    bits = [0, 1, 2, 3, 4, 6, 7]
    return sum(((mask >> source_bit) & 1) << target_bit
               for target_bit, source_bit in enumerate(bits))


def independently_parse_columns():
    columns = [dict() for _ in range(3)]
    counts = [dict() for _ in range(3)]
    lines = JOIN.read_text().splitlines()
    assert lines[0].split()[:3] == ["ECC2K41", "6", "160"]
    for line in lines[1:]:
        fields = line.split()
        slot = int(fields[1])
        if slot > 2:
            continue
        value = code(int(fields[3]))
        pair = frozenset((int(fields[7]), int(fields[8])))
        assert len(pair) == 2
        assert value not in columns[slot] or columns[slot][value] == pair
        columns[slot][value] = pair
        counts[slot][value] = counts[slot].get(value, 0) + 1
    assert all(len(part) == 40 for part in columns)
    assert all(set(part.values()) == {4} for part in counts)
    return columns


def main():
    p = json.loads(PROTOCOL.read_text())
    assert not AUDIT.exists()
    assert p["sha256"] == {
        "audit": sha(Path(__file__)), "reference_full_scan": sha(PREVIOUS / "audit.py"),
        "join_input": sha(JOIN), "rows": sha(ROWS), "result": sha(RESULT),
        "xcnf": sha(SOURCE / "public.xcnf")}
    result = json.loads(RESULT.read_text())
    rows = [json.loads(line) for line in ROWS.read_text().splitlines()]
    assert len(rows) == result["completed"] == 64000
    columns = independently_parse_columns()
    source_invalid = source_valid_conflicts = 0
    for row in rows:
        a, b, c = row["codes"]
        all_columns = columns[0][a] | columns[1][b] | columns[2][c]
        source_ok = len(all_columns) == 6
        assert source_ok == row["source_valid"]
        source_invalid += not source_ok
        source_valid_conflicts += source_ok and row["status"] == "CONFLICT"
    assert source_invalid == result["source_invalid"]
    assert source_valid_conflicts == result["source_valid_conflicts"]
    chosen = {0, len(rows)-1}
    chosen.update(range(0, len(rows), 997))
    for predicate in (
        lambda r: r["status"] == "CONFLICT",
        lambda r: r["status"] == "OPEN" and r["source_valid"],
        lambda r: r["status"] == "CONFLICT" and r["source_valid"],
        lambda r: r["status"] == "OPEN" and not r["source_valid"],
    ):
        matches = (i for i, row in enumerate(rows) if predicate(row))
        for _ in range(50):
            index = next(matches, None)
            if index is None:
                break
            chosen.add(index)
    witness = tuple(result["witness_codes"])
    witness_index = next(i for i, row in enumerate(rows)
                         if tuple(row["codes"]) == witness)
    chosen.add(witness_index)
    clauses, xors = reference.scan_input()
    wires = [tuple(int(x) for x in group) for group in p["code_wires"]]
    assert len(wires) == 3 and len(set(sum((list(g) for g in wires), []))) == 21
    pinned = sum((list(g) for g in wires), [])
    signal.alarm(p["wall_cap_seconds"])
    started = time.monotonic_ns()
    replay = []
    for index in sorted(chosen):
        row = rows[index]
        a, b, c = row["codes"]
        status, assigned, passes = reference.full_scan(
            clauses, xors, pinned, a | (b << 7) | (c << 14))
        assert status == row["status"], (index, status, row["status"])
        if status == "OPEN":
            assert assigned == row["assigned_variables"]
        replay.append({"row_index": index, "codes": row["codes"],
                       "status": status, "assigned_variables": assigned,
                       "passes": passes})
    signal.alarm(0)
    output = {"kind": "n41_sixpair_three_code_independent_audit_v1",
              "status": "PASS_SOURCE_CENSUS_AND_FULL_SCAN_SAMPLE",
              "protocol_sha256": sha(PROTOCOL), "source_invalid": source_invalid,
              "source_valid_conflicts": source_valid_conflicts,
              "rows_checked_for_source_validity": len(rows),
              "full_scan_replay_count": len(replay), "replay": replay,
              "wall_ns": time.monotonic_ns()-started,
              "peak_self_rss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    with AUDIT.open("x") as stream:
        json.dump(output, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps({k: output[k] for k in ("status", "source_invalid",
                                               "source_valid_conflicts",
                                               "full_scan_replay_count")}, sort_keys=True))


if __name__ == "__main__":
    main()
