"""Output-first BDD of exact N41 pair reciprocals with three S3 links."""

import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
FOURPAIR = GOAL / "n131_w18_allseed_fourpair_20261012"
FUNCTIONAL = GOAL / "n41_w8_tenpair_functional_20261012"
PARENT = GOAL / "n41_allseed_fourpair_forward_20261012"
SOURCE = FOURPAIR / "n41_diagonal/pairs.tsv"
FIXTURE = FOURPAIR / "n41_diagonal/control_fixture.json"
sys.path[:0] = [str(FOURPAIR), str(FUNCTIONAL)]
import fourpair_v2 as source  # noqa: E402
import build as forward  # noqa: E402
from karatsuba_circuit import KaratsubaCircuit  # noqa: E402

_run_spec = importlib.util.spec_from_file_location("functional_run", FUNCTIONAL / "run.py")
prior_run = importlib.util.module_from_spec(_run_spec)
_run_spec.loader.exec_module(prior_run)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with path.open("x") as out:
        json.dump(value, out, sort_keys=True, indent=2)
        out.write("\n")


def load_pairs():
    rows = [[] for _ in range(4)]
    targets = {}
    lines = SOURCE.read_text().splitlines()
    assert lines[0] == "ECC2K41_ALLSEED4 4 4"
    for line in lines[1:]:
        parts = line.split()
        if parts[0] == "T":
            targets[int(parts[1])] = tuple(map(int, parts[2:]))
            continue
        assert parts[0] == "S" and len(parts) == 11
        slot, state_id, a, b, ca, cb, sa, sb, x, y = map(int, parts[1:])
        assert state_id == len(rows[slot]) and a < b and ca != cb
        assert x != 0
        rows[slot].append({"id": state_id, "masks": [a, b], "columns": [ca, cb],
                           "signs": [sa, sb], "point": [x, y]})
    assert all(len(row) == 30952 for row in rows)
    assert len(targets) == 4
    return rows, targets


def batch_inverse(field, values):
    assert values and all(values)
    prefix = [1]
    for value in values:
        prefix.append(field.mul(prefix[-1], value))
    inverse = field.inverse(prefix[-1])
    output = [0] * len(values)
    for index in range(len(values) - 1, -1, -1):
        output[index] = field.mul(inverse, prefix[index])
        inverse = field.mul(inverse, values[index])
    assert inverse == 1
    for index in (0, len(values) // 2, len(values) - 1):
        assert field.mul(values[index], output[index]) == 1
    return output


def census():
    start = time.monotonic_ns()
    rows, targets = load_pairs()
    field, _, _ = source.field_config("n41")
    fixture = json.loads(FIXTURE.read_text())
    sets = []
    stats = []
    for slot, states in enumerate(rows):
        xs = sorted({state["point"][0] for state in states})
        reciprocals = sorted(batch_inverse(field, xs))
        assert len(reciprocals) == len(xs)
        root, nodes = source.bdd(set(reciprocals), 41)
        assert fixture["pair_reciprocals"][slot] in reciprocals
        sets.append(reciprocals)
        stats.append({"slot": slot, "signed_pair_states": len(states),
                      "distinct_pair_x": len(xs), "reciprocal_set": len(reciprocals),
                      "bdd_nodes": len(nodes), "bdd_root": root})
    save(HERE / "output_values.json", {"slots": sets, "source_sha256": sha(SOURCE)})
    save(HERE / "census_result.json", {
        "status": "PASS_EXACT_N41_PAIR_OUTPUT_BDD_CENSUS", "candidate_id": None,
        "slots": stats, "raw_targets": {str(k): list(v) for k, v in targets.items()},
        "source_sha256": sha(SOURCE), "fixture_sha256": sha(FIXTURE),
        "output_values_sha256": sha(HERE / "output_values.json"),
        "source_sha256_code": sha(__file__), "wall_ns": time.monotonic_ns() - start})
    print("CENSUS", [(row["reciprocal_set"], row["bdd_nodes"]) for row in stats], flush=True)


def construct():
    census_data = json.loads((HERE / "census_result.json").read_text())
    values = json.loads((HERE / "output_values.json").read_text())
    fixture = json.loads(FIXTURE.read_text())
    parent_chart = json.loads((PARENT / "chart.json").read_text())
    assert census_data["status"] == "PASS_EXACT_N41_PAIR_OUTPUT_BDD_CENSUS"
    assert values["source_sha256"] == sha(SOURCE)
    assert sha(HERE / "output_values.json") == census_data["output_values_sha256"]
    start = time.monotonic_ns()
    circuit = KaratsubaCircuit(41, [0, 3])
    outputs = []
    bdd_nodes = []
    for slot_values in values["slots"]:
        bits = [circuit.variable() for _ in range(41)]
        root, nodes = source.bdd(set(slot_values), 41)
        source.emit_bdd(circuit, bits, root, nodes)
        outputs.append(bits)
        bdd_nodes.append(len(nodes))
    nodes = list(outputs)
    branches = []
    for left, right in ((0, 1), (2, 3), (4, 5)):
        output, branch = forward.s3_forward(circuit, nodes[left], nodes[right])
        nodes.append(output)
        branches.append(branch)
    circuit.require_zero(circuit.add(nodes[-1], circuit.constant(fixture["target_reciprocal"])))
    built = time.monotonic_ns()
    primary = {}
    for bits, reciprocal in zip(outputs, fixture["pair_reciprocals"]):
        primary.update({wire: reciprocal >> bit & 1 for bit, wire in enumerate(bits)})
    for wire, bit in zip(branches, parent_chart["root_branch_bits"][4:]):
        primary[wire] = bit
    complete = prior_run.complete_assignment(circuit, primary)
    checks = prior_run.check_assignment(circuit, complete)
    checked = time.monotonic_ns()
    formula = HERE / "public.xcnf"
    circuit.write(formula)
    written = time.monotonic_ns()
    save(HERE / "build_result.json", {
        "status": "PASS_N41_OUTPUT_BDD_CONSTRUCTED_ASSIGNMENT", "candidate_id": None,
        "variables": circuit.next_var - 1, "and_gates": circuit.and_count,
        "cnf_clauses": len(circuit.clauses), "native_xor_rows": len(circuit.xors),
        "bdd_nodes": bdd_nodes, "pair_output_bits": outputs, "root_branch_wires": branches,
        "positive_assignment_checks": checks,
        "build_ns": built - start, "check_ns": checked - built,
        "write_ns": written - checked,
        "formula_bytes": formula.stat().st_size, "formula_sha256": sha(formula),
        "source_sha256": sha(__file__), "census_sha256": sha(HERE / "census_result.json")})
    print("BUILT", circuit.next_var - 1, len(circuit.clauses), len(circuit.xors), flush=True)


if __name__ == "__main__":
    {"census": census, "construct": construct}[sys.argv[1]]()
