"""Inverse-trace source gates for a fixed-terminal N131 W18 public query."""

import hashlib
import json
import math
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
sys.path.insert(0, str(PRIOR))
import terminal  # noqa: E402

ONLINE_CAP = 600
RSS_CAP = 4 * 1024**3
FLAGS = ["--threads=1", "--maxtime=580", "--zero-exit-status",
         "--verb=1", "--printsol=1"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def sources():
    result = {"runner": Path(__file__),
              "gate_equivalence": HERE / "gate_equivalence.json",
              "prior_protocol": PRIOR / "protocol.json",
              "prior_sage_fibers": PRIOR / "sage_audit_result.json"}
    result.update({"prior_" + name: path for name, path in terminal.sources().items()})
    return result


def gate_equivalence():
    pair = terminal.base.pair
    columns = {int(mask): int(column) for mask, column in
               (line.split() for line in terminal.base.SUPPORT.read_text().splitlines())}
    bdd_codes = pair.valid_codes(columns)
    inverse_codes = set()
    equal_columns = 0
    for code in range(1 << len(pair.SOURCE_BITS)):
        mask = pair.mask_from_code(code)
        other = mask ^ pair.SEED
        if mask in columns and other in columns:
            inverse_codes.add(code)
            equal_columns += columns[mask] == columns[other]
    assert len(inverse_codes) == len(bdd_codes) == 33191
    assert inverse_codes == bdd_codes and equal_columns == 0
    save("gate_equivalence.json", {
        "status": "PASS_EXACT_SOURCE_GATE_EQUIVALENCE",
        "canonical_codes": len(inverse_codes),
        "same_folded_column_pairs": equal_columns,
        "source_support_sha256": sha(terminal.base.SUPPORT),
        "canonical_code_digest": hashlib.sha256(
            b"".join(code.to_bytes(3, "little") for code in sorted(inverse_codes))).hexdigest()})
    print("PASS_EXACT_SOURCE_GATE_EQUIVALENCE", len(inverse_codes), flush=True)


def selected():
    pool = terminal.pool()
    assert pool["control_choice_index"] == 0
    return pool["states"][0]


def freeze():
    target = terminal.base.target_record()
    prior = json.loads((PRIOR / "protocol.json").read_text())
    assert prior["source_sha256"] == {name: sha(path) for name, path in terminal.sources().items()}
    sage = json.loads((PRIOR / "sage_audit_result.json").read_text())
    assert sage["status"] == "PASS_INDEPENDENT_SAGE_TERMINAL_FIBERS"
    counts = json.loads((PRIOR / "source_count.json").read_text())
    edge = selected()["folded_columns"]
    rows = [row for row in counts["conditional_edge_rows"] if row["folded_columns"] == edge]
    assert len(rows) == 1
    signed_tuples = rows[0]["eight_pair_matchings"] * math.factorial(8) * 4**8
    mean = Fraction(signed_tuples, 4 * terminal.prepare.support.R131)
    gate = json.loads((HERE / "gate_equivalence.json").read_text())
    assert gate["status"] == "PASS_EXACT_SOURCE_GATE_EQUIVALENCE"
    save("protocol.json", {"status": "FROZEN_N131_INVERSE_TRACE_BEFORE_CONTROL_AND_QUERY",
                           "candidate_id": None,
                           "curve_id": target["curve_id"],
                           "workload_id": target["workload_id"],
                           "public_target": target["public_target"],
                           "raw_preimage_index": 0,
                           "terminal_state_index": 0,
                           "terminal_state": selected(),
                           "free_pair_slots": 8,
                           "free_pair_rotations": terminal.ROTATIONS,
                           "eligible_source_codes_per_slot": gate["canonical_codes"],
                           "source_gate": "two_nonzero_inverse_witnesses_with_zero_trace",
                           "source_count_distinct_column_ordered_tuples": str(signed_tuples),
                           "uniform_raw_point_mean_upper_exact": f"{mean.numerator}/{mean.denominator}",
                           "uniform_raw_point_mean_upper_decimal": format(float(mean), ".12g"),
                           "online_total_cap_seconds": ONLINE_CAP,
                           "combined_rss_cap_bytes": RSS_CAP,
                           "worker_count": 1, "solver_flags": FLAGS,
                           "source_sha256": {name: sha(path) for name, path in sources().items()}})
    print("FROZEN_N131_INVERSE_TRACE", format(float(mean), ".9g"))


def check_protocol():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["status"] == "FROZEN_N131_INVERSE_TRACE_BEFORE_CONTROL_AND_QUERY"
    assert protocol["source_sha256"] == {name: sha(path) for name, path in sources().items()}
    assert protocol["terminal_state"] == selected()
    return protocol


def fixed_residual(raw_target):
    point = terminal.prepare.subtract(raw_target, selected()["rotated_raw_point"])
    assert point is not None and point[0] not in (0, 1)
    a = terminal.independent.inverse(point[0])
    assert terminal.independent.mul(a, point[0]) == 1
    return {"point": list(point), "standard_reciprocal": a}


def build_inverse(residual_value):
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
                  else algebra.expression(((-1, residual_value),)))
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
                     "inverse_witnesses": inverse_witnesses}


