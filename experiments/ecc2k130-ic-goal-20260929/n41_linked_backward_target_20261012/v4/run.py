"""Exact target-backward terminal chain on the linked N41 public source."""

import hashlib
import importlib.util
import json
import os
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
GOAL = HERE.parents[1]
UP = GOAL / "n41_linked_functional_fullpoint_20261012"
spec = importlib.util.spec_from_file_location("linked_parent", UP / "run.py")
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
old = parent.old
SOLVER = parent.SOLVER
RSS_CAP = 4 * 1024**3


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, obj):
    with (HERE / path).open("x") as out:
        json.dump(obj, out, sort_keys=True, indent=2)
        out.write("\n")


def negate(circuit, point):
    return point[0], circuit.add(point[0], point[1])


def add(circuit, left, right):
    x1, y1 = left
    x2, y2 = right
    denominator = circuit.add(x1, x2)
    literals = [bit for bit in denominator if bit != 0]
    if -1 not in literals:
        assert literals
        circuit.clauses.append(" ".join(map(str, literals)) + " 0")
    slope = circuit.mul(circuit.add(y1, y2), old.inverse(circuit, denominator))
    x3 = circuit.add(circuit.add(circuit.square(slope), slope), denominator)
    y3 = circuit.add(circuit.add(circuit.mul(slope, circuit.add(x1, x3)), x3), y1)
    return slope, (x3, y3)


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
        nodes.append((circuit.linear_element(row, [s["point"][0] for s in lists[slot]]),
                      circuit.linear_element(row, [s["point"][1] for s in lists[slot]])))
    for left in range(10):
        for right in range(left + 1, 10):
            if (left, right) == (0, 1):
                continue
            for edge in range(35):
                for a in selectors[left][4 * edge:4 * edge + 4]:
                    for b in selectors[right][4 * edge:4 * edge + 4]:
                        circuit.clauses.append(f"-{a} -{b} 0")
    slopes, outputs = [], []
    for left, right in old.TREE[:7]:
        slope, output = add(circuit, nodes[left], nodes[right])
        slopes.append(slope)
        outputs.append(output)
        nodes.append(output)
    flags = [circuit.variable() for _ in range(4)]
    old.exactly_one(circuit, flags)
    target = (circuit.linear_element(flags, [p[0] for p in targets]),
              circuit.linear_element(flags, [p[1] for p in targets]))
    slope, residual1 = add(circuit, target, negate(circuit, nodes[9]))
    slopes.append(slope)
    outputs.append(residual1)
    slope, residual2 = add(circuit, residual1, negate(circuit, nodes[8]))
    slopes.append(slope)
    outputs.append(residual2)
    circuit.require_zero(circuit.add(residual2[0], nodes[16][0]))
    circuit.require_zero(circuit.add(residual2[1], nodes[16][1]))
    if pin:
        for row, sid in zip(selectors, witness["state_ids"]):
            circuit.clauses.append(f"{row[sid]} 0")
        circuit.clauses.append(f"{flags[witness['target_index']]} 0")
    return circuit, {"selectors": selectors, "slopes": slopes,
                     "outputs": outputs, "flags": flags}


def replay_values(lists, targets, ids, index):
    assert ids[0] == ids[1]
    edges = [lists[slot][sid]["edge"] for slot, sid in zip(old.SLOTS, ids)]
    assert len(set(edges)) == 9
    nodes = [lists[slot][sid]["point"] for slot, sid in zip(old.SLOTS, ids)]
    slopes, outputs = [], []
    for left, right in old.TREE[:7]:
        p, q = nodes[left], nodes[right]
        assert p[0] != q[0]
        slopes.append(old.mul(p[1] ^ q[1], old.inv(p[0] ^ q[0])))
        output = old.add(p, q)
        assert output is not None
        outputs.append(output)
        nodes.append(output)
    neg = lambda p: (p[0], p[0] ^ p[1])
    left, right = targets[index], neg(nodes[9])
    for next_point in (None, neg(nodes[8])):
        assert left[0] != right[0]
        slopes.append(old.mul(left[1] ^ right[1], old.inv(left[0] ^ right[0])))
        output = old.add(left, right)
        assert output is not None
        outputs.append(output)
        if next_point is None:
            left, right = output, neg(nodes[8])
    assert outputs[-1] == nodes[16]
    assert old.add(old.add(nodes[16], nodes[8]), nodes[9]) == targets[index]
    return slopes, outputs


