"""Build the N131 target resultant on source codes, delaying source validity."""
import hashlib
import json
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
cfg = json.loads((HERE / 'protocol.json').read_text())
for path, expected in cfg['sources'].items():
    assert sha(path) == expected, path
assert cfg['curve_id'] == 'EC1N131Ckb1heb5f1998f20b'
old = ROOT / 'n131_w33_freecode_resultant_20261018'
data = json.loads((old / 'coefficients.json').read_text())
assert data['status'] == 'PASS_N131_W33_FREECODE_RESULTANT_EXPORT'
row = data['rows'][index]
coeff = {(i, j): a for i, j, a in row['terms']}
assert len(coeff) == 13
assert data['rotations'] == [0, 18]
F = design.F
assert F.n == 131 and design.SEED == 898618 << 1
seed_mask = 898618
bits = [bit for bit in range(33) if bit != seed_mask.bit_length()-1]
base = [1 << (bit+1) for bit in bits]
pb = [F.square(a) ^ F.mul(design.SEED, a) for a in base]
rotated_pb = [[F.frob(value, rotation) for value in pb] for rotation in (0, 18)]
assert len(bits) == 32

started = time.monotonic()
circ = design.KaratsubaCircuit(131, [0, 1, 2, 13])
alg = design.Algebra(circ, F, dense_and_threshold=3000)
masks = [[circ.variable() for _ in range(32)] for _ in range(2)]
products = [alg.expression(zip(mask, basis))
            for mask, basis in zip(masks, rotated_pb)]
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
check = None
if index == 0:
    assignment = {}
    for slot, source in enumerate(data['positive_source_checks']):
        for j, wire in enumerate(masks[slot]):
            assignment[wire] = (source['code'] >> j) & 1
    full = selector.old.complete_assignment(circ, assignment)
    check = selector.old.check_assignment(circ, full)
    assert check == {'clauses': counts['clauses'],
                     'native_xor_rows': counts['xor_rows']}
out = HERE / ('positive_core.xcnf' if index == 0 else 'public_core.xcnf')
assert not out.exists()
circ.write(out)
result = {'status': 'PASS_N131_W33_RESULTANT_CORE', 'candidate_id': None,
          'curve_id': cfg['curve_id'], 'target_index': index,
          'target_name': row['name'], 'target_point': row['point'],
          'counts': counts, 'positive_assignment_check': check,
          'formula_sha256': sha(out), 'formula_bytes': out.stat().st_size,
          'wall_seconds': time.monotonic()-started,
          'protocol_sha256': sha(HERE / 'protocol.json')}
(HERE / f'build_{index}_result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps(result, sort_keys=True))
