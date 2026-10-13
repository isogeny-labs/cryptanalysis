"""Read-only replay of the functional-slope N41 formula and solver evidence."""

import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PARENT = GOAL / "n41_fullpoint_balanced_sat_20261012"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = load("functional_slope_runner", HERE / "run.py")
ind = load("independent_fullpoint_curve", PARENT / "verify.py")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def model(stdout, variable_count):
    bits = {}
    for line in stdout.splitlines():
        if line.startswith("v "):
            for word in line[2:].split():
                literal = int(word)
                if literal:
                    assert abs(literal) not in bits
                    bits[abs(literal)] = literal > 0
    assert len(bits) == variable_count
    return bits


def literal_check(path, bits):
    clauses = xors = 0
    with path.open() as stream:
        for line in stream:
            if line.startswith("p "):
                continue
            is_xor = line.startswith("x ")
            words = line.split()
            literals = list(map(int, words[1:-1] if is_xor else words[:-1]))
            assert words[-1] == "0"
            values = [bits[abs(v)] != (v < 0) for v in literals]
            if is_xor:
                assert sum(values) & 1
                xors += 1
            else:
                assert any(values)
                clauses += 1
    return {"cnf_clauses_checked": clauses, "native_xor_rows_checked": xors}


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    standard = {"runner": HERE / "run.py", "input": ind.INPUT,
                "positive": ind.POSITIVE, "old_builder": runner.old.__file__,
                "solver": runner.parent.SOLVER}
    assert {k: sha(v) for k, v in standard.items()} == protocol["sha256"]
    extra = {"parent_runner": PARENT / "run.py",
             "inverse": GOAL / "functional_inverse_circuit.py",
             "karatsuba": GOAL.parents[1] / "experiments/koblitz-polynomial-w-pair-20260925/karatsuba_circuit.py",
             "circuit": GOAL.parents[1] / "experiments/koblitz-s5-invariant-20260924/circuit_sat.py"}
    assert {k: sha(v) for k, v in extra.items()} == protocol["extra_sha256"]
    source, targets = ind.source()
    lists, runner_targets = runner.old.source()
    assert targets == runner_targets
    witness = runner.old.positive_chart(lists, targets)
    profiles = {}
    for label in ("control", "public"):
        build = json.loads((HERE / f"{label}.build.json").read_text())
        receipt = json.loads((HERE / f"{label}.json").read_text())
        formula = HERE / f"{label}.xcnf"
        assert formula.stat().st_size == build["bytes"] and sha(formula) == build["sha256"]
        lines = formula.read_text().splitlines()
        assert lines[0] == f'p cnf {build["variables"]} {build["cnf_clauses"] + build["native_xor_rows"]}'
        assert sum(row.startswith("x ") for row in lines[1:]) == build["native_xor_rows"]
        assert len(lines) - 1 - build["native_xor_rows"] == build["cnf_clauses"]
        assert sha(HERE / f"{label}.stdout") == receipt["stdout_sha256"]
        assert sha(HERE / f"{label}.stderr") == receipt["stderr_sha256"]
        text = (HERE / f"{label}.stdout").read_text(errors="replace")
        assert [row for row in text.splitlines() if row.startswith("s ")] == receipt["terminal_lines"]
        assert sum(row.startswith("c rst") for row in text.splitlines()) == receipt["restart_rows"]
        assert receipt["peak_combined_rss_bytes_sampled"] < protocol["combined_rss_cap_bytes"]
        if label == "control":
            assert receipt["status"] == "SAT" and receipt["terminal_lines"] == ["s SATISFIABLE"]
            bits = model(text, build["variables"])
            assert literal_check(formula, bits) == receipt["model_check"] == {
                "cnf_clauses_checked": build["cnf_clauses"],
                "native_xor_rows_checked": build["native_xor_rows"]}
            circuit, wires = runner.formula(lists, targets, True, witness)
            assert circuit.next_var - 1 == build["variables"]
            with tempfile.NamedTemporaryFile(dir="/private/tmp", suffix=".xcnf") as temporary:
                circuit.write(Path(temporary.name))
                assert sha(temporary.name) == build["sha256"]
            ids = [[i for i, wire in enumerate(row) if bits[wire]]
                   for row in wires["selectors"]]
            flags = [i for i, wire in enumerate(wires["flags"]) if bits[wire]]
            assert all(len(row) == 1 for row in ids) and len(flags) == 1
            ids = [row[0] for row in ids]
            assert ids == receipt["group_replay"]["selected_state_ids"]
            assert flags == [receipt["group_replay"]["raw_preimage_index"]]
            points = [source[slot][sid][1] for slot, sid in zip(ind.SLOTS, ids)]
            assert len({source[slot][sid][0] for slot, sid in zip(ind.SLOTS, ids)}) == 10
            nodes = list(points)
            for left, right in ind.TREE:
                nodes.append(ind.add(nodes[left], nodes[right]))
            assert nodes[-1] == targets[flags[0]] == tuple(receipt["group_replay"]["raw_sum"])
            assert receipt["exit_code"] == 0 and receipt["stop"] is None
        else:
            assert receipt["status"] == receipt["stop"] == "PARENT_TIME_CAP"
            assert receipt["terminal_lines"] == [] and receipt["exit_code"] == -9
            assert 180 <= receipt["wall_ns_exploratory"] / 1e9 < 181
        profiles[label] = {"variables": build["variables"], "clauses": build["cnf_clauses"],
                           "xor_rows": build["native_xor_rows"], "status": receipt["status"]}
    control = (HERE / "control.xcnf").read_text().splitlines()
    public = (HERE / "public.xcnf").read_text().splitlines()
    public_clauses = profiles["public"]["clauses"]
    assert control[1:1 + public_clauses] == public[1:1 + public_clauses]
    units = control[1 + public_clauses:1 + public_clauses + 11]
    assert len(units) == 11 and all(len(row.split()) == 2 for row in units)
    assert control[1 + public_clauses + 11:] == public[1 + public_clauses:]
    output = {"status": "PASS_FUNCTIONAL_SLOPE_N41_CONTROL_AND_PUBLIC_ARCHIVE",
              "profiles": profiles, "control_group_links_replayed": 9,
              "ten_distinct_edges": True, "verifier_sha256": sha(HERE / "verify.py")}
    path = HERE / "audit.json"
    if path.exists():
        assert json.loads(path.read_text()) == output
    else:
        path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(output["status"])


if __name__ == "__main__":
    main()
