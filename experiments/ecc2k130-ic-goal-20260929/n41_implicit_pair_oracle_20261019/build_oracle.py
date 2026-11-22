"""Build two free W9 source pairs and one exact S3 key constraint."""
import hashlib
import json
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
keys = json.loads((HERE / 'keys.json').read_text())
source = json.loads(Path(protocol['source_states']).read_text())
assert keys['status'] == 'PASS_N41_TWO_PAIR_KEY_CENSUS'
assert source['states_per_slot'] == 284
assert not (HERE / 'build_result.json').exists()
F = design.F


def bind(assignment, wires, value):
    assignment.update({wire: (value >> bit) & 1 for bit, wire in enumerate(wires)})


def s3(a, b, z):
    ab = F.mul(a, b)
    abz = F.mul(ab, z)
    return F.square(abz) ^ abz ^ F.square(a ^ b) ^ F.square(z)


result_rows = []
for row in keys['keys']:
    start = time.monotonic()
    key_id = row['key_id']
    formula = HERE / f'{key_id}.xcnf'
    assert not formula.exists()
    circ = design.KaratsubaCircuit(design.N, design.TAPS)
    alg = design.Algebra(circ, F, dense_and_threshold=3000)
    masks, outputs, source_inverses, nodes = [], [], [], []
    for slot, rotation in enumerate((0, 6)):
        code = [circ.variable() for _ in design.BITS]
        masks.append(code)
        product = alg.expression(zip(code, design.PB))
        inverse = [circ.variable() for _ in range(design.N)]
        source_inverses.append(inverse)
        tensor = {(i, j): circ.and_(code[i], inverse[j])
                  for i in range(len(design.BITS)) for j in range(design.N)}
        product_inverse = alg.expression(
            (wire, F.mul(design.PB[i], 1 << j)) for (i, j), wire in tensor.items())
        source_inverse = alg.expression(
            (wire, F.mul(design.BASE[i], 1 << j)) for (i, j), wire in tensor.items())
        circ.require_zero(alg.add(product_inverse, alg.one).bits())
        circ.require_zero([circ.xor(w for w, tr in zip(source_inverse.bits(), design.TRACE) if tr)])
        circ.require_zero([circ.xor(w for j, w in enumerate(inverse)
                                    if design.trace(F.mul(design.SEED, 1 << j)))])
        z = [circ.variable() for _ in range(design.N)]
        outputs.append(z)
        circ.clauses.append(' '.join(map(str, z)) + ' 0')
        zz = alg.from_bits(z)
        cz2 = alg.expression((wire, F.mul(design.C, basis))
                             for wire, basis in alg.square(zz).terms)
        circ.require_zero(alg.add(cz2, alg.mul(product, zz),
                                  alg.expression(((-1, design.H),))).bits())
        rotated = circ.linear_element(z, [F.frob(1 << i, rotation)
                                         for i in range(design.N)])
        nodes.append(alg.from_bits(rotated))
    target = row['reciprocal_x']
    a, b = nodes
    z = alg.expression(((-1, target),))
    ab = alg.mul(a, b)
    abz = alg.mul(ab, z)
    circ.require_zero(alg.add(alg.square(abz), abz,
                              alg.square(alg.add(a, b)), alg.square(z)).bits())
    circ.write(formula)
    counts = {'variables': circ.next_var - 1, 'clauses': len(circ.clauses),
              'xor_rows': len(circ.xors), 'and_gates': circ.and_count}
    witness_check = None
    if row['exact_member']:
        assignment = {}
        state_ids = row['reference_witness']
        raw_reciprocals = []
        for slot, state_id in enumerate(state_ids):
            state = source['states'][slot][state_id]
            mask = state['masks'][0]
            code = sum(((mask >> bit) & 1) << index
                       for index, bit in enumerate(design.BITS))
            product = 0
            for index, basis in enumerate(design.PB):
                if code >> index & 1:
                    product ^= basis
            raw_x = F.frob(state['point'][0], (design.N - (0, 6)[slot]) % design.N)
            raw_z = F.inverse(raw_x)
            raw_reciprocals.append(raw_z)
            bind(assignment, masks[slot], code)
            bind(assignment, outputs[slot], raw_z)
            bind(assignment, source_inverses[slot], F.inverse(product))
        rotated = [F.frob(value, shift)
                   for value, shift in zip(raw_reciprocals, (0, 6))]
        assert s3(rotated[0], rotated[1], target) == 0
        completed = selector.old.complete_assignment(circ, assignment)
        witness_check = selector.old.check_assignment(circ, completed)
        assert witness_check == {'clauses': counts['clauses'],
                                 'native_xor_rows': counts['xor_rows']}
    result_rows.append({'key_id': key_id, 'exact_member': row['exact_member'],
                        'formula_sha256': sha(formula), 'formula_bytes': formula.stat().st_size,
                        'counts': counts, 'constructed_witness_check': witness_check,
                        'build_wall_seconds': time.monotonic() - start})
result = {'status': 'PASS_N41_TWO_PAIR_ORACLE_BUILD', 'candidate_id': None,
          'curve_id': protocol['curve_id'], 'rows': result_rows,
          'keys_sha256': sha(HERE / 'keys.json'),
          'protocol_sha256': sha(HERE / 'build_protocol.json')}
(HERE / 'build_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({'status': result['status'], 'formulas': len(result_rows),
                  'counts': result_rows[0]['counts']}))
