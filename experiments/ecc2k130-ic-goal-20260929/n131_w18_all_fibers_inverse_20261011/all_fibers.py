"""Four raw fibers and 32 terminal states for one N131 public query."""

import hashlib
import json
import psutil
import resource
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / "n131_w18_terminal_fiber_20261011"
BASE = ROOT / "n131_fixed_seed_ninepair_cubic_20261011"
GATE = ROOT / "n131_w18_inverse_trace_terminal_20261011"
sys.path.insert(0, str(PRIOR))
import terminal  # noqa: E402

ONLINE_CAP = 600
RSS_CAP = 4 * 1024**3
FLAGS = ["--threads=1", "--maxtime=580", "--zero-exit-status",
         "--verb=1", "--printsol=1"]
TORSION = [None, (0, 1), (1, 0), (1, 1)]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def sources():
    result = {"runner": Path(__file__),
              "sage_audit": HERE / "audit_sage.py",
              "gate_equivalence": GATE / "gate_equivalence.json",
              "prior_protocol": PRIOR / "protocol.json",
              "prior_sage_fibers": PRIOR / "sage_audit_result.json"}
    result.update({"prior_" + name: path for name, path in terminal.sources().items()})
    return result


def freeze():
    target = terminal.base.target_record()
    prior = json.loads((PRIOR / "protocol.json").read_text())
    assert prior["source_sha256"] == {name: sha(path) for name, path in terminal.sources().items()}
    sage = json.loads((PRIOR / "sage_audit_result.json").read_text())
    assert sage["status"] == "PASS_INDEPENDENT_SAGE_TERMINAL_FIBERS"
    counts = json.loads((PRIOR / "source_count.json").read_text())
    assert counts["status"] == "PASS_EXACT_SELECTED_TERMINAL_SOURCE_COUNT"
    assert counts["selected_signed_states"] == 32
    pool = terminal.pool()
    assert pool["control_choice_index"] == 0
    gate = json.loads((GATE / "gate_equivalence.json").read_text())
    assert gate["status"] == "PASS_EXACT_SOURCE_GATE_EQUIVALENCE"
    assert gate["canonical_codes"] == 33191
    mean = 4 * Fraction(counts["uniform_raw_point_mean_upper_exact"])
    for offset in TORSION:
        assert point_mul(4, offset) is None
    save("protocol.json", {"status": "FROZEN_N131_ALL_FIBERS_BEFORE_CONTROL_AND_QUERY",
                           "candidate_id": None,
                           "curve_id": target["curve_id"],
                           "workload_id": target["workload_id"],
                           "public_target": target["public_target"],
                           "raw_preimage_policy": "inverse_four_mod_r_then_four_torsion_offsets",
                           "four_torsion_offsets": [list(p) if p else None for p in TORSION],
                           "terminal_pool": pool["states"],
                           "terminal_state_count": 32,
                           "residual_choices": 128,
                           "free_pair_slots": 8,
                           "free_pair_rotations": terminal.ROTATIONS,
                           "eligible_source_codes_per_slot": gate["canonical_codes"],
                           "source_gate": "two_nonzero_inverse_witnesses_with_zero_trace",
                           "free_pair_code_policy": "all_distinct_and_different_from_selected_terminal_code",
                           "source_count_distinct_column_ordered_tuples_per_raw_point":
                               counts["signed_ordered_distinct_column_tuples"],
                           "uniform_public_point_mean_upper_exact": f"{mean.numerator}/{mean.denominator}",
                           "uniform_public_point_mean_upper_decimal": format(float(mean), ".12g"),
                           "online_total_cap_seconds": ONLINE_CAP,
                           "combined_rss_cap_bytes": RSS_CAP,
                           "worker_count": 1, "solver_flags": FLAGS,
                           "source_sha256": {name: sha(path) for name, path in sources().items()}})
    print("FROZEN_N131_ALL_FIBERS", format(float(mean), ".9g"))


def check_protocol():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["status"] == "FROZEN_N131_ALL_FIBERS_BEFORE_CONTROL_AND_QUERY"
    assert protocol["source_sha256"] == {name: sha(path) for name, path in sources().items()}
    assert protocol["terminal_pool"] == terminal.pool()["states"]
    return protocol


def point_mul(k, point):
    result = None
    while k:
        if k & 1:
            result = terminal.independent.point_add(result, point)
        point = terminal.independent.point_add(point, point)
        k >>= 1
    return result


def public_preimages(public_point):
    r = terminal.prepare.support.R131
    point = point_mul(pow(4, -1, r), tuple(public_point))
    assert point_mul(4, point) == tuple(public_point)
    rows = [terminal.independent.point_add(point, torsion) for torsion in TORSION]
    assert len(set(rows)) == 4
    assert all(point_mul(4, row) == tuple(public_point) for row in rows)
    return rows


