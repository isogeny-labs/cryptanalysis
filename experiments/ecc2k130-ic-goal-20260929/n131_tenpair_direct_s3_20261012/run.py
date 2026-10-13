"""Compare direct S3 equations with the archived half-trace upper tree."""
import hashlib
import inspect
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PARENT = ROOT / "n131_w18_tenpair_binary_frob_20261012"
sys.path.insert(0, str(PARENT))
import ten  # noqa: E402

SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
CAP = 60
RSS_CAP = 4 * 1024 ** 3
OLD = '''        triple = algebra.mul(algebra.mul(left, right), output)
        total = algebra.add(left, right, output)
        ht = circuit.linear_element(total.bits(), ht_basis)
        circuit.require_zero(algebra.add(
            triple, algebra.from_bits(ht),
            algebra.expression(((branches[index], 1),))).bits())
        circuit.require_zero([circuit.xor(
            wire for wire, bit in zip(total.bits(), trace_basis) if bit)])
'''
NEW = '''        triple = algebra.mul(algebra.mul(left, right), output)
        total = algebra.add(left, right, output)
        circuit.require_zero(algebra.add(
            algebra.square(triple), triple, algebra.square(total)).bits())
'''


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def direct_build():
    source = inspect.getsource(ten.build)
    assert source.count(OLD) == 1
    assert source.count("    branches = [circuit.variable() for _ in TREE]") == 1
    source = source.replace(OLD, NEW).replace(
        "    branches = [circuit.variable() for _ in TREE]", "    branches = []")
    namespace = dict(ten.__dict__)
    exec(compile(source, str(HERE / "generated_direct_build.py"), "exec"), namespace)
    return namespace["build"]


def input_data():
    chain = json.loads((PARENT / "control_fixture.json").read_text())
    prior = json.loads((ten.NINE / "control_fixture.json").read_text())
    points = ten.witness_points(prior) + [tuple(chain["last_pair_point"])]
    nodes = list(points)
    intermediates = []
    for left, right in ten.TREE:
        point = ten.independent.point_add(nodes[left], nodes[right])
        assert point is not None and point[0] not in (0, 1)
        nodes.append(point)
        if len(intermediates) < 8:
            intermediates.append(ten.independent.inverse(point[0]))
    assert nodes[-1] == tuple(chain["raw_target"])
    rows = ten.orbit9.orbit_rows(ten.orbit9.constructed_preimages(chain["raw_target"]))
    _, root, bdd_nodes = ten.base.source_domain()
    return chain, rows, root, bdd_nodes, intermediates, nodes


def bind(bits, value, initial):
    initial.update({wire: value >> bit & 1 for bit, wire in enumerate(bits)})


def constructed_check(circuit, wires, chain, intermediates, points):
    initial = {}
    output_units = []
    selector_units = []
    for item in chain["selected"]:
        slot = item["slot"]
        code = ten.pair.selector_code(item["masks"][0])
        reciprocal = ten.base.standard_reciprocal(item["unrotated_pair_output_z"])
        bind(wires["selectors"][slot], code, initial)
        bind(wires["outputs"][slot], reciprocal, initial)
        selector_units += [wire if code >> bit & 1 else -wire
                           for bit, wire in enumerate(wires["selectors"][slot])]
        output_units += [wire if reciprocal >> bit & 1 else -wire
                         for bit, wire in enumerate(wires["outputs"][slot])]
        for side, mask in enumerate(item["masks"]):
            coordinate = ten.pair.coordinate(mask)
            inverse = ten.base.inverse(coordinate)
            assert ten.pair.gf_mul(coordinate, inverse) == 1
            assert ten.base.trace(inverse) == 0
            bind(wires["inverse_witnesses"][slot][side], inverse, initial)
    for bits, value in zip(wires["intermediates"], intermediates):
        bind(bits, value, initial)
    for wire in wires["fiber_bits"] + wires["rotation_bits"]:
        initial[wire] = 0
    values = ten.base.complete_assignment(circuit, initial)
    checked = ten.base.check_assignment(circuit, values)
    # Independent field arithmetic for all nine S3 links.
    for index, (left, right) in enumerate(ten.TREE):
        a = ten.independent.inverse(points[left][0])
        b = ten.independent.inverse(points[right][0])
        c = ten.independent.inverse(points[10 + index][0])
        triple = ten.pair.gf_mul(ten.pair.gf_mul(a, b), c)
        total = a ^ b ^ c
        assert ten.pair.gf_square(triple) ^ triple ^ ten.pair.gf_square(total) == 0
    target_units = [-wire for wire in wires["fiber_bits"] + wires["rotation_bits"]]
    return checked, {"target": target_units, "outputs": output_units,
                     "selectors": selector_units}


