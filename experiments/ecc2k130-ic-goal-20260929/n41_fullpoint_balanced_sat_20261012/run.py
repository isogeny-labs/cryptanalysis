"""Full-point balanced-tree SAT gate on the frozen N41 public relation."""

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
UP = GOAL / "n41_w8_tenpair_functional_20261012"
sys.path.insert(0, str(UP))
import build as old  # noqa: E402

sys.path.insert(0, str(GOAL / "n131_w18_cubic_correct_target_20261011"))
import run as check  # noqa: E402

SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
CAPS = {"control": 30, "public": 180}
RSS_CAP = 4 * 1024 ** 3


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, data):
    with (HERE / name).open("x") as out:
        json.dump(data, out, indent=2, sort_keys=True)
        out.write("\n")


def nonzero(circuit, word):
    circuit.clauses.append(" ".join(map(str, word)) + " 0")


def formula(lists, targets, pin, witness):
    circuit = old.KaratsubaCircuit(old.N, [0, 3])
    selectors = []
    nodes = []
    for slot in old.SLOTS:
        wires = [circuit.variable() for _ in range(140)]
        old.exactly_one(circuit, wires)
        selectors.append(wires)
        nodes.append((circuit.linear_element(wires, [row["point"][0] for row in lists[slot]]),
                      circuit.linear_element(wires, [row["point"][1] for row in lists[slot]])))
    for left in range(10):
        for right in range(left + 1, 10):
            for edge in range(35):
                for a in selectors[left][4 * edge:4 * edge + 4]:
                    for b in selectors[right][4 * edge:4 * edge + 4]:
                        circuit.clauses.append(f"-{a} -{b} 0")
    slopes = []
    outputs = []
    for left, right in old.TREE:
        x1, y1 = nodes[left]
        x2, y2 = nodes[right]
        slope = [circuit.variable() for _ in range(old.N)]
        x3 = [circuit.variable() for _ in range(old.N)]
        y3 = [circuit.variable() for _ in range(old.N)]
        denominator = circuit.add(x1, x2)
        nonzero(circuit, denominator)
        circuit.require_zero(circuit.add(circuit.mul(slope, denominator),
                                         circuit.add(y1, y2)))
        circuit.require_zero(circuit.add(circuit.add(x3, circuit.square(slope)),
                                         circuit.add(slope, denominator)))
        circuit.require_zero(circuit.add(circuit.add(y3, circuit.mul(slope, circuit.add(x1, x3))),
                                         circuit.add(x3, y1)))
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


def positive_assignment(circuit, wires, witness):
    initial = {}
    for row, sid in zip(wires["selectors"], witness["state_ids"]):
        initial.update({wire: int(index == sid) for index, wire in enumerate(row)})
    points = [tuple(p) for p in witness["point_chain"]]
    for i, (left, right) in enumerate(old.TREE):
        x1, y1 = points[left]
        x2, y2 = points[right]
        assert x1 != x2
        slope = old.mul(y1 ^ y2, old.inv(x1 ^ x2))
        x3, y3 = points[10 + i]
        assert old.square(slope) ^ slope ^ x1 ^ x2 == x3
        assert old.mul(slope, x1 ^ x3) ^ x3 ^ y1 == y3
        for bits, value in ((wires["slopes"][i], slope),
                            (wires["outputs"][i][0], x3),
                            (wires["outputs"][i][1], y3)):
            initial.update({wire: value >> bit & 1 for bit, wire in enumerate(bits)})
    initial.update({wire: int(i == witness["target_index"])
                    for i, wire in enumerate(wires["flags"])})
    values = check.complete_assignment(circuit, initial)
    return check.check_assignment(circuit, values)