def selected_model(text, circuit, formula_path, wires, lists, targets):
    spec = importlib.util.spec_from_file_location("model_parser", GOAL / "n41_n131_fouratom_product_anf_sat_20261012/run.py")
    parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser)
    model = parser.model(text, circuit.next_var - 1)
    counts = parser.check_formula(formula_path, model)
    assert counts == {"cnf_clauses_checked": len(circuit.clauses),
                      "native_xor_rows_checked": len(circuit.xors)}
    ids = [[i for i, bit in enumerate(row) if model[bit]] for row in wires["selectors"]]
    flags = [i for i, bit in enumerate(wires["flags"]) if model[bit]]
    assert all(len(row) == 1 for row in ids) and len(flags) == 1
    ids = [row[0] for row in ids]
    slopes, outputs = replay_values(lists, targets, ids, flags[0])
    for bits, value in zip(wires["slopes"], slopes):
        assert sum((model[bit] if bit > 0 else int(bit == -1)) << i for i, bit in enumerate(bits)) == value
    for pair, point in zip(wires["outputs"], outputs):
        for bits, value in zip(pair, point):
            assert sum((model[bit] if bit > 0 else int(bit == -1)) << i for i, bit in enumerate(bits)) == value
    return {"selected_state_ids": ids, "raw_preimage_index": flags[0],
            "raw_target": list(targets[flags[0]]), "group_links_checked": 9,
            "formula_check": counts}


def run(label, circuit, wires, lists, targets, cap):
    path = HERE / f"{label}.xcnf"
    t0 = time.monotonic_ns()
    circuit.write(path)
    t1 = time.monotonic_ns()
    outpath, errpath = HERE / f"{label}.stdout", HERE / f"{label}.stderr"
    command = [str(SOLVER), "--threads=1", f"--maxtime={cap-5}",
               "--zero-exit-status", "--verb=1", "--printsol=1", str(path)]
    peak, stop = 0, None
    with outpath.open("x") as out, errpath.open("x") as err:
        child = subprocess.Popen(command, stdout=out, stderr=err)
        owner, worker = psutil.Process(os.getpid()), psutil.Process(child.pid)
        t2 = time.monotonic_ns()
        while child.poll() is None:
            try:
                peak = max(peak, owner.memory_info().rss + worker.memory_info().rss)
            except psutil.NoSuchProcess:
                break
            if peak > RSS_CAP:
                stop = "RSS_CAP"
            elif time.monotonic_ns() - t2 >= cap * 10**9:
                stop = "PARENT_TIME_CAP"
            if stop:
                child.kill()
                break
            time.sleep(0.025)
        code = child.wait()
        t3 = time.monotonic_ns()
    raw = outpath.read_text(errors="replace")
    terminals = [line for line in raw.splitlines() if line.startswith("s ")]
    status = ("SAT" if "s SATISFIABLE" in terminals else
              "UNSAT" if "s UNSATISFIABLE" in terminals else
              "BOUNDED_UNKNOWN" if "s INDETERMINATE" in terminals else
              stop or "UNKNOWN")
    replay = selected_model(raw, circuit, path, wires, lists, targets) if status == "SAT" else None
    t4 = time.monotonic_ns()
    result = {"status": status, "stop": stop, "terminal_lines": terminals,
              "exit_code": code, "peak_combined_rss_bytes_sampled": peak,
              "solver_wall_ns_exploratory": t3-t2,
              "formula_serialization_ns": t1-t0, "model_replay_ns": t4-t3,
              "xcnf_sha256": sha(path), "xcnf_bytes": path.stat().st_size,
              "stdout_sha256": sha(outpath), "stderr_sha256": sha(errpath),
              "variables": circuit.next_var-1, "clauses": len(circuit.clauses),
              "xor_rows": len(circuit.xors), "and_gates": circuit.and_count,
              "restart_rows": sum(s.startswith("c rst") for s in raw.splitlines()),
              "group_replay": replay}
    save(f"{label}.json", result)
    print(label, status, (t3-t2)/1e9, flush=True)
    return result


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    sources = {"runner": HERE / "run.py", "input": old.INPUT,
               "parent_runner": UP / "run.py", "linked_audit": parent.LINKED / "audit_result.json",
               "solver": SOLVER}
    assert protocol["status"] == "FROZEN_BEFORE_CONTROL_AND_PUBLIC"
    assert protocol["sha256"] == {k: sha(v) for k, v in sources.items()}
    assert protocol["public_cap_seconds"] == 180 and protocol["control_cap_seconds"] == 30
    assert protocol["combined_rss_cap_bytes"] == RSS_CAP
    lists, targets = old.source()
    witness = parent.linked_witness(lists, targets)
    replay_values(lists, targets, witness["state_ids"], witness["target_index"])
    t0 = time.monotonic_ns()
    control, cw = formula(lists, targets, True, witness)
    t1 = time.monotonic_ns()
    public, pw = formula(lists, targets, False, witness)
    t2 = time.monotonic_ns()
    save("build.json", {"control_build_ns": t1-t0, "public_build_ns": t2-t1})
    control_result = run("control", control, cw, lists, targets, 30)
    assert control_result["status"] == "SAT"
    result = run("public", public, pw, lists, targets, 180)
    save("result.json", {"status": result["status"], "control": control_result["status"],
                         "public": result["status"], "protocol_sha256": sha(HERE / "protocol.json"),
                         "target_dependent_total_ns": (t2-t1)+result["formula_serialization_ns"]+
                                                      result["solver_wall_ns_exploratory"]+
                                                      result["model_replay_ns"]})


if __name__ == "__main__":
    main()
