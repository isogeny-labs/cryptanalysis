"""Exact free-code two-pair XCNF for one N41 target residual."""
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


protocol = json.loads((HERE / 'build_protocol.json').read_text())
for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
assert not (HERE / 'formula.xcnf').exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('two-pair build cap')))
signal.alarm(protocol['wall_cap_seconds'])
started = time.monotonic()
fixture = json.loads((HERE / 'fixture.json').read_text())
design.WIDTH = 11
design.BITS = [bit for bit in range(11) if bit != 5]
design.BASE = [1 << (bit + 1) for bit in design.BITS]
design.PB = [design.F.square(word) ^ design.F.mul(design.SEED, word)
             for word in design.BASE]
assert len(design.BITS) == 10 and fixture['positive_pair_rows'][0]['rotation'] == 12
assert fixture['positive_pair_rows'][1]['rotation'] == 24
F = design.F
circ = design.KaratsubaCircuit(design.N, design.TAPS)
alg = design.Algebra(circ, F, dense_and_threshold=3000)
wires = {'mask': [], 'out': [], 'source_inverse': [], 'rotations': [12, 24]}
nodes = []
for rotation in wires['rotations']:
    masks = [circ.variable() for _ in design.BITS]
    wires['mask'].append(masks)
    product = alg.expression(zip(masks, design.PB))
    inverse = [circ.variable() for _ in range(design.N)]
    wires['source_inverse'].append(inverse)
    tensor = {(i, j): circ.and_(masks[i], inverse[j])
              for i in range(len(design.BITS)) for j in range(design.N)}
    product_inverse = alg.expression(
        (wire, F.mul(design.PB[i], 1 << j)) for (i, j), wire in tensor.items())
    source_inverse = alg.expression(
        (wire, F.mul(design.BASE[i], 1 << j)) for (i, j), wire in tensor.items())
    circ.require_zero(alg.add(product_inverse, alg.one).bits())
    circ.require_zero([circ.xor(w for w, tr in
                                zip(source_inverse.bits(), design.TRACE) if tr)])
    circ.require_zero([circ.xor(w for j, w in enumerate(inverse)
                                if design.trace(F.mul(design.SEED, 1 << j)))])
    circ.require_zero([circ.xor(w for w, value in zip(masks, design.BASE)
                                if design.trace(value))])
    out = [circ.variable() for _ in range(design.N)]
    wires['out'].append(out)
    circ.clauses.append(' '.join(map(str, out)) + ' 0')
    zz = alg.from_bits(out)
    cz2 = alg.expression((wire, F.mul(design.C, basis))
                         for wire, basis in alg.square(zz).terms)
    circ.require_zero(alg.add(cz2, alg.mul(product, zz),
                              alg.expression(((-1, design.H),))).bits())
    rotated = circ.linear_element(out,
                                  [F.frob(1 << i, rotation) for i in range(design.N)])
    nodes.append(alg.from_bits(rotated))

different = [circ.xor((a, b)) for a, b in zip(*wires['mask'])]
circ.clauses.append(' '.join(map(str, different)) + ' 0')
for left, right in fixture['distinct_code_folded_column_collision_pairs']:
    for a, b in ((left, right), (right, left)):
        literals = [(-wire if a >> j & 1 else wire)
                    for j, wire in enumerate(wires['mask'][0])]
        literals += [(-wire if b >> j & 1 else wire)
                     for j, wire in enumerate(wires['mask'][1])]
        circ.clauses.append(' '.join(map(str, literals)) + ' 0')
target = alg.expression(((-1, fixture['target_residual_reciprocal']),))
ab = alg.mul(nodes[0], nodes[1])
abz = alg.mul(ab, target)
circ.require_zero(alg.add(alg.square(abz), abz,
                          alg.square(alg.add(nodes[0], nodes[1])),
                          alg.square(target)).bits())

counts = {'and_gates': circ.and_count, 'variables': circ.next_var - 1,
          'clauses': len(circ.clauses), 'xor_rows': len(circ.xors),
          'sparse_mul_calls': alg.sparse_mul_calls,
          'generic_mul_calls': alg.generic_mul_calls}
assignment = {}
for slot, row in enumerate(fixture['positive_pair_rows']):
    for index, wire in enumerate(wires['mask'][slot]):
        assignment[wire] = row['code'] >> index & 1
    for index, wire in enumerate(wires['source_inverse'][slot]):
        assignment[wire] = row['source_inverse_product'] >> index & 1
    for index, wire in enumerate(wires['out'][slot]):
        assignment[wire] = row['out_unrotated_reciprocal'] >> index & 1
full = selector.old.complete_assignment(circ, assignment)
check = selector.old.check_assignment(circ, full)
assert check == {'clauses': counts['clauses'],
                 'native_xor_rows': counts['xor_rows']}
path = HERE / 'formula.xcnf'
circ.write(path)
(HERE / 'input_wires.json').write_text(json.dumps(wires, sort_keys=True, indent=2) + '\n')
signal.alarm(0)
result = {'status': 'PASS_N41_W11_EXACT_TWO_PAIR_POSITIVE_CIRCUIT',
          'candidate_id': None, 'curve_id': protocol['curve_id'],
          'target_residual_point': fixture['target_residual_point'],
          'target_residual_reciprocal': fixture['target_residual_reciprocal'],
          'constructed_assignment_check': check,
          'counts': counts, 'formula_bytes': path.stat().st_size,
          'formula_sha256': sha(path), 'input_wires_sha256': sha(HERE / 'input_wires.json'),
          'wall_seconds': time.monotonic() - started,
          'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'protocol_sha256': sha(HERE / 'build_protocol.json')}
(HERE / 'build_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: result[key] for key in
                  ('status', 'counts', 'wall_seconds')}, sort_keys=True))
