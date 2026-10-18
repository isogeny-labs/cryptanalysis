"""W33 five-pair circuit; independently audit source validity in slots 3/4."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'n131_w23_sixpair_shared_circuit_20261017'))
import circuit as previous

N = previous.N
TAPS = previous.TAPS
F = previous.F
SEED_MASK = previous.SEED_MASK
SEED = previous.SEED
H = previous.H
C = previous.C
WIDTH = 33
BITS = [bit for bit in range(WIDTH) if bit != SEED_MASK.bit_length() - 1]
BASE = [1 << (bit + 1) for bit in BITS]
PB = [F.square(value) ^ F.mul(SEED, value) for value in BASE]
TRACE = previous.TRACE
ROTATIONS = [0, 18, 36, 54, 72]
LINKS = [(0, 1, 5), (5, 2, 6), (3, 4, 7), (6, 7, 8)]
DEFERRED_SLOTS = (3, 4)
assert len(BITS) == 32 and len(set(PB)) == 32


def build(target):
    assert target
    circ = previous.KaratsubaCircuit(N, TAPS)
    alg = previous.Algebra(circ, F, dense_and_threshold=3000)
    wires = {'mask': [], 'out': [], 'source_inverse': [], 'middle': []}
    nodes = []
    for slot, rotation in enumerate(ROTATIONS):
        masks = [circ.variable() for _ in BITS]
        wires['mask'].append(masks)
        product = alg.expression(zip(masks, PB))
        circ.require_zero([circ.xor(w for w, value in zip(masks, BASE)
                                    if previous.trace(value))])
        if slot in DEFERRED_SLOTS:
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
                                        if previous.trace(F.mul(SEED, 1 << j)))])
        out = [circ.variable() for _ in range(N)]
        wires['out'].append(out)
        circ.clauses.append(' '.join(map(str, out)) + ' 0')
        z = alg.from_bits(out)
        cz2 = alg.expression((w, F.mul(C, basis)) for w, basis in alg.square(z).terms)
        circ.require_zero(alg.add(cz2, alg.mul(product, z),
                                  alg.expression(((-1, H),))).bits())
        rotated = circ.linear_element(out, [F.frob(1 << i, rotation) for i in range(N)])
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
    counts = {'and_gates': circ.and_count, 'variables': circ.next_var - 1,
              'clauses': len(circ.clauses), 'xor_rows': len(circ.xors),
              'sparse_mul_calls': alg.sparse_mul_calls,
              'generic_mul_calls': alg.generic_mul_calls}
    return circ, wires, counts