def control():
    check_protocol()
    fixture = json.loads((BASE / "control_fixture.json").read_text())
    residual = fixed_residual(fixture["raw_target"])
    expected = terminal.base.standard_reciprocal(fixture["intermediate_z"][6])
    assert residual["standard_reciprocal"] == expected
    start = time.monotonic_ns()
    circuit, wires = build_inverse(expected)
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
    save("control_result.json", {"status": "PASS_N131_INVERSE_TRACE_CONSTRUCTED_CONTROL",
                                 "candidate_id": None,
                                 "terminal_state_index": 0,
                                 "residual": residual,
                                 "branch_bits": branch_bits,
                                 "primary_variables": len(initial),
                                 "assignment_check": checked,
                                 "formula": terminal.base.profile(circuit, path,
                                                                  (built-start)/1e9,
                                                                  (written-built)/1e9),
                                 "protocol_sha256": sha(HERE / "protocol.json")})
    print("PASS_N131_INVERSE_TRACE_CONSTRUCTED_CONTROL", flush=True)


def query():
    protocol = check_protocol()
    control_receipt = json.loads((HERE / "control_result.json").read_text())
    assert control_receipt["status"] == "PASS_N131_INVERSE_TRACE_CONSTRUCTED_CONTROL"
    target = terminal.base.target_record()
    t0 = time.monotonic_ns()
    residual = fixed_residual(target["preimages"][0]["point"])
    t1 = time.monotonic_ns()
    circuit, wires = build_inverse(residual["standard_reciprocal"])
    t2 = time.monotonic_ns()
    formula = HERE / "ordinary.xcnf"
    circuit.write(formula)
    t3 = time.monotonic_ns()
    profile = terminal.base.profile(circuit, formula, (t2-t1)/1e9, (t3-t2)/1e9)
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
    t4 = time.monotonic_ns()
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
        decoded = {"selected_codes": [decode(bits) for bits in wires["selectors"]],
                   "pair_standard_reciprocals": [decode(bits) for bits in wires["outputs"]],
                   "middle_standard_reciprocals": [decode(bits) for bits in wires["middle"]],
                   "branch_bits": [int(wire in positive) for wire in wires["branches"]],
                   "inverse_witnesses": [[decode(bits) for bits in slot]
                                         for slot in wires["inverse_witnesses"]],
                   "formula_sha256": profile["xcnf_sha256"]}
        save("decoded_model.json", decoded)
    t5 = time.monotonic_ns()
    phases = {"target_residual_generation_ns": t1-t0,
              "formula_construction_ns": t2-t1,
              "formula_serialization_ns": t3-t2,
              "solver_search_ns": t4-t3,
              "terminal_parse_and_decode_ns": t5-t4}
    assert sum(phases.values()) == t5-t0
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    save("query_result.json", {"status": status, "candidate_id": None,
                               "curve_id": protocol["curve_id"],
                               "workload_id": protocol["workload_id"],
                               "public_target": protocol["public_target"],
                               "raw_preimage_index": 0,
                               "raw_target": target["preimages"][0]["point"],
                               "terminal_state_index": 0,
                               "residual": residual,
                               "phase_ns": phases,
                               "target_dependent_attempt_ns": t5-t0,
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
    print(json.dumps({"status": status, "online_attempt_seconds": (t5-t0)/1e9,
                      "solver_cpu_seconds_sampled": cpu_sample,
                      "peak_rss": peak}), flush=True)


if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] in ("gate", "freeze", "control", "query")
    {"gate": gate_equivalence, "freeze": freeze,
     "control": control, "query": query}[sys.argv[1]]()
