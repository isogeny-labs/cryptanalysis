"""Build paired source-constrained N41 formulas on one public point."""

import hashlib
import importlib.util
import json
import time
from collections import defaultdict
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PARENT = GOAL / "n131_w18_allseed_fourpair_20261012/fourpair_v2.py"
SOURCE = GOAL / "n41_w7_entropy_cubic_20261011/w8/geometry.json"
PUBLIC = GOAL / "n41_common_frob_factor_20261012/audit_result.json"
spec = importlib.util.spec_from_file_location("fourpair_parent", PARENT)
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
from circuit_compare import s3, s4


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(target_reciprocal, variant):
    field, width, _ = parent.field_config("n41")
    columns = parent.support("n41")
    assert len(columns) == 125
    root, nodes = parent.bdd(set(columns), width)
    circuit = parent.KaratsubaCircuit(field.n, [0, 3])
    algebra = parent.Algebra(circuit, field, dense_and_threshold=3000)
    masks, outputs = [], []
    start = time.monotonic()
    for _ in range(3):
        pair_masks = []
        for _ in range(2):
            bits = [circuit.variable() for _ in range(width)]
            masks.append(bits)
            pair_masks.append(bits)
            parent.emit_bdd(circuit, bits, root, nodes)
        out = [circuit.variable() for _ in range(field.n)]
        circuit.clauses.append(" ".join(map(str, out)) + " 0")
        outputs.append(out)
        a, b = [algebra.expression((wire, 1 << (i+1)) for i, wire in enumerate(bits))
                for bits in pair_masks]
        p = algebra.mul(a, b)
        c = algebra.from_bits(out)
        cp = algebra.mul(c, p)
        equation = algebra.add(algebra.square(cp), cp,
                               algebra.square(algebra.add(a, b)), algebra.square(c))
        circuit.require_zero(equation.bits())
    grouped = defaultdict(list)
    for mask, column in columns.items():
        grouped[column].append(mask)
    collision_pairs = [(a, b) for group in grouped.values()
                       for a, b in combinations(sorted(group), 2)]

    def mismatch(bits, code):
        return [-wire if code >> i & 1 else wire for i, wire in enumerate(bits)]

    for i in range(len(masks)):
        for j in range(i+1, len(masks)):
            different = [circuit.xor((x, y)) for x, y in zip(masks[i], masks[j])]
            circuit.clauses.append(" ".join(map(str, different)) + " 0")
            for a, b in collision_pairs:
                for left, right in ((a, b), (b, a)):
                    circuit.clauses.append(" ".join(map(str,
                        mismatch(masks[i], left) + mismatch(masks[j], right))) + " 0")
    source_counts = {"variables": circuit.next_var-1, "and_gates": circuit.and_count,
                     "xor_rows": len(circuit.xors), "clauses": len(circuit.clauses),
                     "build_seconds": time.monotonic()-start}
    target = circuit.constant(target_reciprocal)
    if variant == "two_s3_links":
        middle = [circuit.variable() for _ in range(field.n)]
        circuit.clauses.append(" ".join(map(str, middle)) + " 0")
        s3(circuit, outputs[0], outputs[1], middle)
        s3(circuit, middle, outputs[2], target)
    else:
        s4(circuit, outputs[0], outputs[1], outputs[2], target)
    path = HERE / f"public_{variant}.xcnf"
    circuit.write(path)
    return {"variant": variant, "source_counts": source_counts,
            "total_counts": {"variables": circuit.next_var-1,
                             "and_gates": circuit.and_count,
                             "xor_rows": len(circuit.xors),
                             "clauses": len(circuit.clauses)},
            "formula_bytes": path.stat().st_size, "formula_sha256": sha(path),
            "build_and_write_seconds": time.monotonic()-start,
            "middle_input_bits": field.n if variant == "two_s3_links" else 0,
            "source_masks": len(columns), "bdd_nodes": len(nodes),
            "collision_pairs": len(collision_pairs)}


def main():
    protocol = json.loads((HERE / "source_protocol.json").read_text())
    assert protocol["status"] == "FROZEN"
    assert protocol["sha256"] == {
        "builder": sha(HERE / "source_compare.py"),
        "circuit": sha(HERE / "circuit_compare.py"),
        "parent": sha(PARENT), "source": sha(SOURCE), "public": sha(PUBLIC)}
    field = parent.field_config("n41")[0]
    public = json.loads(PUBLIC.read_text())
    assert public["curve_id"] == "EC1N41Ckb1h7d5e80d3c4d0"
    target = field.inverse(public["public_point"][0])
    assert target == protocol["public_target_reciprocal"]
    rows = [build(target, variant) for variant in ("two_s3_links", "direct_s4")]
    result = {"status": "PAIRED_SOURCE_CONSTRAINED_FORMULAS_BUILT",
              "candidate_id": None, "curve_id": public["curve_id"],
              "public_point": public["public_point"],
              "public_target_reciprocal": target,
              "protocol_sha256": sha(HERE / "source_protocol.json"),
              "rows": rows}
    (HERE / "source_build_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "rows": rows}, sort_keys=True))


if __name__ == "__main__":
    main()
