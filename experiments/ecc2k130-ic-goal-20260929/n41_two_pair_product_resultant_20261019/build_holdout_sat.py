"""Compile the eliminated two-pair resultant over 16 binary source-code bits."""
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path('/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929')
sys.path.insert(0, str(ROOT / 'n41_w9_lazy_source_20261017'))
sys.path.insert(0, str(ROOT / 'n131_w20_selector_elimination_v2_20261013'))
import circuit as design
import selector


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / 'holdout_build_protocol.json').read_text())
for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
assert not (HERE / 'holdout_build_result.json').exists()
resultant = json.loads((HERE / 'resultant.json').read_text())
keys = json.loads(Path(protocol['keys']).read_text())
source = json.loads(Path(protocol['source_states']).read_text())
F = design.F
columns = []
for slot in (0, 1):
    lookup = {}
    for row in source['states'][slot]:
        mask = row['masks'][0]
        code = sum(((mask >> bit) & 1) << index
                   for index, bit in enumerate(design.BITS))
        assert lookup.setdefault(code, set(row['columns'])) == set(row['columns'])
    assert len(lookup) == 71
    columns.append(lookup)


def scaled(alg, node, coefficient):
    return alg.expression((wire, F.mul(basis, coefficient))
                          for wire, basis in node.terms)


def forbid_code(circ, wires, code):
    return ' '.join(str(-wire if code >> bit & 1 else wire)
                    for bit, wire in enumerate(wires))


rows = []
for key_id in protocol['key_ids']:
    started = time.monotonic()
    key = next(row for row in keys['keys'] if row['key_id'] == key_id)
    target = key.get('reciprocal_x', F.inverse(key['point'][0]))
    powers = [1]
    for _ in range(8):
        powers.append(F.mul(powers[-1], target))
    coefficient = [[0 for _ in range(5)] for _ in range(5)]
    for term in resultant['terms']:
        i, j, k = term['exponents']
        coefficient[i][j] ^= F.mul(term['coefficient'], powers[k])
    circ = design.KaratsubaCircuit(design.N, design.TAPS)
    alg = design.Algebra(circ, F, dense_and_threshold=3000)
    a_bits = [circ.variable() for _ in design.BITS]
    b_bits = [circ.variable() for _ in design.BITS]
    p = alg.expression(zip(a_bits, design.PB))
    q = alg.expression((wire, F.frob(basis, 6))
                       for wire, basis in zip(b_bits, design.PB))
    p2, q2 = alg.square(p), alg.square(q)
    p_pow = [alg.one, p, p2, alg.mul(p, p2), alg.square(p2)]
    q_pow = [alg.one, q, q2, alg.mul(q, q2), alg.square(q2)]
    expression = alg.expression(())
    field_products = 0
    for i in range(5):
        for j in range(5):
            if not coefficient[i][j]:
                continue
            if i == 0:
                node = q_pow[j]
            elif j == 0:
                node = p_pow[i]
            else:
                node = alg.mul(p_pow[i], q_pow[j])
                field_products += 1
            expression = alg.add(expression, scaled(alg, node, coefficient[i][j]))
    circ.require_zero(expression.bits())
    for wires in (a_bits, b_bits):
        for code in range(1 << len(design.BITS)):
            if code not in design.ALLOWED_CODES:
                circ.clauses.append(forbid_code(circ, wires, code) + ' 0')
    column_rejects = 0
    for code_a, col_a in columns[0].items():
        for code_b, col_b in columns[1].items():
            if col_a.isdisjoint(col_b):
                continue
            circ.clauses.append(forbid_code(circ, a_bits, code_a) + ' ' +
                                forbid_code(circ, b_bits, code_b) + ' 0')
            column_rejects += 1
    assert column_rejects == 77
    counts = {'variables': circ.next_var-1, 'clauses':len(circ.clauses),
              'xor_rows':len(circ.xors), 'and_gates':circ.and_count,
              'field_products':field_products}
    witness_check = None
    if key['exact_member']:
        assignment = {}
        for slot, state_id in enumerate(key['reference_witness']):
            mask = source['states'][slot][state_id]['masks'][0]
            code = sum(((mask >> bit) & 1) << index
                       for index, bit in enumerate(design.BITS))
            wires = a_bits if slot == 0 else b_bits
            assignment.update({wire: (code >> bit) & 1
                               for bit, wire in enumerate(wires)})
        completed = selector.old.complete_assignment(circ, assignment)
        witness_check = selector.old.check_assignment(circ, completed)
        assert witness_check == {'clauses':counts['clauses'],
                                 'native_xor_rows':counts['xor_rows']}
    formula = HERE / f'{key_id}_resultant.xcnf'
    assert not formula.exists()
    circ.write(formula)
    rows.append({'key_id':key_id,'exact_member':key['exact_member'],
                 'counts':counts,'constructed_witness_check':witness_check,
                 'formula_sha256':sha(formula),'formula_bytes':formula.stat().st_size,
                 'build_wall_seconds':time.monotonic()-started,
                 'input_wires':[a_bits,b_bits]})
result = {'status':'PASS_N41_RESULTANT_HOLDOUT_SAT_BUILD',
          'candidate_id':None,'curve_id':protocol['curve_id'],
          'rows':rows,'protocol_sha256':sha(HERE/'holdout_build_protocol.json')}
(HERE/'holdout_build_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':result['status'],
                  'counts':[row['counts'] for row in rows]}))