def residuals(preimages):
    rows = []
    for preimage_index, raw in enumerate(preimages):
        for terminal_index, state in enumerate(terminal.pool()["states"]):
            point = terminal.prepare.subtract(raw, state["rotated_raw_point"])
            assert point is not None and point[0] not in (0, 1)
            value = terminal.independent.inverse(point[0])
            assert terminal.independent.mul(value, point[0]) == 1
            rows.append({"preimage_index": preimage_index,
                         "terminal_state_index": terminal_index,
                         "point": list(point), "standard_reciprocal": value})
    assert len(rows) == len({row["standard_reciprocal"] for row in rows}) == 128
    return rows


def build_inverse(residual_values):
    assert len(residual_values) == 128
    pair = terminal.base.pair
    base = terminal.base
    circuit = base.KaratsubaCircuit(pair.N, [0, 1, 2, 13])
    algebra = base.Algebra(circuit, base.Field(), dense_and_threshold=3000)
    h2 = pair.gf_square(pair.gf_half_trace(pair.coordinate(pair.SEED)))
    coefficient = 1 ^ h2
    trace_basis = [base.trace(1 << bit) for bit in range(pair.N)]
    selectors, outputs, rotated, inverse_witnesses = [], [], [], []
    for rotation in terminal.ROTATIONS:
        bits = [circuit.variable() for _ in pair.SOURCE_BITS]
        out = [circuit.variable() for _ in range(pair.N)]
        selectors.append(bits)
        outputs.append(out)
        product = algebra.expression(zip(bits, pair.product_basis()))
        square_term = algebra.expression(
            (wire, pair.gf_mul(coefficient, pair.gf_square(1 << bit)))
            for bit, wire in enumerate(out))
        circuit.require_zero(algebra.add(
            algebra.mul(algebra.from_bits(out), product), square_term,
            algebra.expression(((-1, h2),))).bits())
        circuit.clauses.append(" ".join(map(str, out)) + " 0")
        source = algebra.expression(
            (wire, 1 << (source_bit + 1))
            for wire, source_bit in zip(bits, pair.SOURCE_BITS))
        other = algebra.add(source, algebra.expression(((-1, pair.coordinate(pair.SEED)),)))
        witnesses = []
        for endpoint in (source, other):
            inverse_bits = [circuit.variable() for _ in range(pair.N)]
            circuit.require_zero(algebra.add(
                algebra.mul(endpoint, algebra.from_bits(inverse_bits)), algebra.one).bits())
            circuit.require_zero([circuit.xor(
                wire for wire, tracebit in zip(inverse_bits, trace_basis) if tracebit)])
            witnesses.append(inverse_bits)
        inverse_witnesses.append(witnesses)
        images = [pair.gf_frobenius(1 << bit, rotation) for bit in range(pair.N)]
        rotated.append(algebra.from_bits(circuit.linear_element(out, images)))

    choices = [circuit.variable() for _ in residual_values]
    circuit.clauses.append(" ".join(map(str, choices)) + " 0")
    for index, left in enumerate(choices):
        for right in choices[index + 1:]:
            circuit.clauses.append(f"-{left} -{right} 0")
    selected_residual = algebra.expression(zip(choices, residual_values))

    for index, left in enumerate(selectors):
        for right in selectors[index + 1:]:
            differences = [circuit.xor((a, b)) for a, b in zip(left, right)]
            circuit.clauses.append(" ".join(map(str, differences)) + " 0")
    terminal_codes = [state["code"] for _ in range(4)
                      for state in terminal.pool()["states"]]
    for choice, terminal_code in zip(choices, terminal_codes):
        for bits in selectors:
            mismatch = [(-wire if terminal_code >> bit & 1 else wire)
                        for bit, wire in enumerate(bits)]
            circuit.clauses.append(" ".join(map(str, [-choice, *mismatch])) + " 0")

    middle = [[circuit.variable() for _ in range(pair.N)] for _ in range(6)]
    branches = [circuit.variable() for _ in range(7)]
    ht_basis = []
    for bit in range(pair.N):
        value, image = pair.gf_square(1 << bit), 0
        for _ in range((pair.N + 1) // 2):
            image ^= value
            value = pair.gf_square(pair.gf_square(value))
        ht_basis.append(image)
    running = rotated[0]
    for index in range(1, 8):
        output = (algebra.from_bits(middle[index - 1]) if index < 7
                  else selected_residual)
        total = algebra.add(running, rotated[index], output)
        ht = circuit.linear_element(total.bits(), ht_basis)
        circuit.require_zero(algebra.add(
            algebra.mul(algebra.mul(running, rotated[index]), output),
            algebra.from_bits(ht),
            algebra.expression(((branches[index - 1], 1),))).bits())
        circuit.require_zero([circuit.xor(
            wire for wire, bit in zip(total.bits(), trace_basis) if bit)])
        if index < 7:
            circuit.clauses.append(" ".join(map(str, middle[index - 1])) + " 0")
        running = output
    return circuit, {"selectors": selectors, "outputs": outputs,
                     "middle": middle, "branches": branches,
                     "inverse_witnesses": inverse_witnesses,
                     "choices": choices}


def control():
    check_protocol()
    fixture = json.loads((BASE / "control_fixture.json").read_text())
    raw = tuple(fixture["raw_target"])
    preimages = [terminal.independent.point_add(raw, torsion) for torsion in TORSION]
    fixture_public = point_mul(4, raw)
    assert all(point_mul(4, point) == fixture_public for point in preimages)
    rows = residuals(preimages)
    expected = terminal.base.standard_reciprocal(fixture["intermediate_z"][6])
    assert rows[0]["standard_reciprocal"] == expected
    start = time.monotonic_ns()
    circuit, wires = build_inverse([row["standard_reciprocal"] for row in rows])
    built = time.monotonic_ns()
    path = HERE / "control.xcnf"
    circuit.write(path)
    written = time.monotonic_ns()
    initial = {}
    def bind(bits, value):
        initial.update({wire: value >> bit & 1 for bit, wire in enumerate(bits)})
    pair = terminal.base.pair
    h2 = pair.gf_square(pair.gf_half_trace(pair.coordinate(pair.SEED)))
    for item in fixture["selected"][:8]:
        slot = item["slot"]
        code = pair.selector_code(item["masks"][0])
        a = terminal.base.standard_reciprocal(item["unrotated_pair_output_z"])
        product = pair.product_from_code(code)
        assert pair.gf_mul(1 ^ h2, pair.gf_square(a)) ^ pair.gf_mul(a, product) ^ h2 == 0
        bind(wires["selectors"][slot], code)
        bind(wires["outputs"][slot], a)
        for side, mask in enumerate(item["masks"]):
            source = pair.coordinate(mask)
            witness = terminal.base.inverse(source)
            assert pair.gf_mul(source, witness) == 1
            assert terminal.base.trace(witness) == 0
            bind(wires["inverse_witnesses"][slot][side], witness)
    for bits, z in zip(wires["middle"], fixture["intermediate_z"][:6]):
        bind(bits, terminal.base.standard_reciprocal(z))
    for index, wire in enumerate(wires["choices"]):
        initial[wire] = int(index == 0)
    rotated = [terminal.base.standard_reciprocal(z) for z in fixture["pair_rotated_z"][:8]]
    middle = [terminal.base.standard_reciprocal(z) for z in fixture["intermediate_z"][:6]]
    left, branch_bits = rotated[0], []
    for index in range(1, 8):
        right = middle[index - 1] if index < 7 else expected
        total = left ^ rotated[index] ^ right
        branch = pair.gf_mul(pair.gf_mul(left, rotated[index]), right) ^ terminal.base.halftrace(pair.gf_square(total))
        assert branch in (0, 1)
        initial[wires["branches"][index - 1]] = branch
        branch_bits.append(branch)
        left = right
    checked = terminal.base.check_assignment(circuit,
                                             terminal.base.complete_assignment(circuit, initial))
    save("control_result.json", {"status": "PASS_N131_ALL_FIBERS_CONSTRUCTED_CONTROL",
                                 "candidate_id": None,
                                 "selected_choice_index": 0,
                                 "fixture_public_point": list(fixture_public),
                                 "raw_preimages": [list(point) for point in preimages],
                                 "residuals": rows,
                                 "branch_bits": branch_bits,
                                 "primary_variables": len(initial),
                                 "assignment_check": checked,
                                 "formula": terminal.base.profile(circuit, path,
                                                                  (built-start)/1e9,
                                                                  (written-built)/1e9),
                                 "protocol_sha256": sha(HERE / "protocol.json")})
    print("PASS_N131_ALL_FIBERS_CONSTRUCTED_CONTROL", flush=True)


def query():
    protocol = check_protocol()
    control_receipt = json.loads((HERE / "control_result.json").read_text())
    assert control_receipt["status"] == "PASS_N131_ALL_FIBERS_CONSTRUCTED_CONTROL"
    target = terminal.base.target_record()
    t0 = time.monotonic_ns()
    preimages = public_preimages(target["public_target"])
    assert set(preimages) == {tuple(row["point"]) for row in target["preimages"]}
    t1 = time.monotonic_ns()
    rows = residuals(preimages)
    t2 = time.monotonic_ns()
    circuit, wires = build_inverse([row["standard_reciprocal"] for row in rows])
    t3 = time.monotonic_ns()
    formula = HERE / "ordinary.xcnf"
    circuit.write(formula)
    t4 = time.monotonic_ns()
    profile = terminal.base.profile(circuit, formula, (t3-t2)/1e9, (t4-t3)/1e9)
    del circuit
    print(json.dumps({"phase": "frozen_ordinary_formula", "formula": profile}), flush=True)
    outpath, errpath = HERE / "solver.stdout.txt", HERE / "solver.stderr.txt"
    parent = psutil.Process()
    peak, cpu_sample, stop_reason = 0, 0.0, None
    with outpath.open("x") as stdout, errpath.open("x") as stderr:
        process = subprocess.Popen([str(terminal.base.SOLVER), *FLAGS, str(formula)],
                                   stdout=stdout, stderr=stderr)
        child = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                combined = parent.memory_info().rss + child.memory_info().rss
                cpu = child.cpu_times()
                cpu_sample = max(cpu_sample, cpu.user + cpu.system)
            except psutil.NoSuchProcess:
                combined = parent.memory_info().rss
            peak = max(peak, combined)
            if combined > RSS_CAP:
                stop_reason = "RSS_CAP"
                process.kill()
                break
            if time.monotonic_ns() - t0 > ONLINE_CAP * 10**9:
                stop_reason = "ONLINE_WALL_CAP"
                process.kill()
                break
            time.sleep(0.05)
        code = process.wait()
    t5 = time.monotonic_ns()
    output = outpath.read_text(errors="replace")
    status = ("BOUNDED_UNKNOWN" if stop_reason else
              "SAT_PENDING_GROUP_REPLAY" if "s SATISFIABLE" in output else
              "UNSAT" if "s UNSATISFIABLE" in output else "BOUNDED_UNKNOWN")
    decoded = None
    if status == "SAT_PENDING_GROUP_REPLAY":
        positive = {int(token) for line in output.splitlines() if line.startswith("v ")
                    for token in line.split()[1:] if token.isdigit() and int(token) > 0}
        def decode(bits):
            return sum(int(wire in positive) << bit for bit, wire in enumerate(bits))
        choice_indexes = [index for index, wire in enumerate(wires["choices"])
                          if wire in positive]
        assert len(choice_indexes) == 1
        choice = choice_indexes[0]
        decoded = {"selected_codes": [decode(bits) for bits in wires["selectors"]],
                   "pair_standard_reciprocals": [decode(bits) for bits in wires["outputs"]],
                   "middle_standard_reciprocals": [decode(bits) for bits in wires["middle"]],
                   "branch_bits": [int(wire in positive) for wire in wires["branches"]],
                   "inverse_witnesses": [[decode(bits) for bits in slot]
                                         for slot in wires["inverse_witnesses"]],
                   "selected_choice_index": choice,
                   "selected_preimage_index": choice // 32,
                   "selected_terminal_state_index": choice % 32,
                   "formula_sha256": profile["xcnf_sha256"]}
        save("decoded_model.json", decoded)
    t6 = time.monotonic_ns()
    phases = {"public_raw_preimages_ns": t1-t0,
              "target_residual_generation_ns": t2-t1,
              "formula_construction_ns": t3-t2,
              "formula_serialization_ns": t4-t3,
              "solver_search_ns": t5-t4,
              "terminal_parse_and_decode_ns": t6-t5}
    assert sum(phases.values()) == t6-t0
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    save("query_result.json", {"status": status, "candidate_id": None,
                               "curve_id": protocol["curve_id"],
                               "workload_id": protocol["workload_id"],
                               "public_target": protocol["public_target"],
                               "raw_preimages": [list(point) for point in preimages],
                               "residuals": rows,
                               "phase_ns": phases,
                               "target_dependent_attempt_ns": t6-t0,
                               "formula": profile,
                               "worker_count": 1, "solver_flags": FLAGS,
                               "solver_exit_code": code,
                               "solver_cpu_seconds_sampled": cpu_sample,
                               "stop_reason": stop_reason,
                               "peak_combined_rss_bytes_sampled": peak,
                               "parent_peak_rss_bytes": rss if sys.platform == "darwin" else rss*1024,
                               "status_lines": [line for line in output.splitlines() if line.startswith("s ")],
                               "restart_rows": sum(line.startswith("c rst") for line in output.splitlines()),
                               "decoded_model_saved": decoded is not None,
                               "stdout_sha256": sha(outpath), "stderr_sha256": sha(errpath),
                               "protocol_sha256": sha(HERE / "protocol.json")})
    print(json.dumps({"status": status, "online_attempt_seconds": (t6-t0)/1e9,
                      "solver_cpu_seconds_sampled": cpu_sample,
                      "peak_rss": peak}), flush=True)


if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] in ("freeze", "control", "query")
    {"freeze": freeze, "control": control, "query": query}[sys.argv[1]]()
