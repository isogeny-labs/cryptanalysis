"""Four-fiber W18 residual selector with a target-conditioned trace parity row."""

import hashlib
import json
import resource
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / "n131_fixed_seed_ninepair_cubic_20261011"
VERIFY = ROOT / "n131_fixed_seed_halftrace_cubic_20261011"
sys.path.insert(0, str(BASE))
import run as base  # noqa: E402
sys.path.insert(0, str(VERIFY))
import verify as independent  # noqa: E402
import prepare  # noqa: E402
import batch  # noqa: E402

ROTATIONS = base.ROTATIONS[:7]
SOLVER_CAP = 590
TOTAL_CAP_NS = 600 * 10**9
PARSE_RESERVE_NS = 2 * 10**9
SOLVER_FLAGS = ["--threads=1", "--maxtime=590", "--zero-exit-status",
                "--verb=1", "--printsol=1"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, data):
    with (HERE / name).open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def sources():
    return {"terminal": Path(__file__), "preparer": HERE / "prepare.py",
            "batch": HERE / "batch.py",
            "n41_control": HERE / "n41_control.py",
            "n41_control_result": HERE / "n41_control_result.json",
            "trace_audit": HERE / "trace_audit.py",
            "trace_audit_result": HERE / "trace_audit_result.json",
            "sage_runtime": HERE / "sage_runtime_info.json",
            "prior_batch_verification": ROOT / "n131_w18_two_terminal_batch_residual_20261017" / "verification.json",
            "pool": HERE / "pool.json", "control_fixture": HERE / "control_fixture.json",
            "coverage_protocol": ROOT / "n131_w18_two_terminal_coverage_20261015" / "protocol.json",
            "coverage_result": ROOT / "n131_w18_two_terminal_coverage_20261015" / "count_result.json",
            "serial": BASE / "run.py", "pair": base.OLD / "fixed_pair_circuit.py",
            "sparse": ROOT / "n41_basis_aware_quartic_20261011" / "sparse.py",
            "karatsuba": ROOT.parent / "koblitz-polynomial-w-pair-20260925" / "karatsuba_circuit.py",
            "circuit_sat": ROOT.parent / "koblitz-s5-invariant-20260924" / "circuit_sat.py",
            "support": base.SUPPORT, "fixture": BASE / "control_fixture.json",
            "group": VERIFY / "verify.py", "target": base.OLD / "target_preimages.json",
            "solver": base.SOLVER.resolve()}


def pool():
    data = json.loads((HERE / "pool.json").read_text())
    assert data["status"] == "PASS_FROZEN_TWO_TERMINAL48_POOL"
    assert len(data["left_states"]) == len(data["right_states"]) == 48
    assert len(data["joint_states"]) == 2080
    return data


def freeze():
    target = base.target_record()
    n41 = json.loads((HERE / "n41_control_result.json").read_text())
    assert n41["status"] == "PASS_UNPINNED_N41_FOURFIBER_SELECTOR_CONTROL"
    assert [row["matches_unpinned_free_five"] for row in n41["raw_fibers"]] == [True, False, False, False]
    trace_audit = json.loads((HERE / "trace_audit_result.json").read_text())
    assert trace_audit["status"] == "PASS_FOURFIBER_TRACE_PARITY_PREFLIGHT"
    assert trace_audit["public_rows_checked"] == 8320
    counts = json.loads(sources()["coverage_result"].read_text())
    assert counts["status"] == "PASS_EXACT_TWO_TERMINAL_SOURCE_COUNT"
    assert counts["first_prefix_permitting_one_raw_half"] == 12
    _, root, nodes = base.source_domain()
    assert root >= 2 and len(nodes) == 13093 and base.SOLVER.is_file()
    save("protocol.json", {"status": "FROZEN_FOURFIBER_TRACE_PARITY_BEFORE_QUERY",
                           "candidate_id": None,
                           "curve_id": target["curve_id"],
                           "workload_id": target["workload_id"],
                           "public_target": target["public_target"],
                           "raw_preimage_indices": [0, 1, 2, 3],
                           "raw_preimages": [row["point"] for row in target["preimages"]],
                           "fixed_seed_mask": base.pair.SEED,
                           "free_pair_rotations": ROTATIONS,
                           "terminal_rotations": [112, 128],
                           "source_codes_per_free_pair": 33191,
                           "terminal_signed_states_per_slot": 48,
                           "admissible_joint_terminal_states": 2080,
                           "distinct_joint_raw_sums": pool()["distinct_joint_raw_sums"],
                           "terminal_selection_law": "four-fiber two-terminal selector plus one exact target-conditioned trace parity row across all nine pair outputs",
                           "worker_count": 1,
                           "solver_flags": SOLVER_FLAGS,
                           "solver_cap_seconds": SOLVER_CAP,
                           "target_dependent_cap_seconds": TOTAL_CAP_NS // 10**9,
                           "parse_reserve_seconds": PARSE_RESERVE_NS // 10**9,
                           "combined_rss_cap_bytes": base.RSS_CAP,
                           "source_sha256": {name: sha(path) for name, path in sources().items()}})


