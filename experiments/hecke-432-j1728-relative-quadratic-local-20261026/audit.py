"""Exact integer replay of local quadratic discriminant parity and index data."""
import json
import sys
from hashlib import sha256
from pathlib import Path

sys.set_int_max_str_digits(10000)
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
protocol = json.loads((HERE / 'protocol.json').read_text())
result = json.loads((HERE / 'result.json').read_text())
assert result['status'] == 'PASS_LOCAL_QUADRATIC_DISCRIMINANT_PARITY'
known_path = ROOT / 'experiments/hecke-432-j1728-discriminant-norms-20261026/relative_result.json'
assert sha256(known_path.read_bytes()).hexdigest() == protocol['input_sha256']['relative_discriminant_result']
known = next(row for row in json.loads(known_path.read_text())['rows'] if row['base_degree'] == 4)
norm = int(known['relative_discriminant_norm_numerator'])


def valuation(n, p):
    count = 0
    while n % p == 0:
        n //= p
        count += 1
    return count


rows = []
for row in result['rows']:
    p = row['prime']
    assert p in protocol['primes'] and p % 2 == 1
    places = row['places']
    assert sum(v['residue_degree'] for v in places) == 36
    support = [[], []]
    weighted = [0, 0]
    for place in places:
        f = place['residue_degree']
        values = [place['left_discriminant_valuation'], place['right_discriminant_valuation']]
        assert all(v >= 0 and v % 2 == 0 for v in values)
        for side in (0, 1):
            coeffs = place['left_coefficient_valuations' if side == 0 else 'right_coefficient_valuations']
            assert len(coeffs) == 3 and all(v is None or v >= 0 for v in coeffs)
            assert place['left_local_order_index_exponent' if side == 0 else 'right_local_order_index_exponent'] == values[side] // 2
            assert not place['left_ramifies_by_odd_discriminant_valuation' if side == 0 else 'right_ramifies_by_odd_discriminant_valuation']
            weighted[side] += f * values[side]
            if values[side]:
                support[side].append(f)
    assert weighted == row['weighted_discriminant_valuations'] == [valuation(norm, p)] * 2
    assert row['odd_left_place_count'] == row['odd_right_place_count'] == 0
    rows.append({'prime': p, 'place_count': len(places),
                 'relative_discriminant_norm_valuation': weighted[0],
                 'left_local_index_support_degrees': sorted(support[0]),
                 'right_local_index_support_degrees': sorted(support[1]),
                 'all_local_quadratic_discriminant_valuations_even': True})
assert [r['prime'] for r in rows] == protocol['primes']
audit = {'status': 'PASS_LOCAL_QUADRATIC_PARITY_INTEGER_REPLAY',
         'result_sha256': sha256((HERE / 'result.json').read_bytes()).hexdigest(),
         'rows': rows}
(HERE / 'audit.json').write_text(json.dumps(audit, sort_keys=True, indent=2) + '\n')
print(json.dumps({'status': audit['status'], 'support':
                  {str(r['prime']): r['left_local_index_support_degrees'] for r in rows}},
                 sort_keys=True))
