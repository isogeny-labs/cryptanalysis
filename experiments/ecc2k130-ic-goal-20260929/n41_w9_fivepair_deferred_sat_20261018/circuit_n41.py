"""N41 five-pair reciprocal SAT circuit with optional deferred source checks."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'n131_w18_allseed_fourpair_20261012'))
from fourpair_v2 import Algebra, Field, KaratsubaCircuit

N = 41
TAPS = [0, 3]
F = Field(N, TAPS)
WIDTH = 9
SEED_MASK = 56
SEED = SEED_MASK << 1
ROTATIONS = [0, 6, 12, 18, 24]
LINKS = [(0, 1, 5), (5, 2, 6), (3, 4, 7), (6, 7, 8)]
BITS = [bit for bit in range(WIDTH) if bit != SEED_MASK.bit_length() - 1]
BASE = [1 << (bit + 1) for bit in BITS]
PB = [F.square(value) ^ F.mul(SEED, value) for value in BASE]


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
TRACE = [trace(1 << bit) for bit in range(N)]
assert len(BITS) == 8 and len(set(PB)) == 8 and trace(SEED) == 0


def source_valid(mask):
    a = mask << 1
    b = (mask ^ SEED_MASK) << 1
    return bool(a and b and trace(a) == 0 and trace(b) == 0
                and trace(F.inverse(a)) == 0 and trace(F.inverse(b)) == 0)


def build(target_reciprocal, deferred=False):
    assert target_reciprocal
    circ = KaratsubaCircuit(N, TAPS)
    alg = Algebra(circ, F, dense_and_threshold=3000)
    wires = {'mask': [], 'out': [], 'source_inverse': [], 'middle': []}
    nodes = []
    for slot, rotation in enumerate(ROTATIONS):
        masks = [circ.variable() for _ in BITS]
        wires['mask'].append(masks)
        product = alg.expression(zip(masks, PB))
        circ.require_zero([circ.xor(w for w, value in zip(masks, BASE)
                                    if trace(value))])
        if deferred and slot >= 3:
            wires['source_inverse'].append(None)
        else:
            witness = [circ.variable() for _ in range(N)]
            wires['source_inverse'].append(witness)
            tensor = {(i, j): circ.and_(masks[i], witness[j])
                      for i in range(len(BITS)) for j in range(N)}
            product_inverse = alg.expression(
                (w, F.mul(PB[i], 1 << j)) for (i, j), w in tensor.items())
            source_inverse = alg.expression(
                (w, F.mul(BASE[i], 1 << j)) for (i, j), w in tensor.items())
            circ.require_zero(alg.add(product_inverse, alg.one).bits())
            circ.require_zero([circ.xor(w for w, tr in zip(source_inverse.bits(), TRACE) if tr)])
            circ.require_zero([circ.xor(w for j, w in enumerate(witness)
                                        if trace(F.mul(SEED, 1 << j)))])
        out = [circ.variable() for _ in range(N)]
        wires['out'].append(out)
        circ.clauses.append(' '.join(map(str, out)) + ' 0')
        z = alg.from_bits(out)
        cz2 = alg.expression((w, F.mul(C, basis)) for w, basis in alg.square(z).terms)
        circ.require_zero(alg.add(cz2, alg.mul(product, z),
                                  alg.expression(((-1, H),))).bits())
        rotated = circ.linear_element(out, [F.frob(1 << i, rotation)
                                            for i in range(N)])
        nodes.append(alg.from_bits(rotated))
    for _ in range(3):
        middle = [circ.variable() for _ in range(N)]
        wires['middle'].append(middle)
        circ.clauses.append(' '.join(map(str, middle)) + ' 0')
        nodes.append(alg.from_bits(middle))
    nodes.append(alg.expression(((-1, target_reciprocal),)))
    for i, j, k in LINKS:
        a, b, z = nodes[i], nodes[j], nodes[k]
        ab = alg.mul(a, b)
        abz = alg.mul(ab, z)
        circ.require_zero(alg.add(alg.square(abz), abz,
                                  alg.square(alg.add(a, b)), alg.square(z)).bits())
    counts = {'and_gates': circ.and_count, 'variables': circ.next_var - 1,
              'clauses': len(circ.clauses), 'xor_rows': len(circ.xors),
              'sparse_mul_calls': alg.sparse_mul_calls,
              'generic_mul_calls': alg.generic_mul_calls}
    return circ, wires, counts
