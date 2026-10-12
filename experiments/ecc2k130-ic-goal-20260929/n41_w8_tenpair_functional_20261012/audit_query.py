"""Replay archived N41 functional-root public query and any SAT model."""

import hashlib
import json
from pathlib import Path

import build

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, obj):
    with path.open("x") as stream:
        json.dump(obj, stream, sort_keys=True, indent=2)
        stream.write("\n")


def freeze():
    paths = (Path(__file__), HERE / "query_result.json",
             HERE / "solver.stdout", HERE / "solver.stderr",
             HERE / "ordinary.xcnf", HERE / "protocol.json",
             HERE / "control_result.json", HERE / "audit_result.json",
             HERE / "positive_chart.json", build.INPUT, build.POSITIVE)
    save(HERE / "query_audit_protocol.json", {
        "status": "FROZEN_BEFORE_N41_FUNCTIONAL_PUBLIC_QUERY_AUDIT",
        "sources": {str(path): sha(path) for path in paths}})


def parse_model(lines):
    assignment = {}
    for line in lines:
        if line.startswith("v "):
            for word in line.split()[1:]:
                literal = int(word)
                if literal:
                    assert abs(literal) not in assignment
                    assignment[abs(literal)] = literal > 0
    return assignment


def check_formula(assignment):
    cnf = xor = 0
    with (HERE / "ordinary.xcnf").open() as stream:
        head = stream.readline().split()
        assert head[:2] == ["p", "cnf"]
        variables, rows = map(int, head[2:])
        assert set(assignment) == set(range(1, variables + 1))
        for line in stream:
            parts = line.split()
            is_xor = parts[0] == "x"
            lits = list(map(int, parts[1 if is_xor else 0:-1]))
            assert parts[-1] == "0" and lits
            values = [assignment[abs(lit)] == (lit > 0) for lit in lits]
            if is_xor:
                assert sum(values) & 1, xor
                xor += 1
            else:
                assert any(values), cnf
                cnf += 1
    assert cnf + xor == rows
    return {"variables": variables, "cnf_clauses": cnf, "native_xor_rows": xor}


def run():
    frozen = json.loads((HERE / "query_audit_protocol.json").read_text())
    assert frozen["status"] == "FROZEN_BEFORE_N41_FUNCTIONAL_PUBLIC_QUERY_AUDIT"
    for path, digest in frozen["sources"].items():
        assert sha(path) == digest, path
    receipt = json.loads((HERE / "query_result.json").read_text())
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert receipt["protocol_sha256"] == sha(HERE / "protocol.json")
    assert receipt["control_result_sha256"] == sha(HERE / "control_result.json")
    assert receipt["peak_combined_rss_bytes"] < protocol["combined_rss_cap_bytes"]
    assert receipt["solver_wall_ns"] < protocol["cap_ns"] + 2 * 10**9
    lines = (HERE / "solver.stdout").read_text(errors="replace").splitlines()
    terminals = [line for line in lines if line.startswith("s ")]
    assert (terminals[-1] if terminals else None) == receipt["terminal"]
    assert sha(HERE / "solver.stdout") == receipt["stdout_sha256"]
    assert sha(HERE / "solver.stderr") == receipt["stderr_sha256"]
    assert sum(line.startswith("c rst") for line in lines) == receipt["restart_rows"]
    output = {"status": receipt["status"],
              "protocol_sha256": sha(HERE / "query_audit_protocol.json"),
              "query_result_sha256": sha(HERE / "query_result.json"),
              "terminal": receipt["terminal"],
              "restart_rows": receipt["restart_rows"]}
    if receipt["status"] == "SAT_PENDING_GROUP_REPLAY":
        assignment = parse_model(lines)
        output["model_formula_check"] = check_formula(assignment)
        lists, targets = build.source()
        chart = json.loads((HERE / "positive_chart.json").read_text())
        circuit, wires = build.build(lists, targets, chart, False)
        assert circuit.next_var - 1 == output["model_formula_check"]["variables"]
        states = []
        for row in wires["selectors"]:
            chosen = [index for index, wire in enumerate(row) if assignment[wire]]
            assert len(chosen) == 1
            states.append(chosen[0])
        selected = [i for i, wire in enumerate(wires["flags"]) if assignment[wire]]
        assert len(selected) == 1
        fiber = selected[0]
        branches = [int(assignment[wire]) for wire in wires["branches"]]
        assert len({lists[slot][sid]["edge"] for slot, sid in zip(build.SLOTS, states)}) == 10
        point = None
        for slot, sid in zip(build.SLOTS, states):
            point = build.add(point, lists[slot][sid]["point"])
        output.update({"source_state_ids": states,
                       "branch_bits": branches, "target_fiber": fiber,
                       "raw_group_sum": list(point) if point else None,
                       "target_raw_point": list(targets[fiber]),
                       "group_match": point == targets[fiber]})
        output["status"] = ("HIT_PENDING_INDEPENDENT_SAGE" if output["group_match"]
                            else "RELAXED_MODEL_REJECTED_BY_GROUP_REPLAY")
    save(HERE / "query_audit_result.json", output)
    print(output["status"], receipt["terminal"], output.get("group_match"))


if __name__ == "__main__":
    import sys
    {"freeze": freeze, "run": run}[sys.argv[1]]()
