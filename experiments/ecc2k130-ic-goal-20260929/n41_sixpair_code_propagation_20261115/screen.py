"""Test CNF/XOR unit propagation after fixing one N41 source-code family."""

import hashlib
import json
import resource
import signal
import sys
import time
from collections import Counter, deque
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "n41_sixpair_shared_target_20261017"
XCNF = SOURCE / "public.xcnf"
WITNESS = SOURCE / "join_audit_result.json"
PROTOCOL = HERE / "protocol.json"
RESULT = HERE / "result.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_new(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def parse():
    clauses, xors, groups = [], [], Counter()
    nvars = declared = None
    with XCNF.open() as source:
        for line in source:
            if line.startswith("p "):
                _, kind, nvars, declared = line.split()
                assert kind == "cnf"
                nvars, declared = int(nvars), int(declared)
                continue
            if not line.strip() or line.startswith("c"):
                continue
            if line.startswith("x"):
                literals = [int(v) for v in line[1:].split()]
                assert literals.pop() == 0
                variables = tuple(abs(v) for v in literals)
                assert len(variables) == len(set(variables))
                xors.append((variables, 1 ^ (sum(v < 0 for v in literals) & 1)))
            else:
                literals = [int(v) for v in line.split()]
                assert literals.pop() == 0
                clauses.append(tuple(literals))
                if len(literals) == 7:
                    groups[tuple(sorted(map(abs, literals)))] += 1
    assert nvars == 31533 and len(clauses) == 82957 and len(xors) == 3689
    assert declared == len(clauses) + len(xors)
    code_groups = sorted(group for group, count in groups.items() if count == 88)
    assert len(code_groups) == 6 and all(len(group) == 7 for group in code_groups)
    assert all(1 <= abs(v) <= nvars for clause in clauses for v in clause)
    assert all(1 <= v <= nvars for row, _ in xors for v in row)
    return nvars, clauses, xors, code_groups


def allowed_codes(clauses, code_group):
    forbidden = set()
    group = set(code_group)
    for clause in clauses:
        if len(clause) != 7 or {abs(v) for v in clause} != group:
            continue
        by_var = {abs(v): v for v in clause}
        forbidden.add(sum((by_var[var] < 0) << bit
                          for bit, var in enumerate(code_group)))
    assert len(forbidden) == 88
    allowed = sorted(set(range(128)) - forbidden)
    assert len(allowed) == 40
    return allowed


def incidence(nvars, clauses, xors):
    cnf = [[] for _ in range(nvars + 1)]
    xor = [[] for _ in range(nvars + 1)]
    for index, clause in enumerate(clauses):
        for literal in clause:
            cnf[abs(literal)].append((index, literal > 0))
    for index, (row, _) in enumerate(xors):
        for variable in row:
            xor[variable].append(index)
    return cnf, xor


def propagate(nvars, clauses, xors, cnf_occ, xor_occ, code_group, code):
    assignment = bytearray(nvars + 1)  # zero unknown, one false, two true
    left = [len(clause) for clause in clauses]
    satisfied = bytearray(len(clauses))
    xor_left = [len(row) for row, _ in xors]
    xor_parity = bytearray(len(xors))
    queue = deque()
    derived = 0

    def assign(variable, truth):
        nonlocal derived
        value = 2 if truth else 1
        if assignment[variable]:
            return assignment[variable] == value
        assignment[variable] = value
        queue.append(variable)
        derived += 1
        return True

    for bit, variable in enumerate(code_group):
        assert assign(variable, bool(code >> bit & 1))
    for clause in clauses:
        if len(clause) == 1 and not assign(abs(clause[0]), clause[0] > 0):
            return "CONFLICT", derived, "initial_unit"
    for row, rhs in xors:
        if len(row) == 1 and not assign(row[0], rhs):
            return "CONFLICT", derived, "initial_xor"
    while queue:
        variable = queue.popleft()
        truth = assignment[variable] == 2
        for index, positive in cnf_occ[variable]:
            if satisfied[index]:
                continue
            if truth == positive:
                satisfied[index] = 1
            else:
                left[index] -= 1
                if left[index] == 0:
                    return "CONFLICT", derived, "cnf"
                if left[index] == 1:
                    literal = next((v for v in clauses[index]
                                    if assignment[abs(v)] == 0), None)
                    if literal is not None and not assign(abs(literal), literal > 0):
                        return "CONFLICT", derived, "cnf_assignment"
        for index in xor_occ[variable]:
            xor_left[index] -= 1
            xor_parity[index] ^= truth
            row, rhs = xors[index]
            if xor_left[index] == 0 and xor_parity[index] != rhs:
                return "CONFLICT", derived, "xor"
            if xor_left[index] == 1:
                last = next((v for v in row if assignment[v] == 0), None)
                if last is not None and not assign(last, rhs ^ xor_parity[index]):
                    return "CONFLICT", derived, "xor_assignment"
    return "OPEN", derived, None


