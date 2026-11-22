"""Nine-free-state linked N41 full-point circuit on the frozen public point."""

import hashlib
import importlib.util
import json
import os
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
FIRST = HERE.parent
GOAL = HERE.parents[1]
PARENT = GOAL / "n41_fullpoint_functional_slope_20261012"
LINKED = GOAL / "n41_n131_linked_frobenius_pair_20261012"
spec = importlib.util.spec_from_file_location("linked_fullpoint_parent", PARENT / "run.py")
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
old = parent.old
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
CAPS = {"control": 30, "public": 180}
RSS_CAP = 4 * 1024**3


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, data):
    with (HERE / name).open("x") as stream:
        json.dump(data, stream, sort_keys=True, indent=2)
        stream.write("\n")


def nonzero(circuit, bits):
    # A field-coordinate expression can contain known-zero wires. In CNF,
    # zero terminates a clause; it must never be serialized as a literal.
    if -1 in bits:
        return
    literals = [wire for wire in bits if wire > 0]
    assert literals
    circuit.clauses.append(" ".join(map(str, literals)) + " 0")


def linked_witness(lists, targets):
    audit = json.loads((LINKED / "audit_result.json").read_text())
    assert audit["status"] == "PASS_INDEPENDENT_N41_LINKED_FROBENIUS_PUBLIC_RELATION"
    states = audit["source_pairs"]
    assert len(states) == 10 and audit["source_pairs_free"] == 9
    ids = [row["state_id"] for row in states]
    assert ids[0] == ids[1]
    points = [lists[slot][sid]["point"] for slot, sid in zip(old.SLOTS, ids)]
    assert all(tuple(row["pair_point"]) == point for row, point in zip(states, points))
    edges = [lists[slot][sid]["edge"] for slot, sid in zip(old.SLOTS, ids)]
    assert edges[0] == edges[1] and len(set(edges)) == 9
    nodes = list(points)
    for left, right in old.TREE:
        assert nodes[left][0] != nodes[right][0]
        result = old.add(nodes[left], nodes[right])
        assert result is not None
        nodes.append(result)
    index = audit["raw_target_preimage_index"]
    assert nodes[-1] == targets[index]
    return {"state_ids": ids, "target_index": index,
            "point_chain": [list(point) for point in nodes],
            "target_point": list(targets[index])}


def formula(lists, targets, pin, witness):
    circuit = old.KaratsubaCircuit(old.N, [0, 3])
    selectors, nodes = [], []
    for position, slot in enumerate(old.SLOTS):
        if position == 1:
            row = selectors[0]
        else:
            row = [circuit.variable() for _ in range(140)]
            old.exactly_one(circuit, row)
        selectors.append(row)
        nodes.append((circuit.linear_element(row, [state["point"][0] for state in lists[slot]]),
                      circuit.linear_element(row, [state["point"][1] for state in lists[slot]])))
    for left in range(10):
        for right in range(left + 1, 10):
            if (left, right) == (0, 1):
                continue
            for edge in range(35):
                for a in selectors[left][4 * edge:4 * edge + 4]:
                    for b in selectors[right][4 * edge:4 * edge + 4]:
                        circuit.clauses.append(f"-{a} -{b} 0")
    slopes, outputs = [], []
    for left, right in old.TREE:
        x1, y1 = nodes[left]
        x2, y2 = nodes[right]
        denominator = circuit.add(x1, x2)
        nonzero(circuit, denominator)
        slope = circuit.mul(circuit.add(y1, y2), old.inverse(circuit, denominator))
        x3 = circuit.add(circuit.add(circuit.square(slope), slope), denominator)
        y3 = circuit.add(circuit.add(circuit.mul(slope, circuit.add(x1, x3)), x3), y1)
        slopes.append(slope)
        outputs.append((x3, y3))
        nodes.append((x3, y3))
    flags = [circuit.variable() for _ in range(4)]
    old.exactly_one(circuit, flags)
    circuit.require_zero(circuit.add(nodes[-1][0],
                                     circuit.linear_element(flags, [p[0] for p in targets])))
    circuit.require_zero(circuit.add(nodes[-1][1],
                                     circuit.linear_element(flags, [p[1] for p in targets])))
    if pin:
        for row, sid in zip(selectors, witness["state_ids"]):
            circuit.clauses.append(f"{row[sid]} 0")
        circuit.clauses.append(f"{flags[witness['target_index']]} 0")
    return circuit, {"selectors": selectors, "slopes": slopes,
                     "outputs": outputs, "flags": flags}


