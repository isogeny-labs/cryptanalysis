"""One target-conditioned W18 query over its 131 Frobenius conjugates."""

import hashlib
import json
import resource
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n131_w18_terminal4_20261012"
SUPPORT = HERE.parent / "n131_w16_w18_sixpair_width_gate_20261010" / "support_w18.tsv"
GEOMETRY_AUDIT = HERE.parent / "n131_lowpower_w18_m8" / "audit.json"
sys.path.insert(0, str(PARENT))
import terminal  # noqa: E402

ROTATION_COUNT = 131
TERMINAL_STATES = 4
TOTAL_CAP_NS = 600 * 10**9
SOLVER_FLAGS = ["--threads=1", "--maxtime=540", "--zero-exit-status",
                "--verb=1", "--printsol=1"]
PARENT_SOURCES = ("terminal.py", "prepare.py", "pool.json", "source_count.json",
                  "protocol.json", "control_result.json", "query_result.json",
                  "sage_audit_result.json", "audit_result.json")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def point_frob(point):
    return [terminal.independent.square(int(point[0])),
            terminal.independent.square(int(point[1]))]


def orbit(point):
    values, current = [], list(point)
    for _ in range(ROTATION_COUNT):
        values.append(current)
        current = point_frob(current)
    assert current == list(point) and len({tuple(row) for row in values}) == ROTATION_COUNT
    return values


def batch_inverse(values):
    field = terminal.independent
    assert values and all(values)
    prefixes = [1]
    for value in values:
        prefixes.append(field.mul(prefixes[-1], value))
    inverse_product = field.inverse(prefixes[-1])
    result = [0] * len(values)
    for index in range(len(values) - 1, -1, -1):
        result[index] = field.mul(inverse_product, prefixes[index])
        inverse_product = field.mul(inverse_product, values[index])
    assert inverse_product == 1
    assert all(field.mul(a, b) == 1 for a, b in zip(values, result))
    return result


def residuals(raw_target):
    states = terminal.pool()["states"]
    assert len(states) == TERMINAL_STATES
    inputs, denominators = [], []
    for rotation, rotated_target in enumerate(orbit(raw_target)):
        for state_index, state in enumerate(states):
            other = state["rotated_raw_point"]
            x1, y1 = rotated_target
            x2, y2 = other[0], other[1] ^ other[0]
            denominator = x1 ^ x2
            inputs.append((rotation, state_index, x1, y1, x2, y2, denominator))
            if denominator:
                denominators.append(denominator)
    inverse_denominators = iter(batch_inverse(denominators))
    points = []
    field = terminal.independent
    for rotation, state_index, x1, y1, x2, y2, denominator in inputs:
        if denominator:
            slope = field.mul(y1 ^ y2, next(inverse_denominators))
            x3 = field.square(slope) ^ slope ^ x1 ^ x2
            y3 = field.mul(slope, x1 ^ x3) ^ x3 ^ y1
            point = (x3, y3)
        else:
            point = field.point_add((x1, y1), (x2, y2))
        assert point is not None and point[0] not in (0, 1)
        points.append((rotation, state_index, point))
    assert next(inverse_denominators, None) is None
    inverse_x = batch_inverse([point[0] for _, _, point in points])
    result = [{"target_rotation": rotation,
               "terminal_state_index": state_index,
               "point": list(point), "standard_reciprocal": a}
              for (rotation, state_index, point), a in zip(points, inverse_x)]
    assert len(result) == ROTATION_COUNT * TERMINAL_STATES
    return result


