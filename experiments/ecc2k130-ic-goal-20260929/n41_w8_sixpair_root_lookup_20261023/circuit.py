"""Exact N41 source-edge/root lookup feeding the balanced public S3 tree."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRIOR = ROOT / "n41_w8_sixpair_sat_20261016/circuit.py"
spec = importlib.util.spec_from_file_location("prior_sixpair", PRIOR)
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
F = prior.F
N = 41
ROTATIONS = [0, 6, 12, 18, 24, 30]


def source_table():
    g = prior.geometry()
    assert g["rotations"] == ROTATIONS
    masks = g["permitted_canonical_a"]
    assert len(masks) == 40 and len(set(masks)) == 40
    assert g["fixed_seed_sum_code"] == 56
    tables = []
    for block in g["blocks"][:6]:
        assert block["rotation"] == ROTATIONS[len(tables)]
        rows = []
        for mask in masks:
            states = [s for s in block["states"] if s["a"] == mask]
            roots = sorted({s["z"] for s in states})
            assert len(states) == 4 and len(roots) == 2
            assert all(sum(s["z"] == root for s in states) == 2 for root in roots)
            for state in states:
                assert prior.replay.on_curve(F, tuple(state["raw_sum"]))
                assert F.inv(state["raw_sum"][0]) == prior.frob(
                    state["z"], block["rotation"])
            rows.append(roots)
        tables.append(rows)
    assert all(table == tables[0] for table in tables)
    columns = g["mask_columns"]
    edges = [{columns[str(mask)], columns[str(mask ^ 56)]} for mask in masks]
    assert all(len(edge) == 2 for edge in edges)
    return {"masks": masks, "roots": tables[0], "edge_columns": edges,
            "geometry": g}


def build(target):
    assert target
    table = source_table()
    circ = prior.old.KaratsubaCircuit(N, [0, 3])
    alg = prior.old.Algebra(circ, prior.Field(), dense_and_threshold=3000)
    wires = {"edge": [], "branch": [], "out": [], "middle": []}
    nodes = []
    for rotation in ROTATIONS:
        choices = [circ.variable() for _ in table["masks"]]
        branch = circ.variable()
        wires["edge"].append(choices)
        wires["branch"].append(branch)
        circ.clauses.append(" ".join(map(str, choices)) + " 0")
        for i in range(len(choices)):
            for j in range(i + 1, len(choices)):
                circ.clauses.append(f"-{choices[i]} -{choices[j]} 0")
        branch_choices = [circ.and_(choice, branch) for choice in choices]
        out = []
        for bit in range(N):
            terms = [choice for choice, roots in zip(choices, table["roots"])
                     if (roots[0] >> bit) & 1]
            terms.extend(choose for choose, roots in zip(branch_choices, table["roots"])
                         if ((roots[0] ^ roots[1]) >> bit) & 1)
            out.append(circ.xor(terms))
        wires["out"].append(out)
        rotated = circ.linear_element(out, [prior.frob(1 << i, rotation)
                                            for i in range(N)])
        nodes.append(alg.from_bits(rotated))
    conflicts = 0
    for left in range(6):
        for right in range(left + 1, 6):
            for i, cols_i in enumerate(table["edge_columns"]):
                for j, cols_j in enumerate(table["edge_columns"]):
                    if cols_i & cols_j:
                        circ.clauses.append(f"-{wires['edge'][left][i]} "
                                            f"-{wires['edge'][right][j]} 0")
                        conflicts += 1
    for _ in range(4):
        middle = [circ.variable() for _ in range(N)]
        wires["middle"].append(middle)
        circ.clauses.append(" ".join(map(str, middle)) + " 0")
        nodes.append(alg.from_bits(middle))
    nodes.append(alg.expression(((-1, target),)))
    for i, j, k in prior.BALANCED_LINKS:
        a, b, z = nodes[i], nodes[j], nodes[k]
        abz = alg.mul(alg.mul(a, b), z)
        circ.require_zero(alg.add(alg.square(abz), abz,
                                  alg.square(alg.add(a, b)), alg.square(z)).bits())
    counts = {"and_gates": circ.and_count, "variables": circ.next_var - 1,
              "clauses": len(circ.clauses), "native_xor_rows": len(circ.xors),
              "sparse_mul_calls": alg.sparse_mul_calls,
              "generic_mul_calls": alg.generic_mul_calls,
              "cross_slot_column_conflicts": conflicts,
              "source_edges_per_slot": len(table["masks"])}
    return circ, wires, table, counts
