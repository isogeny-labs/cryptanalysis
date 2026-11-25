"""Exhaustively validate conditional images and freeze two N41 formulas."""

import hashlib
import json
import sys
import time
from pathlib import Path

import circuit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "experiments/koblitz-polynomial-w-pair-20260925"))
from karatsuba_circuit import KaratsubaCircuit  # noqa: E402

import importlib.util  # noqa: E402
HELPER = HERE.parent / "n41_derivative_pair_sat_20261011/prepare.py"
spec = importlib.util.spec_from_file_location("derivative_prepare", HELPER)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_images():
    field = circuit.Field()
    out = {}
    for rotation in (20, 30):
        basis = [field.frob(1 << (j + 1), rotation) for j in range(6)]
        pbasis = [field.frob(1 << (j + 2), rotation) for j in range(11)]
        coordinates = {}
        for mask in range(1 << 11):
            v = 0
            for j in range(11):
                if mask >> j & 1:
                    v ^= pbasis[j]
            coordinates[v] = mask
        assert len(coordinates) == 1 << 11
        checks = circuit.product_checks(field, rotation)
        for seed, rows in checks.items():
            allowed = {p for p in range(1, 1 << 11)
                       if all(not circuit.parity(p & h) for h in rows)}
            s = 0
            for j in range(6):
                if seed >> j & 1:
                    s ^= basis[j]
            source = set()
            for a_mask in range(1, 1 << 6):
                if a_mask == seed:
                    continue
                a = 0
                for j in range(6):
                    if a_mask >> j & 1:
                        a ^= basis[j]
                source.add(coordinates[field.square(a) ^ field.mul(a, s)])
            assert source == allowed and len(source) == 31
        out[str(rotation)] = {"seeds": 63, "image_size_each": 31,
                              "parity_rows_each": 6}
    return out


def main():
    assert not (HERE / "protocol.json").exists()
    images = check_images()
    fixtures = json.loads((HERE.parent / "n41_two_pair_relaxation_20261011/targets.json").read_text())
    panel = json.loads((HERE.parent / "n41_target_derived_join_panel_20261011/panel.json").read_text())
    cases = {"positive": fixtures["known_positive"]["target_z"],
             "control_23": panel["controls"][23]["target_z"]}
    shapes = {}
    for name, target in cases.items():
        start = time.monotonic_ns()
        c = KaratsubaCircuit(41, [0, 3])
        wires = circuit.build(c, circuit.Field(), target)
        if name == "positive":
            field = circuit.Field()
            initial = {}
            masks = fixtures["known_positive"]["source_masks"]
            for i, rotation in enumerate((20, 30)):
                a_mask, b_mask = masks[2*i:2*i+2]
                seed_mask = a_mask ^ b_mask
                a_basis = [field.frob(1 << (j+1), rotation) for j in range(6)]
                p_basis = [field.frob(1 << (j+2), rotation) for j in range(11)]
                a = 0
                s = 0
                for j in range(6):
                    if a_mask >> j & 1:
                        a ^= a_basis[j]
                    if seed_mask >> j & 1:
                        s ^= a_basis[j]
                p = field.square(a) ^ field.mul(a, s)
                products = {}
                for pmask in range(1 << 11):
                    value = 0
                    for j in range(11):
                        if pmask >> j & 1:
                            value ^= p_basis[j]
                    products[value] = pmask
                for bits, value in ((wires["seed"][i], seed_mask),
                                    (wires["product"][i], products[p]),
                                    (wires["pair_z"][i], fixtures["known_positive"]["pair_reciprocals"][i])):
                    for j, wire in enumerate(bits):
                        initial[wire] = value >> j & 1
                for value, wire in wires["selectors"][i].items():
                    initial[wire] = int(value == seed_mask)
            assert len(initial) == len(wires["primary_variables"]) + 126
            old.check(c, old.complete_assignment(c, initial))
        path = HERE / f"{name}.xcnf"
        c.write(path)
        shapes[name] = {"target_z": target, "variables": c.next_var - 1,
                        "and_gates": c.and_count, "clauses": len(c.clauses),
                        "xor_rows": len(c.xors), "bytes": path.stat().st_size,
                        "sha256": sha(path), "build_ns": time.monotonic_ns() - start}
    record = {"status": "FROZEN_CONDITIONAL_IMAGE_EXACT_N41", "candidate_id": None,
              "images": images, "cases": shapes,
              "source_sha256": {"circuit": sha(HERE / "circuit.py"),
                                "prepare": sha(__file__)},
              "solver": "/opt/homebrew/bin/cryptominisat5",
              "solver_sha256": sha("/opt/homebrew/bin/cryptominisat5"),
              "solver_flags": ["--threads=1", "--xor=0", "--printsol=1",
                               "--random=20261011", "--maxtime=30"],
              "parent_cap_seconds": 35, "rss_cap_bytes": 4 * 1024**3}
    (HERE / "protocol.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"images": images, "shapes": shapes}, indent=2))


if __name__ == "__main__":
    main()
