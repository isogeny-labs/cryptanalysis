"""Independently check SAT bits, XCNF constraints, and public group witness."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / 'replay_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
assert not (HERE / 'replay_result.json').exists()
build = json.loads((HERE / 'sat_build_result.json').read_text())
query = json.loads((HERE / 'sat_query_result.json').read_text())
keys = json.loads(Path(protocol['keys']).read_text())
source = json.loads(Path(protocol['source_states']).read_text())
R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(R([(int(word) >> bit) & 1 for bit in range(41)]))


model_row = next(row for row in query['rows'] if row['key_id'] == 'P0')
assert model_row['status'] == 'SAT_MODEL_UNVERIFIED'
build_row = next(row for row in build['rows'] if row['key_id'] == 'P0')
stream = (HERE / 'P0_resultant.stdout').read_text().splitlines()
assert stream[0] == 's SATISFIABLE'
assignment = {}
for line in stream[1:]:
    assert line.startswith('v ')
    for literal in map(int, line.split()[1:]):
        if literal == 0:
            continue
        variable = abs(literal)
        assert variable not in assignment
        assignment[variable] = literal > 0
assert len(assignment) == build_row['counts']['variables']
clauses = xors = 0
with (HERE / 'P0_resultant.xcnf').open() as formula:
    header = next(formula).split()
    assert header[:2] == ['p', 'cnf']
    assert int(header[2]) == len(assignment)
    for line in formula:
        xor_row = line.startswith('x')
        tokens = line[1:] if xor_row else line
        literals = list(map(int, tokens.split()))
        assert literals[-1] == 0
        values = [assignment[abs(lit)] if lit > 0 else not assignment[abs(lit)]
                  for lit in literals[:-1]]
        if xor_row:
            assert sum(values) % 2 == 1
            xors += 1
        else:
            assert any(values)
            clauses += 1
assert clauses == build_row['counts']['clauses']
assert xors == build_row['counts']['xor_rows']
assert clauses + xors == int(header[3])
codes = [sum(int(assignment[wire]) << bit for bit, wire in enumerate(wires))
         for wires in build_row['input_wires']]
source_rows = []
for slot, code in enumerate(codes):
    ids = []
    for state_id, row in enumerate(source['states'][slot]):
        mask = row['masks'][0]
        row_code = sum(((mask >> bit) & 1) << index
                       for index, bit in enumerate((0, 1, 2, 3, 4, 6, 7, 8)))
        if row_code == code:
            ids.append(state_id)
    assert len(ids) == 4
    source_rows.append(ids)
key = next(row for row in keys['keys'] if row['key_id'] == 'P0')
target = E(*map(dec, key['point']))
witnesses = []
for a in source_rows[0]:
    row_a = source['states'][0][a]
    A = E(*map(dec, row_a['point']))
    for b in source_rows[1]:
        row_b = source['states'][1][b]
        if not set(row_a['columns']).isdisjoint(row_b['columns']):
            continue
        B = E(*map(dec, row_b['point']))
        if A+B == target:
            witnesses.append([a,b])
assert key['reference_witness'] in witnesses
result = {'status':'PASS_N41_RESULTANT_SAT_INDEPENDENT_GROUP_REPLAY',
          'candidate_id':None,'curve_id':protocol['curve_id'],
          'key_id':'P0','source_codes':codes,'source_state_ids':source_rows,
          'witnesses':witnesses,'verified_cnf_clauses':clauses,
          'verified_native_xor_rows':xors,
          'model_literals':len(assignment),
          'protocol_sha256':sha(HERE/'replay_protocol.json')}
(HERE/'replay_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':result['status'],'source_codes':codes,
                  'witnesses':witnesses,'clauses':clauses,'xors':xors}))
