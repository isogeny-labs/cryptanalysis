"""Extract certified local components from squarefree reduction factors."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'hecke-432-j1728-relative-quartic-local-order-20261026'


def one_side(places, side):
    absolute_degrees = Counter()
    unresolved_local_mass = 0
    unresolved_absolute_mass = 0
    fully_determined_places = 0
    partial_places = 0
    place_rows = []
    for i, place in enumerate(places):
        f_base = place['residue_degree']
        evidence = place[side]
        factors = evidence['reduced_factor_degrees_exponents']
        assert all(d > 0 and e > 0 for d, e in factors)
        assert sum(d * e for d, e in factors) == 4
        assert evidence['discriminant_valuation'] % 2 == 0
        assert all(v >= 0 for v in evidence['coefficient_valuations'])
        known = sorted(d for d, e in factors if e == 1)
        unknown = sum(d * e for d, e in factors if e > 1)
        assert sum(known) + unknown == 4
        for d in known:
            absolute_degrees[d * f_base] += 1
        unresolved_local_mass += unknown
        unresolved_absolute_mass += unknown * f_base
        fully_determined_places += unknown == 0
        partial_places += unknown > 0 and bool(known)
        place_rows.append({'place_index': i, 'base_residue_degree': f_base,
                           'certified_relative_degrees': known,
                           'unresolved_relative_degree_mass': unknown,
                           'polynomial_discriminant_valuation': evidence['discriminant_valuation']})
    assert sum(d * n for d, n in absolute_degrees.items()) + unresolved_absolute_mass == 144
    return {'base_places': len(places), 'fully_determined_places': fully_determined_places,
            'partially_determined_places': partial_places,
            'certified_absolute_degree_counts': [[d, n] for d, n in sorted(absolute_degrees.items())],
            'certified_absolute_prime_count': sum(absolute_degrees.values()),
            'unresolved_relative_degree_mass': unresolved_local_mass,
            'unresolved_absolute_degree_mass': unresolved_absolute_mass,
            'places': place_rows}


def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    support_path = SOURCE / 'conjugate_support_result.json'
    assert sha256(support_path.read_bytes()).hexdigest() == protocol['input_sha256']['local_order_support_result']
    support = json.loads(support_path.read_text())
    assert support['status'] == 'PASS_CONJUGATE_RELATIVE_DISCRIMINANT_SUPPORT'
    assert support['fixed_integer_in_left_discriminant_ideal'] == 96
    source_path = SOURCE / 'result.json'
    source = json.loads(source_path.read_text())
    assert source['status'] == 'PASS_RELATIVE_QUARTIC_LOCAL_SCREEN'
    rows = []
    for row, sr in zip(source['rows'], support['rows']):
        assert row['prime'] == sr['prime']
        assert row['prime'] in protocol['primes']
        assert len(row['places']) == len(sr['places'])
        assert 96 % row['prime'] != 0
        sides = {}
        for side in ('left', 'right'):
            assert all(place[f'{side}_relative_discriminant_valuation' +
                             ('_from_conjugation' if side == 'right' else '')] == 0
                       for place in sr['places'])
            sides[side] = one_side(row['places'], side)
        rows.append({'prime': row['prime'], 'sides': sides})
    assert [r['prime'] for r in rows] == protocol['primes']
    out = {'status': 'PASS_CERTIFIED_SQUAREFREE_COMPONENTS',
           'method': 'monic-integral local polynomial: each exponent-one residue factor Hensel-lifts uniquely; repeated blocks retained as unresolved degree mass',
           'source_sha256': sha256(source_path.read_bytes()).hexdigest(),
           'support_sha256': sha256(support_path.read_bytes()).hexdigest(),
           'rows': rows}
    (HERE / 'squarefree_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    for r in rows:
        print(json.dumps({'prime': r['prime'], 'left_certified_primes': r['sides']['left']['certified_absolute_prime_count'],
                          'right_certified_primes': r['sides']['right']['certified_absolute_prime_count'],
                          'left_unresolved_absolute_mass': r['sides']['left']['unresolved_absolute_degree_mass'],
                          'right_unresolved_absolute_mass': r['sides']['right']['unresolved_absolute_degree_mass']}, sort_keys=True))


if __name__ == '__main__':
    main()
