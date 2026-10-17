"""N41 W9 five-pair circuit with exact, deferred, or table source gates."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'n131_w18_allseed_fourpair_20261012'))
from fourpair_v2 import Algebra, Field, KaratsubaCircuit

N = 41
TAPS = [0, 3]
WIDTH = 9
SEED_MASK = 56
SEED = SEED_MASK << 1
ROTATIONS = [0, 6, 12, 18, 24]
LINKS = [(0, 1, 5), (5, 2, 6), (3, 4, 7), (6, 7, 8)]
BITS = [bit for bit in range(WIDTH) if bit != SEED_MASK.bit_length() - 1]
BASE = [1 << (bit + 1) for bit in BITS]
F = Field(N, TAPS)


def trace(value):
    result = 0
    for _ in range(N):
        result ^= value
        value = F.square(value)
    assert result in (0, 1)
    return result


def halftrace(value):
    original = value
    result = 0
    for _ in range((N + 1) // 2):
        result ^= value
        value = F.square(F.square(value))
    assert F.square(result) ^ result == original
    return result


H = F.square(halftrace(SEED))
C = 1 ^ H
PB = [F.square(value) ^ F.mul(SEED, value) for value in BASE]
TRACE = [trace(1 << bit) for bit in range(N)]
assert len(BITS) == 8 and trace(SEED) == 0 and H and C
assert all(trace(value) == 0 for value in BASE)
SOURCE = ROOT / 'n41_n131_fivepair_w9_w29_20261017/n41_states.json'
allowed_masks = {row['masks'][0] for row in json.loads(SOURCE.read_text())['states'][0]}
assert len(allowed_masks) == 71
ALLOWED_CODES = {
    sum(((mask >> bit) & 1) << j for j, bit in enumerate(BITS))
    for mask in allowed_masks
}
assert len(ALLOWED_CODES) == 71


def build(target, variant):
    assert variant in ('exact5', 'exact3', 'table5') and target
    circ = KaratsubaCircuit(N, TAPS)
    alg = Algebra(circ, F, dense_and_threshold=3000)
    wires = {'mask': [], 'out': [], 'source_inverse': [], 'middle': []}
    nodes = []
    for slot, rotation in enumerate(ROTATIONS):
        masks = [circ.variable() for _ in BITS]
        wires['mask'].append(masks)
        product = alg.expression(zip(masks, PB))
        exact_gate = variant == 'exact5' or (variant == 'exact3' and slot < 3)
        if exact_gate:
            inverse = [circ.variable() for _ in range(N)]
            wires['source_inverse'].append(inverse)
            tensor = {(i, j): circ.and_(masks[i], inverse[j])
                      for i in range(len(BITS)) for j in range(N)}
            product_inverse = alg.expression(
                (wire, F.mul(PB[i], 1 << j)) for (i, j), wire in tensor.items())
            source_inverse = alg.expression(
                (wire, F.mul(BASE[i], 1 << j)) for (i, j), wire in tensor.items())
            circ.require_zero(alg.add(product_inverse, alg.one).bits())
            circ.require_zero([circ.xor(w for w, tr in zip(source_inverse.bits(), TRACE) if tr)])
            circ.require_zero([circ.xor(w for j, w in enumerate(inverse)
                                        if trace(F.mul(SEED, 1 << j)))])
        else:
            wires['source_inverse'].append(None)
        if variant == 'table5':
            for forbidden in range(1 << len(BITS)):
                if forbidden in ALLOWED_CODES:
                    continue
                circ.clauses.append(' '.join(
                    str(-wire if forbidden >> j & 1 else wire)
                    for j, wire in enumerate(masks)) + ' 0')
        z = [circ.variable() for _ in range(N)]
        wires['out'].append(z)
        circ.clauses.append(' '.join(map(str, z)) + ' 0')
        zz = alg.from_bits(z)
        cz2 = alg.expression((wire, F.mul(C, basis))
                             for wire, basis in alg.square(zz).terms)
        circ.require_zero(alg.add(cz2, alg.mul(product, zz),
                                  alg.expression(((-1, H),))).bits())
        rotated = circ.linear_element(z, [F.frob(1 << i, rotation) for i in range(N)])
        nodes.append(alg.from_bits(rotated))
    for _ in range(3):
        middle = [circ.variable() for _ in range(N)]
        wires['middle'].append(middle)
        circ.clauses.append(' '.join(map(str, middle)) + ' 0')
        nodes.append(alg.from_bits(middle))
    nodes.append(alg.expression(((-1, target),)))
    for i, j, k in LINKS:
        a, b, z = nodes[i], nodes[j], nodes[k]
        ab = alg.mul(a, b)
        abz = alg.mul(ab, z)
        circ.require_zero(alg.add(alg.square(abz), abz,
                                  alg.square(alg.add(a, b)), alg.square(z)).bits())
    return circ, wires, {'and_gates': circ.and_count,
                         'variables': circ.next_var - 1,
                         'clauses': len(circ.clauses),
                         'xor_rows': len(circ.xors),
                         'sparse_mul_calls': alg.sparse_mul_calls,
                         'generic_mul_calls': alg.generic_mul_calls}
