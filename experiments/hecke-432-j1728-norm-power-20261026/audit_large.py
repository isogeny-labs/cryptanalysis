"""Independent Python source, local-gcd, and equation replay at the large prime."""
import json
import runpy
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'factor_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'coordinate_map': ROOT / 'experiments/hecke-27-coordinate-bridge-20261025/coordinate_map.json',
    'resolvent': ROOT / 'experiments/hecke-432-relative-resolvent-20261025/relative_resolvent.json',
    'branch_formula': ROOT / 'experiments/hecke-432-b-coordinate-resolvent-20261025/branch_formula.json',
    'fast_gate_source': ROOT / 'experiments/hecke-432-j1728-fast-local-root-gate-20261026/run.py',
}


def rational_terms(terms, x, y, p):
    total = 0
    for t in terms:
        q = Fraction(t['coefficient'])
        total += (q.numerator * pow(q.denominator, -1, p)
                  * pow(x, t['x_power'], p) * pow(y, t['y_power'], p))
    return total % p


def integer_terms(terms, x, y, z, p):
    return sum(int(t['integer_coefficient'])
               * pow(x, t['x_C_exponent'], p)
               * pow(y, t['y_C_exponent'], p)
               * pow(z, t['x_E_exponent'], p) for t in terms) % p


def base_factor_value(factor, x, z, p):
    value = 0
    for vector in reversed(factor['coefficients_low_to_high']):
        coefficient = 0
        for raw in reversed(vector):
            q = Fraction(raw)
            coefficient = (coefficient * x
                           + q.numerator * pow(q.denominator, -1, p)) % p
        value = (value * z + coefficient) % p
    return value


def main():
    pp = HERE / 'protocol.json'
    protocol = json.loads(pp.read_text())
    lp = HERE / 'local_audit_protocol.json'
    local_protocol = json.loads(lp.read_text())
    rp = HERE / 'large_prime_result.json'
    assert sha256(rp.read_bytes()).hexdigest() == local_protocol['large_prime_result_sha256']
    registered = json.loads(rp.read_text())
    for name, path in INPUTS.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    p = protocol['large_prime']
    assert int(registered['prime']) == p
    field = json.loads(INPUTS['factor_certificate'].read_text())
    coordinate = json.loads(INPUTS['coordinate_map'].read_text())['source_j']
    resolvent = json.loads(INPUTS['resolvent'].read_text())['terms']
    branch = json.loads(INPUTS['branch_formula'].read_text())
    gate = runpy.run_path(str(INPUTS['fast_gate_source']))
    field_roots, sources, undefined = gate['source_points'](p, field, coordinate)
    expected_sources = sorted([int(v) for v in row['C_point']]
                              for row in registered['rows'])
    assert sources == expected_sources and not undefined
    fibers = []
    total_pairs = 0
    total_polynomial_multiplications = 0
    root_factor_degrees = []
    for row in registered['rows']:
        x, y = map(int, row['C_point'])
        assert (y * y + y - x ** 3 + 7) % p == 0
        numerator = rational_terms(coordinate['numerator'], x, y, p)
        denominator = rational_terms(coordinate['denominator'], x, y, p)
        assert denominator and (numerator + 1728 * denominator) % p == 0
        counted = gate['fiber_gate'](p, x, y, resolvent)
        assert counted['status'] == 'EXACT_LOCAL_POLYNOMIAL_GCD_GATE'
        assert counted['rational_x_E_roots'] == row['rational_x_E_roots']
        assert counted['rational_CE_pairs'] == row['rational_CE_pairs']
        assert counted['resolvent_degree'] == row['resolvent_degree']
        total_pairs += counted['rational_CE_pairs']
        total_polynomial_multiplications += counted['arithmetic_counts']['polynomial_multiplications']
        for pair in row['pairs']:
            z, ye = map(int, pair['E_point'])
            assert (ye * ye - z ** 3 - 432) % p == 0
            assert integer_terms(resolvent, x, y, z, p) == 0
            bn = integer_terms(branch['numerator_terms'], x, y, z, p)
            bd = integer_terms(branch['denominator_terms'], x, y, z, p)
            assert (bn == 0) == pair['branch_numerator_zero']
            assert (bd == 0) == pair['branch_denominator_zero']
            assert pair['status'] == 'ZERO_DENOMINATOR' and bn == bd == 0
            factor_values = [(len(factor['coefficients_low_to_high']) - 1,
                              base_factor_value(factor, x, z, p))
                             for factor in field['factors']]
            assert [degree for degree, value in factor_values if value == 0] == [4]
            root_factor_degrees.append(4)
        fibers.append(counted)
    assert total_pairs == registered['rational_CE_pairs'] == 2
    out = {'status': 'PASS_INDEPENDENT_LARGE_PRIME_GCD_AND_EQUATION_REPLAY',
           'protocol_sha256': sha256(pp.read_bytes()).hexdigest(),
           'local_audit_protocol_sha256': sha256(lp.read_bytes()).hexdigest(),
           'registered_result_sha256': sha256(rp.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'prime': str(p), 'field_poly_rational_roots': len(field_roots),
           'source_points': len(sources), 'rational_CE_pairs': total_pairs,
           'root_factor_degrees': root_factor_degrees,
           'polynomial_multiplications': total_polynomial_multiplications,
           'fibers': fibers}
    (HERE / 'large_prime_audit.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({key: out[key] for key in
                      ('status', 'prime', 'source_points', 'rational_CE_pairs',
                       'polynomial_multiplications')}, sort_keys=True))


if __name__ == '__main__':
    main()