def source_geometry():
    table = [tuple(map(int, line.split())) for line in SUPPORT.read_text().splitlines()]
    assert len(table) == 131307 and len({mask for mask, _ in table}) == len(table)
    columns = {column for _, column in table}
    assert len(columns) == 131068
    parent_count = json.loads((PARENT / "source_count.json").read_text())
    count = int(parent_count["signed_ordered_distinct_column_tuples"])
    full_order = int(parent_count["full_curve_order"])
    mean = Fraction(ROTATION_COUNT * count, full_order)
    return {"source_masks": len(table), "folded_columns": len(columns),
            "full_signed_frobenius_base_size": 2 * ROTATION_COUNT * len(columns),
            "target_rotations": ROTATION_COUNT,
            "terminal_states_per_rotation": TERMINAL_STATES,
            "labeled_tuple_count_upper": str(ROTATION_COUNT * count),
            "uniform_raw_point_mean_upper_exact": f"{mean.numerator}/{mean.denominator}",
            "uniform_raw_point_mean_upper_decimal": format(float(mean), ".12g"),
            "base_construction": "sign and full Frobenius closure of the W18 source columns"}


def sources():
    return {"runner": Path(__file__), "preflight_runner": HERE / "preflight.py",
            "preflight_result": HERE / "preflight_result.json",
            "n41_orbit_control_script": HERE / "n41_orbit_control_sage.py",
            "n41_orbit_control_result": HERE / "n41_orbit_control_result.json",
            "n41_ordinary_relation": HERE.parent / "n41_w8_terminal1_sevenpair_20261012" / "sage_audit_result_v2.json",
            "n41_fixture": HERE.parent / "n41_w7_entropy_cubic_20261011" / "w8" / "fixture.json",
            "support": SUPPORT, "geometry_audit": GEOMETRY_AUDIT,
            "solver": terminal.base.SOLVER.resolve(),
            "checked_sage_runtime": HERE / "sage_runtime_info.json",
            **{f"parent_{name}": PARENT / name for name in PARENT_SOURCES}}


def freeze():
    parent = terminal.check_protocol()
    assert json.loads((HERE / "preflight_result.json").read_text())["status"] == "PASS_EXACT_524_BATCH_RESIDUAL_REPLAY"
    assert json.loads((HERE / "n41_orbit_control_result.json").read_text())["status"] == "PASS_N41_FROBENIUS_ORBIT_RELATION_TRANSPORT"
    target = terminal.base.target_record()
    assert target["workload_id"] == parent["workload_id"]
    assert len(orbit(target["public_target"])) == ROTATION_COUNT
    assert len(orbit(target["preimages"][0]["point"])) == ROTATION_COUNT
    geometry = source_geometry()
    assert geometry["full_signed_frobenius_base_size"] == 34339816
    save("protocol.json", {"status": "FROZEN_N131_FROBENIUS_TARGET_FIBER_BEFORE_QUERY",
                           "candidate_id": None,
                           "curve_id": parent["curve_id"],
                           "workload_id": parent["workload_id"],
                           "public_target": parent["public_target"],
                           "raw_preimage_index": 0,
                           "source_geometry": geometry,
                           "selection_law": "all 131 target Frobenius rotations, then all four signed states of one fixed terminal edge",
                           "worker_count": 1,
                           "combined_rss_cap_bytes": parent["combined_rss_cap_bytes"],
                           "total_target_dependent_cap_seconds": TOTAL_CAP_NS // 10**9,
                           "solver_flags": SOLVER_FLAGS,
                           "source_sha256": {name: sha(path) for name, path in sources().items()}})


def protocol():
    data = json.loads((HERE / "protocol.json").read_text())
    assert data["status"] == "FROZEN_N131_FROBENIUS_TARGET_FIBER_BEFORE_QUERY"
    assert data["source_sha256"] == {name: sha(path) for name, path in sources().items()}
    assert data["solver_flags"] == SOLVER_FLAGS
    terminal.check_protocol()
    return data


