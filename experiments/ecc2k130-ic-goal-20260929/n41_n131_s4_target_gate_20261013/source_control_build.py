"""Pin a checked three-pair group witness in both exact source formulas."""

import hashlib
import json
import time
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import source_compare as source
from circuit_compare import s3, s4

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(variant, control):
    field, width, _ = source.parent.field_config("n41")
    columns = source.parent.support("n41")
    root, nodes = source.parent.bdd(set(columns), width)
    circuit = source.parent.KaratsubaCircuit(field.n, [0, 3])
    algebra = source.parent.Algebra(circuit, field, dense_and_threshold=3000)
    masks, outputs = [], []
    start = time.monotonic()
    for _ in range(3):
        pair_masks = []
        for _ in range(2):
            bits = [circuit.variable() for _ in range(width)]
            masks.append(bits)
            pair_masks.append(bits)
            source.parent.emit_bdd(circuit, bits, root, nodes)
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
                     "xor_rows": len(circuit.xors), "clauses": len(circuit.clauses)}
    target = circuit.constant(control["target_reciprocal"])
    middle = None
    if variant == "two_s3_links":
        middle = [circuit.variable() for _ in range(field.n)]
        circuit.clauses.append(" ".join(map(str, middle)) + " 0")
        s3(circuit, outputs[0], outputs[1], middle)
        s3(circuit, middle, outputs[2], target)
    else:
        s4(circuit, outputs[0], outputs[1], outputs[2], target)
    unpinned_counts = {"variables": circuit.next_var-1, "and_gates": circuit.and_count,
                       "xor_rows": len(circuit.xors), "clauses": len(circuit.clauses)}

    def pin(bits, value):
        for bit, wire in enumerate(bits):
            circuit.clauses.append(f"{wire if value >> bit & 1 else -wire} 0")

    for bits, value in zip(masks, [x for pair in control["masks"] for x in pair]):
        pin(bits, value)
    for bits, value in zip(outputs, control["pair_reciprocals"]):
        pin(bits, value)
    if middle is not None:
        pin(middle, control["middle_reciprocal"])
    path = HERE / f"control_{variant}.xcnf"
    circuit.write(path)
    return {"variant": variant, "source_counts": source_counts,
            "unpinned_counts": unpinned_counts,
            "pin_clauses": 6*width+3*field.n+(field.n if middle is not None else 0),
            "formula_sha256": sha(path), "formula_bytes": path.stat().st_size,
            "build_and_write_seconds": time.monotonic()-start}


def main():
    protocol = json.loads((HERE / "source_control_build_protocol.json").read_text())
    files = {"builder": HERE / "source_control_build.py",
             "source_builder": HERE / "source_compare.py",
             "control": HERE / "source_control.json",
             "public_build": HERE / "source_build_result.json"}
    assert protocol["status"] == "FROZEN"
    assert protocol["sha256"] == {name: sha(path) for name, path in files.items()}
    control = json.loads(files["control"].read_text())
    public = json.loads(files["public_build"].read_text())
    assert control["status"] == "PASS_THREE_PAIR_GROUP_CONTROL"
    rows = [build(variant, control) for variant in ("two_s3_links", "direct_s4")]
    for row, previous in zip(rows, public["rows"]):
        assert row["source_counts"] == {key: previous["source_counts"][key]
                                         for key in row["source_counts"]}
        # Target constants change the optimized link circuits, while the
        # source prefix must remain byte-for-byte equivalent in counts.
    result = {"status": "PAIRED_PINNED_GROUP_CONTROL_BUILT",
              "protocol_sha256": sha(HERE / "source_control_build_protocol.json"),
              "control_sha256": sha(HERE / "source_control.json"),
              "rows": rows}
    (HERE / "source_control_build_result.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "rows": rows}, sort_keys=True))


if __name__ == "__main__":
    main()