def check_protocol():
    data = json.loads((HERE / "protocol.json").read_text())
    assert data["status"] == "FROZEN_FOURFIBER_TRACE_PARITY_BEFORE_QUERY"
    assert data["source_sha256"] == {name: sha(path) for name, path in sources().items()}
    assert data["solver_flags"] == SOLVER_FLAGS
    return data


def residuals(raw_targets, joint_states):
    assert len(raw_targets) == 4 and len({tuple(x) for x in raw_targets}) == 4
    result = []
    for index, target in enumerate(raw_targets):
        rows, stats = batch.residuals(target, joint_states, independent)
        assert stats['batch_inversions'] == 2
        result.extend({'raw_preimage_index': index, **row} for row in rows)
    assert len(result) == 4 * 2080
    return result


def build(residual_rows, raw_targets, bdd_root, bdd_nodes):
    pair = base.pair
    circuit = base.KaratsubaCircuit(pair.N, [0, 1, 2, 13])
    algebra = base.Algebra(circuit, base.Field(), dense_and_threshold=3000)
    h2 = pair.gf_square(pair.gf_half_trace(pair.coordinate(pair.SEED)))
    coefficient = 1 ^ h2
    selectors, outputs, rotated = [], [], []
    for rotation in ROTATIONS:
        bits = [circuit.variable() for _ in range(17)]
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
        images = [pair.gf_frobenius(1 << bit, rotation) for bit in range(pair.N)]
        rotated.append(algebra.from_bits(circuit.linear_element(out, images)))

    choices_a = [circuit.variable() for _ in range(48)]
    choices_b = [circuit.variable() for _ in range(48)]
    choices_raw = [circuit.variable() for _ in range(4)]
    for choices in (choices_a, choices_b, choices_raw):
        circuit.clauses.append(" ".join(map(str, choices)) + " 0")
        for index, left in enumerate(choices):
            for right in choices[index + 1:]:
                circuit.clauses.append(f"-{left} -{right} 0")
    lookup = {(row["raw_preimage_index"], row["left_state_id"], row["right_state_id"]):
              row["standard_reciprocal"] for row in residual_rows}
    assert len(lookup) == 4 * 2080
    pair_terms = []
    forbidden = 0
    exceptional = 0
    for i, left in enumerate(choices_a):
        for j, right in enumerate(choices_b):
            if (0, i, j) not in lookup:
                circuit.clauses.append(f"-{left} -{right} 0")
                forbidden += 1
            else:
                joined = circuit.and_(left, right)
                for raw, raw_wire in enumerate(choices_raw):
                    value = lookup[(raw, i, j)]
                    if value is None:
                        circuit.clauses.append(f"-{left} -{right} -{raw_wire} 0")
                        exceptional += 1
                    else:
                        pair_terms.append((circuit.and_(joined, raw_wire), value))
    assert len(pair_terms) + exceptional + 4 * forbidden == 4 * 48**2
    selected_residual = algebra.expression(pair_terms)
    middle = [[circuit.variable() for _ in range(pair.N)] for _ in range(5)]
    branches = [circuit.variable() for _ in range(6)]
    ht_basis, trace_basis = [], []
    for bit in range(pair.N):
        value, image = pair.gf_square(1 << bit), 0
        for _ in range((pair.N + 1) // 2):
            image ^= value
            value = pair.gf_square(pair.gf_square(value))
        ht_basis.append(image)
        trace_basis.append(base.trace(1 << bit))
    terminal_pool = pool()
    left_traces = [base.trace(base.inverse(state["rotated_raw_point"][0]))
                   for state in terminal_pool["left_states"]]
    right_traces = [base.trace(base.inverse(state["rotated_raw_point"][0]))
                    for state in terminal_pool["right_states"]]
    raw_traces = [base.trace(base.inverse(point[0])) for point in raw_targets]
    parity_lits = [wire for output in outputs for bit, wire in enumerate(output)
                   if trace_basis[bit]]
    parity_lits += [wire for wire, bit in zip(choices_a, left_traces) if bit]
    parity_lits += [wire for wire, bit in zip(choices_b, right_traces) if bit]
    parity_lits += [wire for wire, bit in zip(choices_raw, raw_traces) if bit]
    circuit.require_zero([circuit.xor(parity_lits)])
    running = rotated[0]
    for index in range(1, 7):
        output = (algebra.from_bits(middle[index - 1]) if index < 6
                  else selected_residual)
        total = algebra.add(running, rotated[index], output)
        ht = circuit.linear_element(total.bits(), ht_basis)
        circuit.require_zero(algebra.add(
            algebra.mul(algebra.mul(running, rotated[index]), output),
            algebra.from_bits(ht),
            algebra.expression(((branches[index - 1], 1),))).bits())
        circuit.require_zero([circuit.xor(
            wire for wire, bit in zip(total.bits(), trace_basis) if bit)])
        if index < 6:
            circuit.clauses.append(" ".join(map(str, middle[index - 1])) + " 0")
        running = output

    for bits in selectors:
        literals = {0: 0, 1: -1}
        for node in sorted(bdd_nodes):
            bit, low, high = bdd_nodes[node]
            left, right = literals[low], literals[high]
            literals[node] = circuit.xor((
                left, circuit.and_(bits[bit], circuit.xor((left, right)))))
        circuit.clauses.append(str(literals[bdd_root]) + " 0")
    return circuit, {"selectors": selectors, "outputs": outputs,
                     "middle": middle, "branches": branches,
                     "choices_a": choices_a, "choices_b": choices_b,
                     "choices_raw": choices_raw,
                     "trace_parity_literals": len(parity_lits),
                     "raw_target_trace_bits": raw_traces,
                     "active_pair_terms": len(pair_terms),
                     "forbidden_joint_choices": forbidden,
                     "exceptional_raw_joint_choices": exceptional}


def control():
    check_protocol()
    fixture = json.loads((BASE / "control_fixture.json").read_text())
    control_fixture = json.loads((HERE / "control_fixture.json").read_text())
    state_pool = pool()
    torsion = (None, (0, 1), (1, 0), (1, 1))
    control_targets = [list(independent.point_add(tuple(control_fixture["raw_target"]), offset))
                       for offset in torsion]
    assert len({tuple(x) for x in control_targets}) == 4
    residual_rows = residuals(control_targets,
                              state_pool["joint_states"])
    chosen_a, chosen_b = (control_fixture["left_state_id"],
                          control_fixture["right_state_id"])
    expected = base.standard_reciprocal(fixture["intermediate_z"][5])
    assert next(row["standard_reciprocal"] for row in residual_rows
                if row["raw_preimage_index"] == 0 and
                   row["left_state_id"] == chosen_a and
                   row["right_state_id"] == chosen_b) == expected
    _, root, nodes = base.source_domain()
    start = time.monotonic_ns()
    circuit, wires = build(residual_rows, control_targets, root, nodes)
    constructed = time.monotonic_ns()
    formula = HERE / "control.xcnf"
    circuit.write(formula)
    written = time.monotonic_ns()
    initial = {}
    def bind(bits, value):
        initial.update({wire: value >> bit & 1 for bit, wire in enumerate(bits)})
    h2 = base.pair.gf_square(base.pair.gf_half_trace(base.pair.coordinate(base.pair.SEED)))
    for item in fixture["selected"][:7]:
        slot = item["slot"]
        code = base.pair.selector_code(item["masks"][0])
        a = base.standard_reciprocal(item["unrotated_pair_output_z"])
        product = base.pair.product_from_code(code)
        assert base.pair.gf_mul(1 ^ h2, base.pair.gf_square(a)) ^ base.pair.gf_mul(a, product) ^ h2 == 0
        assert base.pair.gf_frobenius(a, item["rotation"]) == base.standard_reciprocal(fixture["pair_rotated_z"][slot])
        bind(wires["selectors"][slot], code)
        bind(wires["outputs"][slot], a)
    for bits, z in zip(wires["middle"], fixture["intermediate_z"][:5]):
        bind(bits, base.standard_reciprocal(z))
    for index, wire in enumerate(wires["choices_a"]):
        initial[wire] = int(index == chosen_a)
    for index, wire in enumerate(wires["choices_b"]):
        initial[wire] = int(index == chosen_b)
    for index, wire in enumerate(wires["choices_raw"]):
        initial[wire] = int(index == 0)
    rotated = [base.standard_reciprocal(z) for z in fixture["pair_rotated_z"][:7]]
    middle = [base.standard_reciprocal(z) for z in fixture["intermediate_z"][:5]]
    left, branch_bits = rotated[0], []
    for index in range(1, 7):
        right = middle[index - 1] if index < 6 else expected
        total = left ^ rotated[index] ^ right
        branch = base.pair.gf_mul(base.pair.gf_mul(left, rotated[index]), right) ^ base.halftrace(base.pair.gf_square(total))
        assert branch in (0, 1)
        initial[wires["branches"][index - 1]] = branch
        branch_bits.append(branch)
        left = right
    checked = base.check_assignment(circuit, base.complete_assignment(circuit, initial))
    save("control_result.json", {"status": "PASS_EXACT_N131_FOURFIBER_TRACE_PARITY_CONTROL",
                                 "candidate_id": None,
                                 "control_choice_indices": [chosen_a, chosen_b],
                                 "control_raw_target": control_fixture["raw_target"],
                                 "control_raw_targets": control_targets,
                                 "residuals": residual_rows,
                                 "branch_bits": branch_bits,
                                 "primary_variables": len(initial),
                                 "active_joint_pair_terms": wires["active_pair_terms"],
                                 "trace_parity_literals": wires["trace_parity_literals"],
                                 "raw_target_trace_bits": wires["raw_target_trace_bits"],
                                 "forbidden_joint_choices": wires["forbidden_joint_choices"],
                                 "exceptional_raw_joint_choices": wires["exceptional_raw_joint_choices"],
                                 "assignment_check": checked,
                                 "formula": base.profile(circuit, formula,
                                                         (constructed-start)/1e9,
                                                         (written-constructed)/1e9),
                                 "protocol_sha256": sha(HERE / "protocol.json")})
    print("PASS_EXACT_N131_FOURFIBER_TWO_TERMINAL_CONTROL", flush=True)


def query():
    protocol = check_protocol()
    control_result = json.loads((HERE / "control_result.json").read_text())
    assert control_result["status"] == "PASS_EXACT_N131_FOURFIBER_TRACE_PARITY_CONTROL"
    target = base.target_record()
    raw_targets = [row["point"] for row in target["preimages"]]
    assert len(raw_targets) == 4
    _, root, nodes = base.source_domain()
    t0 = time.monotonic_ns()
    residual_rows = residuals(raw_targets, pool()["joint_states"])
    t1 = time.monotonic_ns()
    circuit, wires = build(residual_rows, raw_targets, root, nodes)
    t2 = time.monotonic_ns()
    formula = HERE / "ordinary.xcnf"
    circuit.write(formula)
    t3 = time.monotonic_ns()
    details = base.profile(circuit, formula, (t2-t1)/1e9, (t3-t2)/1e9)
    del circuit
    print(json.dumps({"phase": "frozen_ordinary_formula", "formula": details}), flush=True)
    outpath, errpath = HERE / "solver.stdout.txt", HERE / "solver.stderr.txt"
    parent = psutil.Process()
    peak, stop_reason = 0, None
    solver_budget_seconds = min(
        SOLVER_CAP,
        max(0, (TOTAL_CAP_NS - (t3 - t0) - PARSE_RESERVE_NS) // 10**9))
    actual_solver_flags = [
        f"--maxtime={solver_budget_seconds}" if flag.startswith("--maxtime=")
        else flag for flag in SOLVER_FLAGS]
    with outpath.open("x") as stdout, errpath.open("x") as stderr:
        if solver_budget_seconds == 0:
            stop_reason, code = "PRE_SOLVER_TOTAL_CAP", None
        else:
            process = subprocess.Popen(
                [str(base.SOLVER), *actual_solver_flags, str(formula)],
                stdout=stdout, stderr=stderr)
            child = psutil.Process(process.pid)
            while process.poll() is None:
                try:
                    combined = parent.memory_info().rss + child.memory_info().rss
                except psutil.NoSuchProcess:
                    combined = parent.memory_info().rss
                peak = max(peak, combined)
                if combined > base.RSS_CAP:
                    stop_reason = "RSS_CAP"
                    process.kill()
                    break
                if time.monotonic_ns() - t0 > TOTAL_CAP_NS - PARSE_RESERVE_NS:
                    stop_reason = "TARGET_DEPENDENT_TIMEOUT"
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
                   "terminal_choice_indices": [
                       next(index for index, wire in enumerate(wires[key])
                            if wire in positive)
                       for key in ("choices_a", "choices_b")],
                   "raw_preimage_index": next(index for index, wire in
                       enumerate(wires["choices_raw"]) if wire in positive),
                   "formula_sha256": details["xcnf_sha256"]}
        save("decoded_model.json", decoded)
    t5 = time.monotonic_ns()
    phase = {"target_residual_generation_ns": t1-t0,
             "formula_construction_ns": t2-t1,
             "formula_serialization_ns": t3-t2,
             "solver_search_ns": t4-t3,
             "terminal_parse_and_model_decode_ns": t5-t4}
    assert sum(phase.values()) == t5-t0
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    save("query_result.json", {"status": status, "candidate_id": None,
                               "curve_id": protocol["curve_id"],
                               "workload_id": protocol["workload_id"],
                               "public_target": protocol["public_target"],
                               "raw_preimage_indices": [0, 1, 2, 3],
                               "raw_targets": raw_targets,
                               "residuals": residual_rows,
                               "active_joint_pair_terms": wires["active_pair_terms"],
                               "trace_parity_literals": wires["trace_parity_literals"],
                               "raw_target_trace_bits": wires["raw_target_trace_bits"],
                               "forbidden_joint_choices": wires["forbidden_joint_choices"],
                               "exceptional_raw_joint_choices": wires["exceptional_raw_joint_choices"],
                               "phase_ns": phase,
                               "target_dependent_attempt_ns": t5-t0,
                               "formula": details, "worker_count": 1,
                               "solver_flags": actual_solver_flags,
                               "solver_budget_seconds": solver_budget_seconds,
                               "target_dependent_cap_seconds": TOTAL_CAP_NS // 10**9,
                               "solver_exit_code": code, "stop_reason": stop_reason,
                               "peak_combined_rss_bytes_sampled": peak,
                               "parent_peak_rss_bytes": rss if sys.platform == "darwin" else rss*1024,
                               "status_lines": [line for line in output.splitlines() if line.startswith("s ")],
                               "restart_rows": sum(line.startswith("c rst") for line in output.splitlines()),
                               "decoded_model_saved": decoded is not None,
                               "stdout_sha256": sha(outpath), "stderr_sha256": sha(errpath),
                               "protocol_sha256": sha(HERE / "protocol.json")})
    print(json.dumps({"status": status,
                      "attempt_seconds": (t5-t0)/1e9,
                      "peak_rss": peak}), flush=True)


if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] in ("freeze", "control", "query")
    {"freeze": freeze, "control": control, "query": query}[sys.argv[1]]()