def main(mode):
    if mode == "freeze":
        save_new(PROTOCOL, {
            "kind": "n41_sixpair_one_code_cnf_xor_propagation_v1",
            "candidate_id": None,
            "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
            "input_law": "all 40 source-valid first-slot canonical codes on one frozen ordinary public point",
            "target_count": 1,
            "one_worker": True,
            "wall_cap_seconds": 180,
            "rss_cap_bytes": 4 * 1024**3,
            "source_sha256": {"script": sha(Path(__file__)), "public_xcnf": sha(XCNF),
                              "independent_join_witness": sha(WITNESS)},
        })
        return
    protocol = json.loads(PROTOCOL.read_text())
    assert protocol["source_sha256"] == {
        "script": sha(Path(__file__)), "public_xcnf": sha(XCNF),
        "independent_join_witness": sha(WITNESS)}
    signal.alarm(protocol["wall_cap_seconds"])
    start = time.monotonic_ns()
    nvars, clauses, xors, groups = parse()
    first = groups[0]
    allowed = allowed_codes(clauses, first)
    witness = json.loads(WITNESS.read_text())
    assert witness["status"] == "PASS_INDEPENDENT_N41_SIXPAIR_PUBLIC_RELATION"
    assert witness["distinct_columns"] == 12
    first_mask = witness["pair_rows"][0]["masks"][0]
    source_bits = [i for i in range(8) if i != 5]
    witness_code = sum(((first_mask >> bit) & 1) << index
                       for index, bit in enumerate(source_bits))
    assert witness_code in allowed
    cnf_occ, xor_occ = incidence(nvars, clauses, xors)
    rows = []
    for code in allowed:
        item_start = time.monotonic_ns()
        status, assigned, reason = propagate(nvars, clauses, xors, cnf_occ,
                                             xor_occ, first, code)
        rows.append({"code": code, "status": status, "assigned_variables": assigned,
                     "conflict_reason": reason, "elapsed_ns": time.monotonic_ns()-item_start})
    signal.alarm(0)
    assert next(row for row in rows if row["code"] == witness_code)["status"] == "OPEN"
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    assert peak <= protocol["rss_cap_bytes"]
    save_new(RESULT, {"kind": "n41_sixpair_one_code_cnf_xor_propagation_result_v1",
                      "status": "PASS_BOUNDED_CODE_PROPAGATION_SCREEN",
                      "protocol_sha256": sha(PROTOCOL), "public_xcnf_sha256": sha(XCNF),
                      "witness_code": witness_code, "first_slot_code_wires": first,
                      "code_count": len(rows), "conflicts": sum(row["status"] == "CONFLICT" for row in rows),
                      "open_families": sum(row["status"] == "OPEN" for row in rows),
                      "rows": rows, "total_wall_ns": time.monotonic_ns()-start,
                      "peak_self_rss_bytes": peak})
    print(json.dumps({"status": "PASS_BOUNDED_CODE_PROPAGATION_SCREEN",
                      "conflicts": sum(row["status"] == "CONFLICT" for row in rows),
                      "witness_code": witness_code, "elapsed_seconds": (time.monotonic_ns()-start)/1e9}))


if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] in ("freeze", "run")
    main(sys.argv[1])