def control():
    protocol()
    fixture = json.loads((terminal.BASE / "control_fixture.json").read_text())
    residual_rows = residuals(fixture["raw_target"])
    chosen = terminal.pool()["control_choice_index"]
    expected = terminal.base.standard_reciprocal(fixture["intermediate_z"][6])
    assert residual_rows[chosen]["standard_reciprocal"] == expected
    _, root, nodes = terminal.base.source_domain()
    t0 = time.monotonic_ns()
    circuit, wires = terminal.build([row["standard_reciprocal"] for row in residual_rows],
                                    root, nodes)
    t1 = time.monotonic_ns()
    formula = HERE / "control.xcnf"
    circuit.write(formula)
    t2 = time.monotonic_ns()
    initial = {}
    def bind(bits, value):
        initial.update({wire: value >> bit & 1 for bit, wire in enumerate(bits)})
    h2 = terminal.base.pair.gf_square(terminal.base.pair.gf_half_trace(
        terminal.base.pair.coordinate(terminal.base.pair.SEED)))
    for item in fixture["selected"][:8]:
        slot = item["slot"]
        code = terminal.base.pair.selector_code(item["masks"][0])
        a = terminal.base.standard_reciprocal(item["unrotated_pair_output_z"])
        product = terminal.base.pair.product_from_code(code)
        assert (terminal.base.pair.gf_mul(1 ^ h2, terminal.base.pair.gf_square(a)) ^
                terminal.base.pair.gf_mul(a, product) ^ h2) == 0
        bind(wires["selectors"][slot], code)
        bind(wires["outputs"][slot], a)
    for bits, z in zip(wires["middle"], fixture["intermediate_z"][:6]):
        bind(bits, terminal.base.standard_reciprocal(z))
    for index, wire in enumerate(wires["choices"]):
        initial[wire] = int(index == chosen)
    rotated = [terminal.base.standard_reciprocal(z)
               for z in fixture["pair_rotated_z"][:8]]
    middle = [terminal.base.standard_reciprocal(z)
              for z in fixture["intermediate_z"][:6]]
    left, branches = rotated[0], []
    for index in range(1, 8):
        right = middle[index - 1] if index < 7 else expected
        total = left ^ rotated[index] ^ right
        branch = (terminal.base.pair.gf_mul(
            terminal.base.pair.gf_mul(left, rotated[index]), right) ^
            terminal.base.halftrace(terminal.base.pair.gf_square(total)))
        assert branch in (0, 1)
        initial[wires["branches"][index - 1]] = branch
        branches.append(branch)
        left = right
    checked = terminal.base.check_assignment(
        circuit, terminal.base.complete_assignment(circuit, initial))
    save("control_result.json", {"status": "PASS_N131_FROBENIUS_TARGET_FIBER_CONTROL",
                                 "candidate_id": None,
                                 "control_choice_index": chosen,
                                 "control_target_rotation": 0,
                                 "residual_count": len(residual_rows),
                                 "distinct_residuals": len({row["standard_reciprocal"] for row in residual_rows}),
                                 "branch_bits": branches,
                                 "primary_variables": len(initial),
                                 "assignment_check": checked,
                                 "formula": terminal.base.profile(circuit, formula,
                                                                  (t1-t0)/1e9, (t2-t1)/1e9),
                                 "protocol_sha256": sha(HERE / "protocol.json")})
    print("PASS_N131_FROBENIUS_TARGET_FIBER_CONTROL", flush=True)


