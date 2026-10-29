"""Independent coefficient-conjugation and local-index arithmetic replay."""
import json
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
screen = json.loads((HERE / 'result.json').read_text())
direct = json.loads((HERE / 'direct_rnfdisc_side0.json').read_text())
transport = json.loads((HERE / 'conjugate_support_result.json').read_text())
split = json.loads((ROOT / 'experiments/hecke-432-j1728-sqrt2-split-20261026/sqrt2_factor_certificate.json').read_text())
assert screen['status'] == 'PASS_RELATIVE_QUARTIC_LOCAL_SCREEN'
assert direct['status'] == 'PASS_DIRECT_RNFDISC_RELATIVE_IDEAL'
assert transport['status'] == 'PASS_CONJUGATE_RELATIVE_DISCRIMINANT_SUPPORT'
assert '96' in direct['relative_discriminant_ideal_generators']
octic = next(r for r in split['records'] if r['base_degree'] == 8)
left, right = octic['factors']
assert len(left['coefficients_low_to_high']) == len(right['coefficients_low_to_high']) == 5


def vector(values):
    return tuple(Fraction(x) for x in values)


for a, b in zip(left['coefficients_low_to_high'], right['coefficients_low_to_high']):
    assert vector(a[0]) == vector(b[0])
    assert vector(a[1]) == tuple(-x for x in vector(b[1]))


direct_rows = {r['prime']: {tuple(v['ideal_generators']): v for v in r['places']}
               for r in direct['rows']}
transport_rows = {r['prime']: {tuple(v['ideal_generators']): v for v in r['places']}
                  for r in transport['rows']}
rows = []
for row in screen['rows']:
    p = row['prime']
    transport_summary = next(x for x in transport['rows'] if x['prime'] == p)
    assert p in (7, 11, 23, 31) and 96 % p
    assert len(row['places']) == len(direct_rows[p]) == len(transport_rows[p])
    index_counts = [0, 0]
    weighted_polynomial = [0, 0]
    weighted_index = [0, 0]
    for place in row['places']:
        key = tuple(place['ideal_generators'])
        d = direct_rows[p][key]
        t = transport_rows[p][key]
        f = place['residue_degree']
        for side in (0, 1):
            name = ('left', 'right')[side]
            v = place[name]['discriminant_valuation']
            assert v >= 0 and v % 2 == 0
            field_key = ('left_relative_discriminant_valuation' if side == 0 else
                         'right_relative_discriminant_valuation_from_conjugation')
            assert t[field_key] == 0
            assert t[f'{name}_local_order_index_exponent'] == v // 2
            weighted_polynomial[side] += f * v
            weighted_index[side] += f * (v // 2)
            index_counts[side] += v > 0
        assert d['polynomial_discriminant_valuation'] == place['left']['discriminant_valuation']
        assert d['maximal_order_relative_discriminant_valuation'] == 0
        assert d['local_order_index_exponent'] == place['left']['discriminant_valuation'] // 2
    assert index_counts == [transport_summary['left_positive_index_places'],
                            transport_summary['right_positive_index_places']]
    assert weighted_polynomial == row['weighted_discriminant_valuations']
    assert weighted_polynomial == [2 * v for v in weighted_index]
    rows.append({'prime': p, 'place_count': len(row['places']),
                 'positive_index_places': index_counts,
                 'weighted_polynomial_discriminant_valuations': weighted_polynomial,
                 'weighted_order_index_exponents': weighted_index,
                 'maximal_relative_discriminant_valuations_zero': True})
audit = {'status': 'PASS_RELATIVE_QUARTIC_LOCAL_ORDER_AUDIT',
         'input_sha256': {name: sha256((HERE / name).read_bytes()).hexdigest()
                          for name in ('result.json', 'direct_rnfdisc_side0.json',
                                       'conjugate_support_result.json')},
         'coefficient_conjugation_independent_replay': True,
         'rows': rows}
(HERE / 'audit.json').write_text(json.dumps(audit, sort_keys=True, indent=2) + '\n')
print(json.dumps({'status': audit['status'],
                  'index_counts': [[r['prime'], *r['positive_index_places']] for r in rows]},
                 sort_keys=True))
