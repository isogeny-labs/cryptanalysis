"""Seven W18 pairs plus explicit first/terminal pair outputs for a public point."""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / "n131_fixed_seed_ninepair_cubic_20261011"
sys.path.insert(0, str(BASE))
import run as base  # noqa: E402

PAIR = base.pair
N = PAIR.N
FREE_ROTATIONS = base.ROTATIONS[1:8]
TERMINAL_ROTATION = 128


def constants():
    states = json.loads((ROOT / "n131_w18_terminal_fiber_20261011/pool.json").read_text())["states"]
    codes = list(dict.fromkeys(row["code"] for row in states))
    assert len(codes) == 8
    h2 = PAIR.gf_square(PAIR.gf_half_trace(PAIR.coordinate(PAIR.SEED)))
    terminal_h2 = PAIR.gf_frobenius(h2, TERMINAL_ROTATION)
    k, ell = 1 ^ h2, 1 ^ terminal_h2
    assert k and ell
    return codes, h2, terminal_h2, k, ell


def build(target_a, bdd_root, bdd_nodes):
    circuit = base.KaratsubaCircuit(N, [0, 1, 2, 13])
    algebra = base.Algebra(circuit, base.Field(), dense_and_threshold=3000)
    codes, h2, terminal_h2, k, ell = constants()

    def const(value):
        return algebra.expression(((-1, value),))

    def add(*items):
        return algebra.add(*items)

    def mul(left, right):
        return algebra.mul(left, right)

    first_code = [circuit.variable() for _ in range(17)]
    first_product = algebra.expression(zip(first_code, PAIR.product_basis()))
    first_bits = [circuit.variable() for _ in range(N)]
    first = algebra.from_bits(first_bits)
    first_square = algebra.expression(
        (wire, PAIR.gf_mul(k, PAIR.gf_square(1 << bit)))
        for bit, wire in enumerate(first_bits))
    circuit.require_zero(add(mul(first, first_product), first_square,
                             const(h2)).bits())
    circuit.clauses.append(" ".join(map(str, first_bits)) + " 0")
    selectors, pair_outputs, rotated = [], [], []
    for rotation in FREE_ROTATIONS:
        selector = [circuit.variable() for _ in range(17)]
        output = [circuit.variable() for _ in range(N)]
        selectors.append(selector)
        pair_outputs.append(output)
        product = algebra.expression(zip(selector, PAIR.product_basis()))
        square_term = algebra.expression(
            (wire, PAIR.gf_mul(k, PAIR.gf_square(1 << bit)))
            for bit, wire in enumerate(output))
        circuit.require_zero(add(mul(algebra.from_bits(output), product),
                                 square_term, const(h2)).bits())
        circuit.clauses.append(" ".join(map(str, output)) + " 0")
        images = [PAIR.gf_frobenius(1 << bit, rotation) for bit in range(N)]
        rotated.append(algebra.from_bits(circuit.linear_element(output, images)))

    choices = [circuit.variable() for _ in codes]
    circuit.clauses.append(" ".join(map(str, choices)) + " 0")
    for index, left in enumerate(choices):
        for right in choices[index+1:]:
            circuit.clauses.append(f"-{left} -{right} 0")
    q = algebra.expression((wire, PAIR.gf_frobenius(PAIR.product_from_code(code),
                                                    TERMINAL_ROTATION))
                           for wire, code in zip(choices, codes))
    terminal_bits = [circuit.variable() for _ in range(N)]
    terminal = algebra.from_bits(terminal_bits)
    terminal_square = algebra.expression(
        (wire, PAIR.gf_mul(ell, PAIR.gf_square(1 << bit)))
        for bit, wire in enumerate(terminal_bits))
    circuit.require_zero(add(mul(terminal, q), terminal_square,
                             const(terminal_h2)).bits())
    circuit.clauses.append(" ".join(map(str, terminal_bits)) + " 0")

    middle = [[circuit.variable() for _ in range(N)] for _ in range(6)]
    block_bits = [circuit.variable() for _ in range(N)]
    block = algebra.from_bits(block_bits)
    branches = [circuit.variable() for _ in range(8)]
    ht_basis, trace_basis = [], []
    for bit in range(N):
        value, image = PAIR.gf_square(1 << bit), 0
        for _ in range((N+1)//2):
            image ^= value
            value = PAIR.gf_square(PAIR.gf_square(value))
        ht_basis.append(image)
        trace_basis.append(base.trace(1 << bit))
    running = rotated[0]
    for index in range(1, 7):
        output = algebra.from_bits(middle[index-1])
        total = add(running, rotated[index], output)
        ht = circuit.linear_element(total.bits(), ht_basis)
        circuit.require_zero(add(mul(mul(running, rotated[index]), output),
                                 algebra.from_bits(ht),
                                 algebra.expression(((branches[index-1], 1),))).bits())
        circuit.require_zero([circuit.xor(
            wire for wire, bit in zip(total.bits(), trace_basis) if bit)])
        circuit.clauses.append(" ".join(map(str, middle[index-1])) + " 0")
        running = output
    target = const(target_a)
    total = add(running, block, target)
    ht = circuit.linear_element(total.bits(), ht_basis)
    circuit.require_zero(add(mul(mul(running, block), target),
                             algebra.from_bits(ht),
                             algebra.expression(((branches[-1], 1),))).bits())
    circuit.require_zero([circuit.xor(
        wire for wire, bit in zip(total.bits(), trace_basis) if bit)])
    circuit.clauses.append(" ".join(map(str, block_bits)) + " 0")
    block_total = add(first, terminal, block)
    block_ht = circuit.linear_element(block_total.bits(), ht_basis)
    circuit.require_zero(add(mul(mul(first, terminal), block),
                             algebra.from_bits(block_ht),
                             algebra.expression(((branches[-1], 1),))).bits())
    circuit.require_zero([circuit.xor(
        wire for wire, bit in zip(block_total.bits(), trace_basis) if bit)])

    for selector in [first_code, *selectors]:
        literals = {0: 0, 1: -1}
        for node in sorted(bdd_nodes):
            bit, low, high = bdd_nodes[node]
            left, right = literals[low], literals[high]
            literals[node] = circuit.xor((
                left, circuit.and_(selector[bit], circuit.xor((left, right)))))
        circuit.clauses.append(str(literals[bdd_root]) + " 0")
    return circuit, {"first_code": first_code, "first_output": first_bits,
                     "terminal_output": terminal_bits, "selectors": selectors,
                     "pair_outputs": pair_outputs, "choices": choices,
                     "middle": middle, "block": block_bits, "branches": branches,
                     "terminal_codes": codes}
