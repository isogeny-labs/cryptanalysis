"""Five-multiplication XCNF for the free-code N41 bivariate resultant."""
import hashlib
import json
import resource
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'n41_w9_lazy_source_20261017'))
sys.path.insert(0, str(ROOT / 'n131_w20_selector_elimination_v2_20261013'))
import circuit as design
import selector


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


index = int(sys.argv[1])
assert index in (0, 1)
cfg = json.loads((HERE / 'circuit_protocol.json').read_text())
for name, digest in cfg['sources'].items():
    assert sha(name) == digest, name
out = HERE / ('positive.xcnf' if index == 0 else 'ordinary.xcnf')
assert not out.exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('resultant circuit cap')))
signal.alarm(cfg['wall_cap_seconds'])
started = time.monotonic()
lines = (HERE / 'resultant_input.tsv').read_text().splitlines()
assert lines[0] == 'FREECODE 25 281 13'
source_rows = [line.split() for line in lines if line.startswith('P ')]
target_rows = [line.split() for line in lines if line.startswith('T ')]
coefficient_rows = [line.split() for line in lines if line.startswith(f'C {index} ')]
assert len(source_rows) == 281 and len(target_rows) == 25 and len(coefficient_rows) == 13
coeff = {(int(row[2]), int(row[3])): int(row[4]) for row in coefficient_rows}
assert len(coeff) == 13
valid = {int(row[1]) for row in source_rows}
assert len(valid) == 281
fixture = json.loads((ROOT / 'n41_w11_exact_two_pair_oracle_20261018/fixture.json').read_text())
F = design.F
bits = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10]
base = [1 << (bit+1) for bit in bits]
pb = [F.square(a) ^ F.mul(112, a) for a in base]
rotations = [12, 24]
rotated_pb = [[F.frob(v, rotation) for v in pb] for rotation in rotations]
for row in source_rows:
    code = int(row[1])
    for slot in range(2):
        value = 0
        for j in range(10):
            if code >> j & 1:
                value ^= rotated_pb[slot][j]
        assert value == int(row[2+slot])

circ = design.KaratsubaCircuit(41, [0, 3])
alg = design.Algebra(circ, F, dense_and_threshold=3000)
masks = [[circ.variable() for _ in range(10)] for _ in range(2)]
for row in masks:
    for invalid in range(1024):
        if invalid not in valid:
            circ.clauses.append(' '.join(str(-wire if invalid >> j & 1 else wire)
                                         for j, wire in enumerate(row)) + ' 0')
different = [circ.xor((a, b)) for a, b in zip(*masks)]
circ.clauses.append(' '.join(map(str, different))+' 0')
for left, right in fixture['distinct_code_folded_column_collision_pairs']:
    for a, b in ((left, right), (right, left)):
        literals = [(-wire if a >> j & 1 else wire) for j, wire in enumerate(masks[0])]
        literals += [(-wire if b >> j & 1 else wire) for j, wire in enumerate(masks[1])]
        circ.clauses.append(' '.join(map(str, literals))+' 0')
p, q = [alg.expression(zip(row, basis)) for row, basis in zip(masks, rotated_pb)]
p2, q2 = alg.square(p), alg.square(q)
p4, q4 = alg.square(p2), alg.square(q2)


def scale(expr, value):
    return alg.expression((wire, F.mul(basis, value)) for wire, basis in expr.terms)


def constant(value):
    return alg.expression(((-1, value),))


def qlinear(values):
    return alg.add(constant(values[0]), scale(q2, values[1]), scale(q4, values[2]))


row0 = qlinear([coeff[(0, j)] for j in (0, 2, 4)])
row2 = qlinear([coeff[(2, j)] for j in (0, 2, 4)])
row4 = qlinear([coeff[(4, j)] for j in (0, 2, 4)])
even_part = alg.add(row0, alg.mul(p2, row2), alg.mul(p4, row4))
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
    for slot, code in enumerate((253, 63)):
        for j, wire in enumerate(masks[slot]):
            assignment[wire] = (code >> j) & 1
    full = selector.old.complete_assignment(circ, assignment)
    check = selector.old.check_assignment(circ, full)
    assert check == {'clauses': counts['clauses'],
                     'native_xor_rows': counts['xor_rows']}
circ.write(out)
signal.alarm(0)
result = {'status': 'PASS_N41_W11_FREECODE_RESULTANT_CIRCUIT',
          'candidate_id': None, 'curve_id': cfg['curve_id'],
          'target_index': index, 'target_point': list(map(int, target_rows[index][2:4])),
          'counts': counts, 'positive_assignment_check': check,
          'formula_bytes': out.stat().st_size, 'formula_sha256': sha(out),
          'wall_seconds': time.monotonic()-started,
          'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'protocol_sha256': sha(HERE / 'circuit_protocol.json')}
(HERE / f'circuit_{index}_result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps({'target_index': index, 'counts': counts,
                  'wall_seconds': result['wall_seconds']}, sort_keys=True))
