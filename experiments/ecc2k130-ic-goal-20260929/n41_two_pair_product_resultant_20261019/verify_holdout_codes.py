"""Compare the compact resultant with exact N41 source-code pairs."""
import hashlib
import json
import sys
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = Path('/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929')
sys.path.insert(0, str(ROOT / 'n41_w9_lazy_source_20261017'))
import circuit as design


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / 'holdout_verify_protocol.json').read_text())
for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
assert not (HERE / 'holdout_verify_result.json').exists()
resultant = json.loads((HERE / 'resultant.json').read_text())
keys = json.loads(Path(protocol['keys']).read_text())
source = json.loads(Path(protocol['source_states']).read_text())
S = PolynomialRing(GF(2), 'u')
u = S.gen()
F = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(S([(int(word) >> bit) & 1 for bit in range(41)]))


code_rows = []
for slot in (0, 1):
    entries = {}
    for state_id, row in enumerate(source['states'][slot]):
        mask = row['masks'][0]
        code = sum(((mask >> bit) & 1) << index
                   for index, bit in enumerate(design.BITS))
        if code not in entries:
            product = sum((dec(basis) for index, basis in enumerate(design.PB)
                           if code >> index & 1), F.zero())
            if slot == 1:
                product = product**64
            entries[code] = {'product': product, 'columns': set(row['columns']),
                             'state_ids': []}
        assert entries[code]['columns'] == set(row['columns'])
        entries[code]['state_ids'].append(state_id)
    assert len(entries) == 71 and all(len(entry['state_ids']) == 4
                                      for entry in entries.values())
    code_rows.append(entries)
state_points = [[E(*map(dec, row['point'])) for row in source['states'][slot]]
                for slot in (0, 1)]
terms = [(tuple(row['exponents']), dec(row['coefficient']))
         for row in resultant['terms']]
rows = []
for key in keys['keys']:
    started = time.monotonic()
    t = (dec(key['reciprocal_x']) if 'reciprocal_x' in key
         else 1 / dec(key['point'][0]))
    t_powers = [t**index for index in range(9)]
    coeff = [[F.zero() for _ in range(5)] for _ in range(5)]
    for (i, j, k), value in terms:
        coeff[i][j] += value*t_powers[k]
    key_point = E(*map(dec, key['point']))
    zeros = []
    checked_pairs = 0
    for code_a, left in code_rows[0].items():
        p = left['product']
        p_powers = [p**index for index in range(5)]
        q_coeff = [sum((coeff[i][j]*p_powers[i] for i in range(5)), F.zero())
                   for j in range(5)]
        for code_b, right in code_rows[1].items():
            if not left['columns'].isdisjoint(right['columns']):
                continue
            checked_pairs += 1
            q = right['product']
            value = sum((q_coeff[j]*q**j for j in range(5)), F.zero())
            if value != 0:
                continue
            witnesses = [[a, b] for a in left['state_ids']
                         for b in right['state_ids']
                         if state_points[0][a] + state_points[1][b] == key_point]
            zeros.append({'codes': [code_a, code_b], 'witnesses': witnesses})
    found = any(row['witnesses'] for row in zeros)
    assert found == key['exact_member']
    rows.append({'key_id': key['key_id'], 'exact_member': key['exact_member'],
                 'admissible_code_pairs': checked_pairs,
                 'resultant_zero_code_pairs': len(zeros),
                 'zero_pairs': zeros, 'verified_member': found,
                 'wall_seconds': time.monotonic()-started})
    print(json.dumps({'key_id':key['key_id'],'code_pairs':checked_pairs,
                      'resultant_zeros':len(zeros),'verified_member':found,
                      'wall_seconds':rows[-1]['wall_seconds']}),flush=True)
result = {'status':'PASS_N41_RESULTANT_HOLDOUT_CODE_CENSUS','candidate_id':None,
          'curve_id':protocol['curve_id'],'rows':rows,
          'protocol_sha256':sha(HERE/'holdout_verify_protocol.json')}
(HERE/'holdout_verify_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
