"""Screen all three-code N41 families by exact CNF/XOR unit propagation."""

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
import screen as previous  # noqa: E402

PROTOCOL = HERE / "protocol.json"
ROWS = HERE / "rows.jsonl"
RESULT = HERE / "result.json"
XCNF = SOURCE / "public.xcnf"
JOIN = SOURCE / "join_input.tsv"
WITNESS = SOURCE / "join_audit_result.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes():
    return {"run": sha(Path(__file__)), "propagator": sha(PREVIOUS / "screen.py"),
            "xcnf": sha(XCNF), "join_input": sha(JOIN), "witness": sha(WITNESS)}


def mask_code(mask):
    return sum(((mask >> bit) & 1) << index
               for index, bit in enumerate(bit for bit in range(8) if bit != 5))


def source_columns():
    result = [dict() for _ in range(3)]
    seen = [dict() for _ in range(3)]
    with JOIN.open() as stream:
        header = stream.readline().split()
        assert header[:3] == ["ECC2K41", "6", "160"]
        for line in stream:
            fields = line.split()
            assert fields[0] == "S" and len(fields) == 11
            slot = int(fields[1])
            if slot >= 3:
                continue
            code = mask_code(int(fields[3]))
            columns = tuple(map(int, fields[7:9]))
            assert len(set(columns)) == 2
            if code in result[slot]:
                assert result[slot][code] == columns
            result[slot][code] = columns
            seen[slot][code] = seen[slot].get(code, 0) + 1
    assert all(len(part) == 40 for part in result)
    assert all(all(count == 4 for count in part.values()) for part in seen)
    return result


def alarm(_signum, _frame):
    raise TimeoutError("frozen three-code wall cap")


def main():
    p = json.loads(PROTOCOL.read_text())
    assert p["source_sha256"] == source_hashes()
    assert not ROWS.exists() and not RESULT.exists()
    witness = json.loads(WITNESS.read_text())
    assert witness["status"] == "PASS_INDEPENDENT_N41_SIXPAIR_PUBLIC_RELATION"
    witness_codes = [mask_code(witness["pair_rows"][i]["masks"][0])
                     for i in range(3)]
    columns = source_columns()
    started = time.monotonic_ns()
    nvars, clauses, xors, groups = previous.parse()
    assert len(groups) == 6
    codes = [previous.allowed_codes(clauses, group) for group in groups[:3]]
    assert all(c in allowed for c, allowed in zip(witness_codes, codes))
    assert all(set(columns[i]) == set(codes[i]) for i in range(3))
    cnf_occ, xor_occ = previous.incidence(nvars, clauses, xors)
    pinned = groups[0] + groups[1] + groups[2]
    assert len(pinned) == 21 and len(set(pinned)) == 21
    signal.signal(signal.SIGALRM, alarm)
    signal.alarm(p["wall_cap_seconds"])
    completed = conflicts = source_invalid = target_conflicts = witness_open = 0
    try:
        with ROWS.open("x") as output:
            for a in codes[0]:
                for b in codes[1]:
                    for c in codes[2]:
                        triplet = (a, b, c)
                        source_ok = len({column for i, code in enumerate(triplet)
                                         for column in columns[i][code]}) == 6
                        item_start = time.monotonic_ns()
                        status, assigned, reason = previous.propagate(
                            nvars, clauses, xors, cnf_occ, xor_occ, pinned,
                            a | (b << 7) | (c << 14))
                        row = {"codes": triplet, "status": status,
                               "source_valid": source_ok,
                               "assigned_variables": assigned,
                               "conflict_reason": reason,
                               "elapsed_ns": time.monotonic_ns() - item_start}
                        output.write(json.dumps(row, sort_keys=True,
                                                separators=(",", ":")) + "\n")
                        completed += 1
                        conflicts += status == "CONFLICT"
                        source_invalid += not source_ok
                        target_conflicts += status == "CONFLICT" and source_ok
                        witness_open += triplet == tuple(witness_codes) and status == "OPEN"
        status = "COMPLETE_THREE_CODE_PROPAGATION"
    except TimeoutError:
        status = "BOUNDED_UNKNOWN"
    finally:
        signal.alarm(0)
    assert witness_open == 1 if completed == 64000 else witness_open <= 1
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result = {"kind": "n41_sixpair_three_code_propagation_v1", "status": status,
              "protocol_sha256": sha(PROTOCOL), "rows_sha256": sha(ROWS),
              "completed": completed, "expected": 40**3,
              "conflicts": conflicts, "source_invalid": source_invalid,
              "source_valid_conflicts": target_conflicts,
              "witness_codes": witness_codes, "witness_open": witness_open == 1,
              "elapsed_ns": time.monotonic_ns() - started,
              "peak_self_rss_raw": peak}
    with RESULT.open("x") as output:
        json.dump(result, output, indent=2, sort_keys=True)
        output.write("\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
