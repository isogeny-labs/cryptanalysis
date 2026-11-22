"""Check all dispersed SAT models against XCNF and independent Sage points."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / 'holdout_replay_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
assert not (HERE / 'holdout_replay_result.json').exists()
build = json.loads((HERE / 'holdout_build_result.json').read_text())
keys = json.loads(Path(protocol['keys']).read_text())
source = json.loads(Path(protocol['source_states']).read_text())
R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(R([(int(word) >> bit) & 1 for bit in range(41)]))


rows = []
for key_id in ('H0', 'H1', 'H2', 'H3'):
    build_row = next(row for row in build['rows'] if row['key_id'] == key_id)
    key = next(row for row in keys['keys'] if row['key_id'] == key_id)
    stream = (HERE / f'{key_id}_resultant.stdout').read_text().splitlines()
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
    with (HERE / f'{key_id}_resultant.xcnf').open() as formula:
        header = next(formula).split()
        assert header[:2] == ['p', 'cnf']
        assert int(header[2]) == len(assignment)
        for line in formula:
            xor_row = line.startswith('x')
            literals = list(map(int, (line[1:] if xor_row else line).split()))
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
    possible = []
    for slot, code in enumerate(codes):
        ids = []
        for state_id, state in enumerate(source['states'][slot]):
            mask = state['masks'][0]
            row_code = sum(((mask >> bit) & 1) << index
                           for index, bit in enumerate((0, 1, 2, 3, 4, 6, 7, 8)))
            if row_code == code:
                ids.append(state_id)
        assert len(ids) == 4
        possible.append(ids)
    target = E(*map(dec, key['point']))
    witnesses = []
    for a in possible[0]:
        state_a = source['states'][0][a]
        A = E(*map(dec, state_a['point']))
        for b in possible[1]:
            state_b = source['states'][1][b]
            if not set(state_a['columns']).isdisjoint(state_b['columns']):
                continue
            B = E(*map(dec, state_b['point']))
            if A+B == target:
                witnesses.append([a,b])
    assert key['reference_witness'] in witnesses
    rows.append({'key_id':key_id,'codes':codes,'witnesses':witnesses,
                 'verified_cnf_clauses':clauses,'verified_native_xor_rows':xors,
                 'model_literals':len(assignment),
                 'model_stdout_sha256':sha(HERE / f'{key_id}_resultant.stdout')})
result = {'status':'PASS_N41_RESULTANT_HOLDOUT_SAT_GROUP_REPLAY',
          'candidate_id':None,'curve_id':protocol['curve_id'],
          'rows':rows,'protocol_sha256':sha(HERE/'holdout_replay_protocol.json')}
(HERE/'holdout_replay_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':result['status'],
                  'witnesses':[row['witnesses'] for row in rows]}))