def pinned(source, units, destination):
    header, body = source.read_bytes().split(b"\n", 1)
    words = header.split()
    assert words[:2] == [b"p", b"cnf"]
    with destination.open("xb") as out:
        out.write(("p cnf %d %d\n" % (int(words[2]), int(words[3]) + len(units))).encode())
        out.write(body)
        for literal in units:
            out.write(("%d 0\n" % literal).encode())
    return {"bytes": destination.stat().st_size, "sha256": sha(destination),
            "unit_clauses": len(units)}


def run_arm(label, original, units, variable_count, clause_count, xor_count):
    form = HERE / (label + ".xcnf")
    profile = pinned(original, units, form)
    command = [str(SOLVER), "--threads=1", "--maxtime=55",
               "--zero-exit-status", "--verb=1", "--printsol=1", str(form)]
    stdout_path = HERE / (label + ".stdout.txt")
    stderr_path = HERE / (label + ".stderr.txt")
    start = time.monotonic_ns()
    peak = 0
    stop = None
    parent = psutil.Process(os.getpid())
    with stdout_path.open("x") as out, stderr_path.open("x") as err:
        child = subprocess.Popen(command, stdout=out, stderr=err)
        process = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak = max(peak, parent.memory_info().rss + process.memory_info().rss)
            except psutil.NoSuchProcess:
                break
            if peak > RSS_CAP:
                stop = "RSS_CAP"
            elif (time.monotonic_ns() - start) / 1e9 > CAP:
                stop = "PARENT_TIME_CAP"
            if stop:
                child.kill()
                break
            time.sleep(0.025)
        child.wait()
    ended = time.monotonic_ns()
    stdout = stdout_path.read_text(errors="replace")
    terminals = [line for line in stdout.splitlines() if line.startswith("s ")]
    status = ("SAT" if "s SATISFIABLE" in terminals else
              "UNSAT" if "s UNSATISFIABLE" in terminals else
              "BOUNDED_UNKNOWN" if "s INDETERMINATE" in terminals else
              stop or "UNKNOWN")
    model_check = None
    if status == "SAT":
        # Reuse the separately written literal-level parser from the prior gate.
        sys.path.insert(0, str(ROOT / "n41_n131_fouratom_product_anf_sat_20261012"))
        import run as checker  # noqa: E402
        bits = checker.model(stdout, variable_count)
        model_check = checker.check_formula(form, bits)
        assert model_check == {"cnf_clauses_checked": clause_count + len(units),
                               "native_xor_rows_checked": xor_count}
    receipt = {"label": label, "status": status, "candidate_id": None,
               "formula": profile, "command": command, "terminal_lines": terminals,
               "stop": stop, "exit_code": child.returncode,
               "solver_wall_ns_exploratory": ended - start,
               "peak_combined_rss_bytes_sampled": peak,
               "stdout_sha256": sha(stdout_path), "stderr_sha256": sha(stderr_path),
               "restart_rows": sum(line.startswith("c rst") for line in stdout.splitlines()),
               "model_check": model_check}
    (HERE / (label + ".json")).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(label, status, (ended - start) / 1e9, flush=True)
    return status


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    for name, path in (("runner", HERE / "run.py"), ("ten", PARENT / "ten.py"),
                       ("fixture", PARENT / "control_fixture.json"),
                       ("prior_fixture", ten.NINE / "control_fixture.json"),
                       ("solver", SOLVER)):
        assert sha(path) == protocol["sha256"][name], name
    ten.build = direct_build()
    chain, rows, root, bdd_nodes, intermediates, points = input_data()
    start = time.monotonic_ns()
    circuit, wires = ten.build([row["standard_reciprocal"] for row in rows], root, bdd_nodes)
    constructed = time.monotonic_ns()
    checked, units = constructed_check(circuit, wires, chain, intermediates, points)
    checked_at = time.monotonic_ns()
    original = HERE / "direct_control.xcnf"
    circuit.write(original)
    written = time.monotonic_ns()
    profile = {"variables": circuit.next_var - 1, "clauses": len(circuit.clauses),
               "native_xor_rows": len(circuit.xors), "bytes": original.stat().st_size,
               "sha256": sha(original)}
    (HERE / "construction.json").write_text(json.dumps({
        "status": "PASS_DIRECT_S3_CONSTRUCTED_ASSIGNMENT", "candidate_id": None,
        "formula": profile, "assignment_check": checked,
        "nine_group_links_checked": 9,
        "phase_ns_exploratory": {"build": constructed - start,
                                  "assignment_check": checked_at - constructed,
                                  "serialization": written - checked_at}}, indent=2, sort_keys=True) + "\n")
    for label, kinds in (("outputs_only", ("target", "outputs")),
                         ("selectors_outputs", ("target", "selectors", "outputs"))):
        pinned_units = [literal for kind in kinds for literal in units[kind]]
        run_arm(label, original, pinned_units, profile["variables"],
                profile["clauses"], profile["native_xor_rows"])


if __name__ == "__main__":
    main()
