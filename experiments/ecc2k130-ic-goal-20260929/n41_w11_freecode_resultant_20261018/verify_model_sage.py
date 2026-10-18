"""Independent XCNF-model and curve-sum check of the positive SAT row."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
cfg = json.loads((HERE / 'model_protocol.json').read_text())
for name, digest in cfg['sources'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest, name
assert not (HERE / 'model_result.json').exists()
stream = (HERE / 'solver_0.stdout').read_text()
assert 's SATISFIABLE' in stream
assignment = {}
for line in stream.splitlines():
    if line.startswith('v '):
        for token in line.split()[1:]:
            literal = int(token)
            if literal:
                assert abs(literal) not in assignment
                assignment[abs(literal)] = int(literal > 0)
formula = (HERE / 'positive.xcnf').read_text().splitlines()
assert formula[0].startswith('p cnf ')
_, _, variables, constraints = formula[0].split()
assert len(assignment) == int(variables) == 2259
cnf_checked = xor_checked = 0
for line in formula[1:]:
    if line.startswith('x'):
        literals = [int(value) for value in line[1:].split()]
        assert literals[-1] == 0
        assert sum(assignment[abs(v)] if v > 0 else 1-assignment[abs(v)]
                   for v in literals[:-1]) % 2 == 1
        xor_checked += 1
    else:
        literals = [int(value) for value in line.split()]
        assert literals[-1] == 0
        assert any(assignment[abs(v)] if v > 0 else 1-assignment[abs(v)]
                   for v in literals[:-1])
        cnf_checked += 1
assert cnf_checked+xor_checked == int(constraints)
assert (cnf_checked, xor_checked) == (6881, 458)
codes = [sum(assignment[1+10*slot+j] << j for j in range(10))
         for slot in range(2)]
assert codes == [253, 63]

P = PolynomialRing(GF(2), 'u')
u = P.gen()
K = GF(2**41, name='u', modulus=u**41+u**3+1)
E = EllipticCurve(K, [1, 0, 0, 0, 1])


def dec(n):
    return K(P([(n >> i) & 1 for i in range(41)]))


target = E(*(dec(v) for v in json.loads((HERE / 'export_result.json').read_text())['rows'][0]['target_point']))
states = [[], []]
with (ROOT / 'n41_w11_fivepair_native_join_20261018/join_input.tsv').open() as table:
    assert table.readline().split() == ['W11FIVE', '5', '1124', '1']
    for line in table:
        row = line.split()
        if row[0] == 'S' and int(row[1]) in (3, 4):
            slot = int(row[1])-3
            if int(row[3]) == codes[slot]:
                states[slot].append({'sid': int(row[2]),
                                     'columns': {int(row[7]), int(row[8])},
                                     'point': E(dec(int(row[9])), dec(int(row[10])))})
assert all(len(items) == 4 for items in states)
hits = []
for first in states[0]:
    for second in states[1]:
        if first['columns'].isdisjoint(second['columns']) and first['point']+second['point'] == target:
            hits.append([first['sid'], second['sid']])
assert hits == [[278, 74]]
result = {'status': 'PASS_N41_W11_FREECODE_SAT_MODEL_AND_GROUP',
          'candidate_id': None, 'curve_id': cfg['curve_id'],
          'codes': codes, 'model_variables': len(assignment),
          'cnf_checked': cnf_checked, 'native_xor_checked': xor_checked,
          'exact_group_state_id_hits': hits,
          'protocol_sha256': hashlib.sha256((HERE / 'model_protocol.json').read_bytes()).hexdigest()}
(HERE / 'model_result.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print(json.dumps(result, sort_keys=True))