def search(label, formula_path, circuit, wires, lists, targets):
    cap = CAPS[label]
    stdout, stderr = HERE / f"{label}.stdout", HERE / f"{label}.stderr"
    command = [str(SOLVER), "--threads=1", f"--maxtime={cap-5}",
               "--zero-exit-status", "--verb=1", "--printsol=1", str(formula_path)]
    start, peak, stop = time.monotonic_ns(), 0, None
    with stdout.open("x") as out, stderr.open("x") as err:
        child = subprocess.Popen(command, stdout=out, stderr=err)
        worker, owner = psutil.Process(child.pid), psutil.Process(os.getpid())
        while child.poll() is None:
            try:
                peak = max(peak, owner.memory_info().rss + worker.memory_info().rss)
            except psutil.NoSuchProcess:
                break
            if peak > RSS_CAP:
                stop = "RSS_CAP"
            elif time.monotonic_ns() - start >= cap * 10**9:
                stop = "PARENT_TIME_CAP"
            if stop:
                child.kill()
                break
            time.sleep(0.025)
        code = child.wait()
    duration = time.monotonic_ns() - start
    text = stdout.read_text(errors="replace")
    terminals = [line for line in text.splitlines() if line.startswith("s ")]
    status = ("SAT" if "s SATISFIABLE" in terminals else
              "UNSAT" if "s UNSATISFIABLE" in terminals else
              "BOUNDED_UNKNOWN" if "s INDETERMINATE" in terminals else
              stop or "UNKNOWN")
    result = {"status": status, "terminal_lines": terminals, "stop": stop,
              "exit_code": code, "wall_ns_exploratory": duration,
              "peak_combined_rss_bytes_sampled": peak,
              "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr),
              "restart_rows": sum(line.startswith("c rst") for line in text.splitlines()),
              "model_check": None}
    if status == "SAT":
        parser_path = GOAL / "n41_n131_fouratom_product_anf_sat_20261012/run.py"
        spec = importlib.util.spec_from_file_location("linked_literal_parser", parser_path)
        parser = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(parser)
        model = parser.model(text, circuit.next_var - 1)
        result["model_check"] = parser.check_formula(formula_path, model)
        assert result["model_check"] == {
            "cnf_clauses_checked": len(circuit.clauses),
            "native_xor_rows_checked": len(circuit.xors)}
        def bit(wire):
            return (0 if wire == 0 else 1 if wire == -1 else
                    model[wire] if wire > 0 else 1 - model[-wire])
        ids = [[i for i, wire in enumerate(row) if model[wire]]
               for row in wires["selectors"]]
        flags = [i for i, wire in enumerate(wires["flags"]) if model[wire]]
        assert all(len(row) == 1 for row in ids) and len(flags) == 1
        ids = [row[0] for row in ids]
        assert ids[0] == ids[1]
        points = [lists[slot][sid]["point"] for slot, sid in zip(old.SLOTS, ids)]
        edges = [lists[slot][sid]["edge"] for slot, sid in zip(old.SLOTS, ids)]
        assert edges[0] == edges[1] and len(set(edges)) == 9
        nodes = list(points)
        for i, (left, right) in enumerate(old.TREE):
            point = old.add(nodes[left], nodes[right])
            assert point is not None and nodes[left][0] != nodes[right][0]
            x3, y3 = wires["outputs"][i]
            observed = (sum(bit(wire) << index for index, wire in enumerate(x3)),
                        sum(bit(wire) << index for index, wire in enumerate(y3)))
            assert point == observed
            nodes.append(point)
        assert nodes[-1] == targets[flags[0]]
        result["group_replay"] = {"selected_state_ids": ids,
                                  "raw_preimage_index": flags[0],
                                  "raw_sum": nodes[-1],
                                  "nine_distinct_edges": True,
                                  "nine_links_checked": 9}
        save(f"{label}.model.json", {"selected_state_ids": ids,
                                      "raw_preimage_index": flags[0],
                                      "raw_sum": nodes[-1]})
    save(f"{label}.json", result)
    print(label, status, duration / 1e9, flush=True)


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    sources = {"runner": HERE / "run.py", "input": old.INPUT,
               "first_failure_audit": FIRST / "failure_audit_result.json",
               "v2_control_formula": FIRST / "v2/control.xcnf",
               "v2_control_stdout": FIRST / "v2/control.stdout",
               "v2_runner": FIRST / "v2/run.py",
               "linked_audit": LINKED / "audit_result.json",
               "parent_runner": PARENT / "run.py",
               "old_builder": GOAL / "n41_w8_tenpair_functional_20261012/build.py",
               "inverse": GOAL / "functional_inverse_circuit.py",
               "karatsuba": GOAL.parents[1] / "experiments/koblitz-polynomial-w-pair-20260925/karatsuba_circuit.py",
               "circuit": GOAL.parents[1] / "experiments/koblitz-s5-invariant-20260924/circuit_sat.py",
               "solver": SOLVER}
    assert protocol["status"] == "FROZEN_BEFORE_N41_LINKED_FUNCTIONAL_CONTROL_AND_PUBLIC"
    assert protocol["sha256"] == {key: sha(path) for key, path in sources.items()}
    assert protocol["control_cap_s"] == 30 and protocol["public_cap_s"] == 180
    assert protocol["combined_rss_cap_bytes"] == RSS_CAP
    lists, targets = old.source()
    witness = linked_witness(lists, targets)
    for label, pin in (("control", True), ("public", False)):
        start = time.monotonic_ns()
        circuit, wires = formula(lists, targets, pin, witness)
        built = time.monotonic_ns()
        checked = parent.positive_assignment(circuit, wires, witness)
        audited = time.monotonic_ns()
        formula_path = HERE / f"{label}.xcnf"
        circuit.write(formula_path)
        written = time.monotonic_ns()
        save(f"{label}.build.json", {
            "variables": circuit.next_var - 1,
            "cnf_clauses": len(circuit.clauses),
            "native_xor_rows": len(circuit.xors),
            "and_gates": circuit.and_count,
            "bytes": formula_path.stat().st_size,
            "sha256": sha(formula_path),
            "positive_assignment_check": checked,
            "build_ns_exploratory": built-start,
            "assignment_check_ns_exploratory": audited-built,
            "serialization_ns_exploratory": written-audited})
        search(label, formula_path, circuit, wires, lists, targets)


if __name__ == "__main__":
    main()
