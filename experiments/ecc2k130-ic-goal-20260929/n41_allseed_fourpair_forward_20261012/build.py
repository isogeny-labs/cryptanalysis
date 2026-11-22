"""Source-bound forward S3 circuit on the frozen four-pair public point."""

import hashlib
import importlib.util
import json
import sys
import time
from collections import defaultdict
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
FOURPAIR = GOAL / "n131_w18_allseed_fourpair_20261012"
FUNCTIONAL = GOAL / "n41_w8_tenpair_functional_20261012"
sys.path[:0] = [str(FOURPAIR), str(FUNCTIONAL)]
import fourpair_v2 as source  # noqa: E402
import build as forward  # noqa: E402
from karatsuba_circuit import KaratsubaCircuit  # noqa: E402

_run_spec = importlib.util.spec_from_file_location("functional_run", FUNCTIONAL / "run.py")
prior_run = importlib.util.module_from_spec(_run_spec)
_run_spec.loader.exec_module(prior_run)

FIXTURE = FOURPAIR / "n41_diagonal/control_fixture.json"
GEOMETRY = GOAL / "n41_w7_entropy_cubic_20261011/w8/geometry.json"
TREE = ((0, 1), (2, 3), (4, 5), (6, 7), (8, 9), (10, 11), (12, 13))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with path.open("x") as out:
        json.dump(value, out, sort_keys=True, indent=2)
        out.write("\n")


def chart():
    fixture = json.loads(FIXTURE.read_text())
    geometry = json.loads(GEOMETRY.read_text())
    rows = {int(row["mask"]): row for row in geometry["rows"]}

    def negate(point):
        return (point[0], point[1] ^ point[0])

    def frob(point, count):
        for _ in range(count):
            point = (forward.square(point[0]), forward.square(point[1]))
        return point

    leaves = []
    masks = []
    for slot, (pair, signs) in enumerate(zip(fixture["masks"], fixture["sign_bits"])):
        for mask, sign in zip(pair, signs):
            original = tuple(rows[mask]["raw_point"])
            diagonal = forward.add(original, frob(original, 1))
            assert diagonal is not None and diagonal[0]
            assert forward.inv(diagonal[0]) == mask << 1
            leaf = frob(negate(diagonal) if sign else diagonal, fixture["rotations"][slot])
            leaves.append(leaf)
            masks.append(mask)
    nodes = list(leaves)
    branches = []
    for left, right in TREE:
        point = forward.add(nodes[left], nodes[right])
        assert point is not None and point[0]
        a, b, z = (forward.inv(nodes[left][0]), forward.inv(nodes[right][0]),
                   forward.inv(point[0]))
        choices = [bit for bit in (0, 1) if forward.root_value(a, b, bit) == z]
        assert choices
        branches.append(choices[0])
        nodes.append(point)
    assert nodes[-1] == tuple(fixture["raw_target"])
    assert forward.inv(nodes[-1][0]) == fixture["target_reciprocal"]
    save(HERE / "chart.json", {
        "status": "PASS_N41_FOURPAIR_FORWARD_POSITIVE_CHART",
        "candidate_id": None, "masks": masks,
        "sign_bits": [bit for pair in fixture["sign_bits"] for bit in pair],
        "root_branch_bits": branches,
        "point_chain": [list(point) for point in nodes],
        "target_reciprocal": fixture["target_reciprocal"],
        "fixture_sha256": sha(FIXTURE), "geometry_sha256": sha(GEOMETRY),
        "source_sha256": sha(__file__)})
    print("PASS_CHART", branches, flush=True)


def formula(name, target):
    field, width, rotations = source.field_config(name)
    support = source.support(name)
    root, bddnodes = source.bdd(set(support), width)
    taps = [i for i in range(field.n) if field.modulus >> i & 1]
    circuit = KaratsubaCircuit(field.n, taps)
    masks = []
    nodes = []
    for slot in range(4):
        for _ in range(2):
            bits = [circuit.variable() for _ in range(width)]
            masks.append(bits)
            source.emit_bdd(circuit, bits, root, bddnodes)
            basis = [field.frob(1 << (i + 1), rotations[slot]) for i in range(width)]
            nodes.append(circuit.linear_element(bits, basis))
    groups = defaultdict(list)
    for mask, column in support.items():
        groups[column].append(mask)
    collisions = [pair for group in groups.values()
                  for pair in combinations(sorted(group), 2)]

    def mismatch(bits, code):
        return [(-wire if code >> i & 1 else wire) for i, wire in enumerate(bits)]

    shield = 0
    for i in range(8):
        for j in range(i + 1, 8):
            different = [circuit.xor((a, b)) for a, b in zip(masks[i], masks[j])]
            circuit.clauses.append(" ".join(map(str, different)) + " 0")
            for a, b in collisions:
                for first, second in ((a, b), (b, a)):
                    circuit.clauses.append(" ".join(map(str,
                        mismatch(masks[i], first) + mismatch(masks[j], second))) + " 0")
                    shield += 1
    branches = []
    for left, right in TREE:
        output, branch = forward.s3_forward(circuit, nodes[left], nodes[right])
        nodes.append(output)
        branches.append(branch)
    circuit.require_zero(circuit.add(nodes[-1], circuit.constant(target)))
    return circuit, {"masks": masks, "branches": branches, "nodes": nodes}, {
        "field": name, "source_masks": len(support), "source_bdd_nodes": len(bddnodes),
        "same_column_mask_pairs": len(collisions), "column_shield_clauses": shield,
        "rotations": rotations, "target_reciprocal": target,
        "s3_links": len(TREE), "source_width": width}


def build_n41():
    chart_data = json.loads((HERE / "chart.json").read_text())
    fixture = json.loads(FIXTURE.read_text())
    assert chart_data["fixture_sha256"] == sha(FIXTURE)
    start = time.monotonic_ns()
    circuit, wires, meta = formula("n41", fixture["target_reciprocal"])
    constructed = time.monotonic_ns()
    initial = {}
    for bits, mask in zip(wires["masks"], chart_data["masks"]):
        initial.update({wire: mask >> i & 1 for i, wire in enumerate(bits)})
    initial.update({wire: bit for wire, bit in
                    zip(wires["branches"], chart_data["root_branch_bits"])})
    values = prior_run.complete_assignment(circuit, initial)
    checks = prior_run.check_assignment(circuit, values)
    checked = time.monotonic_ns()
    output = HERE / "n41_public.xcnf"
    circuit.write(output)
    written = time.monotonic_ns()
    save(HERE / "build_result.json", {
        "status": "PASS_N41_FORWARD_CONSTRUCTED_FULL_ASSIGNMENT",
        "candidate_id": None, "metadata": meta,
        "variables": circuit.next_var - 1, "and_gates": circuit.and_count,
        "cnf_clauses": len(circuit.clauses), "native_xor_rows": len(circuit.xors),
        "positive_assignment_checks": checks, "primary_mask_bits": len(initial) - len(wires["branches"]),
        "root_branch_bits": len(wires["branches"]),
        "build_ns": constructed - start, "check_ns": checked - constructed,
        "write_ns": written - checked,
        "formula_bytes": output.stat().st_size,
        "formula_sha256": sha(output), "source_sha256": sha(__file__),
        "chart_sha256": sha(HERE / "chart.json")})
    print("PASS_N41_FORWARD_CONTROL", circuit.next_var - 1,
          len(circuit.clauses), len(circuit.xors), flush=True)


if __name__ == "__main__":
    {"chart": chart, "build_n41": build_n41}[sys.argv[1]]()
