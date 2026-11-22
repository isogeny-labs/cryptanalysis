"""Exact seed-conditioned linear product image in the N41 two-pair circuit."""

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "n41_derivative_pair_sat_20261011/circuit.py"
spec = importlib.util.spec_from_file_location("derivative_pair", SOURCE)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
Field, Algebra = old.Field, old.Algebra


def parity(x):
    return bin(x).count("1") & 1


def product_checks(field, rotation):
    a_basis = [field.frob(1 << (j + 1), rotation) for j in range(6)]
    p_basis = [field.frob(1 << (j + 2), rotation) for j in range(11)]
    coordinates = {}
    for mask in range(1 << 11):
        value = 0
        for j in range(11):
            if mask >> j & 1:
                value ^= p_basis[j]
        assert value not in coordinates
        coordinates[value] = mask
    checks = {}
    for seed in range(1, 1 << 6):
        s = 0
        for j in range(6):
            if seed >> j & 1:
                s ^= a_basis[j]
        images = [coordinates[field.square(a) ^ field.mul(a, s)] for a in a_basis]
        rows = {}
        for h in range(1, 1 << 11):
            if any(parity(h & v) for v in images):
                continue
            v = h
            while v:
                lead = v.bit_length() - 1
                if lead in rows:
                    v ^= rows[lead]
                else:
                    rows[lead] = v
                    break
            if len(rows) == 6:
                break
        assert len(rows) == 6
        checks[seed] = list(rows.values())
    return checks


def selector(circuit, bits, value):
    out = circuit.variable()
    lits = [wire if (value >> i) & 1 else -wire for i, wire in enumerate(bits)]
    for lit in lits:
        circuit.clauses.append(f"-{out} {lit} 0")
    circuit.clauses.append(" ".join([str(out), *[str(-lit) for lit in lits], "0"]))
    return out


def build(circuit, field, target_z):
    assert circuit.n == 41 and 0 < target_z < 1 << 41
    algebra = Algebra(circuit, field)
    seed = [[circuit.variable() for _ in range(6)] for _ in range(2)]
    product = [[circuit.variable() for _ in range(11)] for _ in range(2)]
    pair_z = [[circuit.variable() for _ in range(41)] for _ in range(2)]
    primary = [*sum(seed, []), *sum(product, []), *sum(pair_z, [])]
    selectors = []
    for i, rotation in enumerate((20, 30)):
        circuit.clauses.append(" ".join(map(str, seed[i])) + " 0")
        circuit.clauses.append(" ".join(map(str, pair_z[i])) + " 0")
        side_selectors = {}
        for value, rows in product_checks(field, rotation).items():
            guard = selector(circuit, seed[i], value)
            side_selectors[value] = guard
            for row in rows:
                check = circuit.xor(product[i][j] for j in range(11) if row >> j & 1)
                circuit.clauses.append(f"-{guard} -{check} 0")
        selectors.append(side_selectors)
        s = algebra.expression((wire, field.frob(1 << (j + 1), rotation))
                               for j, wire in enumerate(seed[i]))
        p = algebra.expression((wire, field.frob(1 << (j + 2), rotation))
                               for j, wire in enumerate(product[i]))
        z = algebra.from_bits(pair_z[i])
        v = algebra.mul(p, z)
        total = algebra.add(s, z)
        circuit.require_zero(algebra.add(algebra.square(v), v,
                                         algebra.square(total)).bits())
    left, right = (algebra.from_bits(bits) for bits in pair_z)
    target = algebra.from_bits(circuit.constant(target_z))
    triple = algebra.mul(algebra.mul(left, right), target)
    total = algebra.add(left, right, target)
    circuit.require_zero(algebra.add(algebra.square(triple), triple,
                                     algebra.square(total)).bits())
    return {"seed": seed, "product": product, "pair_z": pair_z,
            "selectors": selectors,
            "primary_variables": primary}
