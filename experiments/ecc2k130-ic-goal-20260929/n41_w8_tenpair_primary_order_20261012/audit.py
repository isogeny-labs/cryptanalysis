"""Independent formula parser and raw-group replay for ordered N41 search."""

import hashlib
import json
from pathlib import Path

import experiment

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_formula(path, assignment):
    cnf = xor = 0
    with path.open() as stream:
        head = stream.readline().split()
        assert head == ["p", "cnf", "289065", "731771"]
        assert len(assignment) == 289065
        for line in stream:
            parts = line.split()
            is_xor = parts[0] == "x"
            literals = map(int, parts[1:-1] if is_xor else parts[:-1])
            assert parts[-1] == "0"
            if is_xor:
                assert sum(assignment[abs(lit)] == (lit > 0) for lit in literals) & 1, xor
                xor += 1
            else:
                assert any(assignment[abs(lit)] == (lit > 0) for lit in literals), cnf
                cnf += 1
    assert (cnf, xor) == (604526, 127245)
    return {"cnf_clauses": cnf, "native_xor_rows": xor}


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    receipt = json.loads((HERE / "query_result.json").read_text())
    assert receipt["protocol_sha256"] == sha(HERE / "protocol.json")
    for path, digest in protocol["sources"].items():
        assert sha(path) == digest, path
    assert receipt["stdout_sha256"] == sha(HERE / "solver.stdout")
    assert receipt["stderr_sha256"] == sha(HERE / "solver.stderr")
    lines = (HERE / "solver.stdout").read_text(errors="replace").splitlines()
    terminal = [line for line in lines if line.startswith("s ")]
    assert (terminal[-1] if terminal else None) == receipt["terminal"]
    assert sum(line.startswith("c rst") for line in lines) == receipt["restart_rows"]
    assert receipt["peak_combined_rss_bytes"] <= protocol["combined_rss_cap_bytes"]
    result = {"status": receipt["status"], "query_result_sha256": sha(HERE / "query_result.json"),
              "protocol_sha256": sha(HERE / "protocol.json"),
              "audit_source_sha256": sha(__file__), "terminal": receipt["terminal"]}
    if receipt["status"] == "SAT_PENDING_GROUP_REPLAY":
        assignment = {}
        for line in lines:
            if line.startswith("v "):
                for word in line.split()[1:]:
                    lit = int(word)
                    if lit:
                        assert abs(lit) not in assignment
                        assignment[abs(lit)] = lit > 0
        result["formula_check"] = check_formula(HERE / "ordered.xcnf", assignment)
        lists, targets = experiment.prior_build.source()
        chart = json.loads((experiment.SOURCE / "positive_chart.json").read_text())
        _, wires = experiment.prior_build.build(lists, targets, chart, False)
        ordered = wires["branches"] + [v for row in wires["selectors"] for v in row] + wires["flags"]
        selected = set(ordered)
        perm = ordered + [v for v in range(1, 289066) if v not in selected]
        old_to_new = [0] * 289066
        for new, old in enumerate(perm, 1):
            old_to_new[old] = new
        source_ids = []
        for row in wires["selectors"]:
            hits = [i for i, old in enumerate(row) if assignment[old_to_new[old]]]
            assert len(hits) == 1
            source_ids.append(hits[0])
        fibers = [i for i, old in enumerate(wires["flags"]) if assignment[old_to_new[old]]]
        assert len(fibers) == 1
        fiber = fibers[0]
        branches = [int(assignment[old_to_new[old]]) for old in wires["branches"]]
        edges = [lists[slot][sid]["edge"] for slot, sid in zip(experiment.prior_build.SLOTS, source_ids)]
        assert len(set(edges)) == 10
        point = None
        for slot, sid in zip(experiment.prior_build.SLOTS, source_ids):
            point = experiment.prior_build.add(point, lists[slot][sid]["point"])
        assert point == targets[fiber]
        result.update({"status": "PASS_RAW_GROUP_REPLAY_PENDING_SAGE",
                       "source_state_ids": source_ids, "branch_bits": branches,
                       "raw_target_fiber": fiber, "raw_group_sum": list(point)})
    with (HERE / "audit_result.json").open("x") as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write("\n")
    print(result["status"])


if __name__ == "__main__":
    main()
