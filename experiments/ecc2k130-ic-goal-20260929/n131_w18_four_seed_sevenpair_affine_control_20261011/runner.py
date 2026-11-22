"""Construct a full seven-pair N131 control exercising every affine seed."""

import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CIRCUIT = ROOT / "n131_w18_four_seed_sevenpair_circuit_20261011"
sys.path.insert(0, str(CIRCUIT))
import circuit as method  # noqa: E402

SEEDS = (212, 213, 214, 215, 212, 213, 214)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, data):
    with (HERE / name).open("x") as stream:
        json.dump(data, stream, sort_keys=True, indent=2)
        stream.write("\n")


def construct():
    prior = method.prior
    curve = prior.terminal.independent
    pair = prior.terminal.base.pair
    columns, _, _ = method.support()
    terminal = prior.terminal.pool()["states"][0]
    used = set(terminal["folded_columns"])
    points, selected = [], []
    total = None
    for slot, (seed, rotation) in enumerate(zip(SEEDS, method.ROTATIONS)):
        found = None
        for a in sorted(columns):
            b = a ^ seed
            if a >= b or b not in columns:
                continue
            folded = [columns[a], columns[b]]
            if folded[0] == folded[1] or any(v in used for v in folded):
                continue
            options_a, options_b = curve.point_options(a), curve.point_options(b)
            unrotated = curve.point_add(options_a[0], options_b[0])
            if unrotated is None or unrotated[0] in (0, 1):
                continue
            rotated = (curve.frobenius(unrotated[0], rotation),
                       curve.frobenius(unrotated[1], rotation))
            next_total = curve.point_add(total, rotated)
            if next_total is None or next_total[0] in (0, 1):
                continue
            found = (a, b, folded, unrotated, rotated, next_total)
            break
        assert found is not None, (slot, seed)
        a, b, folded, unrotated, rotated, total = found
        used.update(folded)
        points.append(rotated)
        selected.append({"slot": slot, "seed": seed, "rotation": rotation,
                         "masks": [a, b], "folded_columns": folded,
                         "unrotated_pair_point": list(unrotated),
                         "rotated_pair_point": list(rotated),
                         "partial_sum_point": list(total)})
    assert len(used) == 16
    raw = curve.point_add(total, tuple(terminal["rotated_raw_point"]))
    assert raw is not None
    public = prior.point_mul(4, raw)
    preimages = [curve.point_add(raw, offset) for offset in prior.TORSION]
    assert all(prior.point_mul(4, value) == public for value in preimages)
    residuals = prior.residuals(preimages)
    assert residuals[0]["standard_reciprocal"] == curve.inverse(total[0])
    start = time.monotonic_ns()
    circuit, wires = method.build([row["standard_reciprocal"] for row in residuals])
    built = time.monotonic_ns()
    path = HERE / "control.xcnf"
    circuit.write(path)
    written = time.monotonic_ns()
    initial = {}

    def bind(bits, value):
        initial.update({wire: value >> bit & 1 for bit, wire in enumerate(bits)})

    for slot, row in enumerate(selected):
        a, b = row["masks"]
        bind(wires["selectors"][slot], pair.selector_code(a))
        bind(wires["seeds"][slot], row["seed"] ^ 212)
        bind(wires["outputs"][slot], curve.inverse(row["unrotated_pair_point"][0]))
        for side, mask in enumerate((a, b)):
            witness = curve.inverse(pair.coordinate(mask))
            assert curve.trace(witness) == 0
            bind(wires["inverse_witnesses"][slot][side], witness)
    for bits, row in zip(wires["middle"], selected[1:6]):
        bind(bits, curve.inverse(row["partial_sum_point"][0]))
    for i, wire in enumerate(wires["choices"]):
        initial[wire] = int(i == 0)
    for i, wire in enumerate(wires["branches"]):
        left = curve.inverse(selected[i]["partial_sum_point"][0])
        right = curve.inverse(points[i + 1][0])
        output = curve.inverse(selected[i + 1]["partial_sum_point"][0])
        delta = left ^ right ^ output
        branch = (curve.mul(curve.mul(left, right), output) ^
                  curve.halftrace(curve.square(delta)))
        assert branch in (0, 1)
        initial[wire] = branch
    checked = prior.terminal.base.check_assignment(
        circuit, prior.terminal.base.complete_assignment(circuit, initial))
    save("control_result.json", {
        "status": "PASS_N131_ALL_FOUR_AFFINE_SEEDS_CONSTRUCTED_CONTROL",
        "candidate_id": None,
        "curve_id": "EC1N131Ckb1heb5f1998f20b",
        "seed_sequence": list(SEEDS),
        "selected": selected,
        "terminal_point": terminal["rotated_raw_point"],
        "terminal_folded_columns": terminal["folded_columns"],
        "raw_point": list(raw), "public_point": list(public),
        "selected_choice_index": 0,
        "primary_variables": len(initial),
        "assignment_check": checked,
        "formula": prior.terminal.base.profile(circuit, path,
                                                (built-start)/1e9,
                                                (written-built)/1e9),
        "source_sha256": {"runner": sha(Path(__file__)),
                          "circuit": sha(CIRCUIT / "circuit.py"),
                          "support": sha(method.SUPPORT),
                          "terminal_pool": sha(prior.ROOT / "n131_w18_terminal_fiber_20261011" / "pool.json")},
    })
    print("PASS_N131_ALL_FOUR_AFFINE_SEEDS_CONSTRUCTED_CONTROL", flush=True)


if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] == "control"
    construct()