def search(label, formula_path, variables, clauses, xors, wires, lists, targets):
    cap = CAPS[label]
    stdout = HERE / f"{label}.stdout"
    stderr = HERE / f"{label}.stderr"
    command = [str(SOLVER), "--threads=1", f"--maxtime={cap-5}",
               "--zero-exit-status", "--verb=1", "--printsol=1", str(formula_path)]
    start = time.monotonic_ns()
    peak = 0
    stop = None
    with stdout.open("x") as out, stderr.open("x") as err:
        child = subprocess.Popen(command, stdout=out, stderr=err)
        parent_proc = psutil.Process(os.getpid())
        worker = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak = max(peak, parent_proc.memory_info().rss + worker.memory_info().rss)
            except psutil.NoSuchProcess:
                break
            if peak > RSS_CAP:
                stop = "RSS_CAP"
            elif (time.monotonic_ns() - start) / 1e9 > cap:
                stop = "PARENT_TIME_CAP"
            if stop:
                child.kill()
                break
            time.sleep(0.025)
        child.wait()
    duration = time.monotonic_ns() - start
    log = stdout.read_text(errors="replace")
    terminals = [line for line in log.splitlines() if line.startswith("s ")]
    status = ("SAT" if "s SATISFIABLE" in terminals else
              "UNSAT" if "s UNSATISFIABLE" in terminals else
              "BOUNDED_UNKNOWN" if "s INDETERMINATE" in terminals else
              stop or "UNKNOWN")
    result = {"status": status, "terminal_lines": terminals, "stop": stop,
              "command": command, "exit_code": child.returncode,
              "wall_ns_exploratory": duration, "peak_combined_rss_bytes_sampled": peak,
              "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr),
              "restart_rows": sum(line.startswith("c rst") for line in log.splitlines()),
              "model_check": None}
    if status == "SAT":
        import importlib.util
        path = GOAL / "n41_n131_fouratom_product_anf_sat_20261012/run.py"
        spec = importlib.util.spec_from_file_location("literal_parser", path)
        parser = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(parser)
        model = parser.model(log, variables)
        result["model_check"] = parser.check_formula(formula_path, model)
        assert result["model_check"] == {"cnf_clauses_checked": clauses,
                                          "native_xor_rows_checked": xors}
        ids = [[i for i, wire in enumerate(row) if model[wire]]
               for row in wires["selectors"]]
        flags = [i for i, wire in enumerate(wires["flags"]) if model[wire]]
        assert all(len(row) == 1 for row in ids) and len(flags) == 1
        ids = [row[0] for row in ids]
        points = [lists[slot][sid]["point"] for slot, sid in zip(old.SLOTS, ids)]
        assert len({lists[slot][sid]["edge"] for slot, sid in zip(old.SLOTS, ids)}) == 10
        nodes = list(points)
        for i, (left, right) in enumerate(old.TREE):
            point = old.add(nodes[left], nodes[right])
            assert point is not None and nodes[left][0] != nodes[right][0]
            x3, y3 = wires["outputs"][i]
            encoded = (sum(model[wire] << bit for bit, wire in enumerate(x3)),
                       sum(model[wire] << bit for bit, wire in enumerate(y3)))
            assert point == encoded
            nodes.append(point)
        assert nodes[-1] == targets[flags[0]]
        result["group_replay"] = {"selected_state_ids": ids,
                                  "raw_preimage_index": flags[0],
                                  "raw_sum": nodes[-1],
                                  "ten_distinct_edges": True,
                                  "nine_links_checked": 9}
        save(f"{label}.model.json", {"variable_count": variables,
                                      "selected_state_ids": ids,
                                      "raw_preimage_index": flags[0],
                                      "assignment_sha256": hashlib.sha256(log.encode()).hexdigest()})
    save(f"{label}.json", result)
    print(label, status, duration / 1e9, flush=True)
    return result


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    sources = {"runner": HERE / "run.py", "input": old.INPUT,
               "positive": old.POSITIVE, "old_builder": UP / "build.py", "solver": SOLVER}
    assert {key: sha(path) for key, path in sources.items()} == protocol["sha256"]
    lists, targets = old.source()
    witness = old.positive_chart(lists, targets)
    assert witness["target_point"] == list(targets[witness["target_index"]])
    for label, pin in (("control", True), ("public", False)):
        start = time.monotonic_ns()
        circuit, wires = formula(lists, targets, pin, witness)
        built = time.monotonic_ns()
        checked = positive_assignment(circuit, wires, witness)
        audited = time.monotonic_ns()
        formula_path = HERE / f"{label}.xcnf"
        circuit.write(formula_path)
        written = time.monotonic_ns()
        profile = {"variables": circuit.next_var - 1,
                   "cnf_clauses": len(circuit.clauses),
                   "native_xor_rows": len(circuit.xors),
                   "and_gates": circuit.and_count,
                   "bytes": formula_path.stat().st_size,
                   "sha256": sha(formula_path),
                   "positive_assignment_check": checked,
                   "build_ns_exploratory": built - start,
                   "assignment_check_ns_exploratory": audited - built,
                   "serialization_ns_exploratory": written - audited}
        save(f"{label}.build.json", profile)
        search(label, formula_path, profile["variables"],
               profile["cnf_clauses"], profile["native_xor_rows"],
               wires, lists, targets)


if __name__ == "__main__":
    main()