def query():
    frozen = protocol()
    control_result = json.loads((HERE / "control_result.json").read_text())
    assert control_result["status"] == "PASS_N131_FROBENIUS_TARGET_FIBER_CONTROL"
    target = terminal.base.target_record()
    raw_target = target["preimages"][0]["point"]
    _, root, nodes = terminal.base.source_domain()
    t0 = time.monotonic_ns()
    residual_rows = residuals(raw_target)
    t1 = time.monotonic_ns()
    circuit, wires = terminal.build([row["standard_reciprocal"] for row in residual_rows],
                                    root, nodes)
    t2 = time.monotonic_ns()
    formula = HERE / "ordinary.xcnf"
    circuit.write(formula)
    t3 = time.monotonic_ns()
    details = terminal.base.profile(circuit, formula, (t2-t1)/1e9, (t3-t2)/1e9)
    del circuit
    print(json.dumps({"phase": "ordinary_formula", "formula": details}), flush=True)
    outpath, errpath = HERE / "solver.stdout.txt", HERE / "solver.stderr.txt"
    parent = psutil.Process()
    peak, stop = 0, None
    with outpath.open("x") as stdout, errpath.open("x") as stderr:
        process = subprocess.Popen([str(terminal.base.SOLVER), *SOLVER_FLAGS,
                                    str(formula)], stdout=stdout, stderr=stderr)
        child = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                combined = parent.memory_info().rss + child.memory_info().rss
            except psutil.NoSuchProcess:
                combined = parent.memory_info().rss
            peak = max(peak, combined)
            if combined > frozen["combined_rss_cap_bytes"]:
                stop = "RSS_CAP"
            elif time.monotonic_ns() - t0 >= TOTAL_CAP_NS:
                stop = "TOTAL_QUERY_TIMEOUT"
            if stop:
                process.kill()
                break
            time.sleep(0.05)
        code = process.wait()
    t4 = time.monotonic_ns()
    output = outpath.read_text(errors="replace")
    status = ("BOUNDED_UNKNOWN" if stop else
              "SAT_PENDING_GROUP_REPLAY" if "s SATISFIABLE" in output else
              "UNSAT" if "s UNSATISFIABLE" in output else "BOUNDED_UNKNOWN")
    decoded = None
    if status == "SAT_PENDING_GROUP_REPLAY":
        positive = {int(token) for line in output.splitlines() if line.startswith("v ")
                    for token in line.split()[1:] if token.isdigit() and int(token) > 0}
        def decode(bits):
            return sum(int(wire in positive) << bit for bit, wire in enumerate(bits))
        chosen = [index for index, wire in enumerate(wires["choices"]) if wire in positive]
        assert len(chosen) == 1
        decoded = {"selected_codes": [decode(bits) for bits in wires["selectors"]],
                   "pair_standard_reciprocals": [decode(bits) for bits in wires["outputs"]],
                   "middle_standard_reciprocals": [decode(bits) for bits in wires["middle"]],
                   "branch_bits": [int(wire in positive) for wire in wires["branches"]],
                   "target_rotation": chosen[0] // TERMINAL_STATES,
                   "terminal_state_index": chosen[0] % TERMINAL_STATES,
                   "formula_sha256": details["xcnf_sha256"]}
        save("decoded_model.json", decoded)
    t5 = time.monotonic_ns()
    phase = {"target_orbit_and_residuals_ns": t1-t0,
             "formula_construction_ns": t2-t1,
             "formula_serialization_ns": t3-t2,
             "solver_search_ns": t4-t3,
             "terminal_parse_and_decode_ns": t5-t4}
    assert sum(phase.values()) == t5-t0
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    save("query_result.json", {"status": status, "candidate_id": None,
                               "curve_id": frozen["curve_id"],
                               "workload_id": frozen["workload_id"],
                               "public_target": frozen["public_target"],
                               "raw_preimage_index": 0,
                               "raw_target": raw_target,
                               "target_rotations": ROTATION_COUNT,
                               "terminal_states_per_rotation": TERMINAL_STATES,
                               "residual_count": len(residual_rows),
                               "distinct_residuals": len({row["standard_reciprocal"] for row in residual_rows}),
                               "phase_ns": phase,
                               "target_dependent_attempt_ns": t5-t0,
                               "formula": details, "worker_count": 1,
                               "solver_flags": SOLVER_FLAGS,
                               "solver_exit_code": code, "stop_reason": stop,
                               "peak_combined_rss_bytes_sampled": peak,
                               "parent_peak_rss_bytes": rss if sys.platform == "darwin" else rss*1024,
                               "status_lines": [line for line in output.splitlines() if line.startswith("s ")],
                               "restart_rows": sum(line.startswith("c rst") for line in output.splitlines()),
                               "decoded_model_saved": decoded is not None,
                               "stdout_sha256": sha(outpath), "stderr_sha256": sha(errpath),
                               "protocol_sha256": sha(HERE / "protocol.json")})
    print(json.dumps({"status": status, "attempt_seconds": (t5-t0)/1e9,
                      "peak_rss": peak}), flush=True)


if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] in ("freeze", "control", "query")
    {"freeze": freeze, "control": control, "query": query}[sys.argv[1]]()
