"""Exact N131 W33 source validity plus five-mul two-pair resultant."""
import hashlib
import json
import resource
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'n131_w23_sixpair_shared_circuit_20261017'))
sys.path.insert(0, str(ROOT / 'n131_w20_selector_elimination_v2_20261013'))
import circuit as design
import selector


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


index = int(sys.argv[1])
assert index in (0, 1)
cfg = json.loads((HERE / 'build_protocol.json').read_text())
for path, digest in cfg['sources'].items():
    assert sha(path) == digest, path
out = HERE / ('positive.xcnf' if index == 0 else 'public.xcnf')
assert not out.exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('N131 free-code build cap')))
signal.alarm(cfg['wall_cap_seconds'])
started = time.monotonic()
source = json.loads((HERE / 'coefficients.json').read_text())
assert source['status'] == 'PASS_N131_W33_FREECODE_RESULTANT_EXPORT'
assert source['free_code_bits'] == 32 and source['source_product_rank'] == 32
assert source['rotations'] == [0, 18]
row = source['rows'][index]
coeff = {(i, j): value for i, j, value in row['terms']}
assert len(coeff) == 13
F = design.F
assert F.n == 131 and design.SEED == (898618 << 1)
seed_mask = 898618
bits = [bit for bit in range(33) if bit != seed_mask.bit_length()-1]
base = [1 << (bit+1) for bit in bits]
pb = [F.square(a) ^ F.mul(design.SEED, a) for a in base]
rotations = [0, 18]
rotated_pb = [[F.frob(value, rotation) for value in pb]
              for rotation in rotations]
assert len(bits) == 32
if index == 0:
    for slot, check in enumerate(source['positive_source_checks']):
        code = check['code']
        value = 0
        for j, basis in enumerate(pb):
            if code >> j & 1:
                value ^= basis
        assert value == check['unrotated_product']

circ = design.KaratsubaCircuit(131, [0, 1, 2, 13])
alg = design.Algebra(circ, F, dense_and_threshold=3000)
masks = []
inverse_witnesses = []
products = []
for rotation in rotations:
    mask = [circ.variable() for _ in range(32)]
    masks.append(mask)
    circ.require_zero([circ.xor(wire for wire, basis in zip(mask, base)
                                if design.trace(basis))])
    witness = [circ.variable() for _ in range(131)]
    inverse_witnesses.append(witness)
    tensor = {(i, j): circ.and_(mask[i], witness[j])
              for i in range(32) for j in range(131)}
    product_inverse = alg.expression(
        (wire, F.mul(pb[i], 1 << j)) for (i, j), wire in tensor.items())
    source_inverse = alg.expression(
        (wire, F.mul(base[i], 1 << j)) for (i, j), wire in tensor.items())
    circ.require_zero(alg.add(product_inverse, alg.one).bits())
    circ.require_zero([circ.xor(wire for wire, tr in
                                zip(source_inverse.bits(), design.TRACE) if tr)])
    circ.require_zero([circ.xor(wire for j, wire in enumerate(witness)
                                if design.trace(F.mul(design.SEED, 1 << j)))])
    products.append(alg.expression(zip(mask, rotated_pb[rotations.index(rotation)])))
different = [circ.xor((a, b)) for a, b in zip(*masks)]
circ.clauses.append(' '.join(map(str, different))+' 0')
p, q = products
p2, q2 = alg.square(p), alg.square(q)
p4, q4 = alg.square(p2), alg.square(q2)


def scale(expr, value):
    return alg.expression((wire, F.mul(basis, value)) for wire, basis in expr.terms)


def constant(value):
    return alg.expression(((-1, value),))


def qlinear(values):
    return alg.add(constant(values[0]), scale(q2, values[1]), scale(q4, values[2]))


even0 = qlinear([coeff[(0, j)] for j in (0, 2, 4)])
even2 = qlinear([coeff[(2, j)] for j in (0, 2, 4)])
even4 = qlinear([coeff[(4, j)] for j in (0, 2, 4)])
even_part = alg.add(even0, alg.mul(p2, even2), alg.mul(p4, even4))
odd0 = alg.add(constant(coeff[(1, 1)]), scale(q2, coeff[(1, 3)]))
odd2 = alg.add(constant(coeff[(3, 1)]), scale(q2, coeff[(3, 3)]))
odd_part = alg.add(odd0, alg.mul(p2, odd2))
res = alg.add(even_part, alg.mul(alg.mul(p, q), odd_part))
circ.require_zero(res.bits())
counts = {'and_gates': circ.and_count, 'variables': circ.next_var-1,
          'clauses': len(circ.clauses), 'xor_rows': len(circ.xors),
          'sparse_mul_calls': alg.sparse_mul_calls,
          'generic_mul_calls': alg.generic_mul_calls,
          'sparse_pair_products': alg.sparse_pair_products,
          'linear_squares': alg.linear_squares}
assert alg.sparse_mul_calls+alg.generic_mul_calls == 5
positive_check = None
if index == 0:
    assignment = {}
    for slot, check in enumerate(source['positive_source_checks']):
        for j, wire in enumerate(masks[slot]):
            assignment[wire] = (check['code'] >> j) & 1
        for j, wire in enumerate(inverse_witnesses[slot]):
            assignment[wire] = (check['inverse_product'] >> j) & 1
    full = selector.old.complete_assignment(circ, assignment)
    positive_check = selector.old.check_assignment(circ, full)
    assert positive_check == {'clauses': counts['clauses'],
                              'native_xor_rows': counts['xor_rows']}
circ.write(out)
signal.alarm(0)
result = {'status': 'PASS_N131_W33_FREECODE_RESULTANT_CIRCUIT',
          'candidate_id': None, 'curve_id': cfg['curve_id'],
          'target_index': index, 'target_name': row['name'],
          'target_point': row['point'],
          'rotations': rotations, 'source_bits': bits,
          'counts': counts, 'positive_assignment_check': positive_check,
          'formula_bytes': out.stat().st_size, 'formula_sha256': sha(out),
          'wall_seconds': time.monotonic()-started,
          'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'protocol_sha256': sha(HERE / 'build_protocol.json')}
(HERE / f'build_{index}_result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps({'target_index': index, 'counts': counts,
                  'wall_seconds': result['wall_seconds'],
                  'formula_bytes': result['formula_bytes']}, sort_keys=True))
