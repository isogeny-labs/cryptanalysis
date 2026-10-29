"""Independent finite-field gcd, derivative, and branch audit."""
import json
import runpy
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'multiplicity_result': HERE / 'multiplicity_result.json',
    'factor_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'branch_formula': ROOT / 'experiments/hecke-432-b-coordinate-resolvent-20261025/branch_formula.json',
    'fast_gate_source': ROOT / 'experiments/hecke-432-j1728-fast-local-root-gate-20261026/run.py',
}


def evaluate(coefficients, z, p):
    value = 0
    for c in reversed(coefficients):
        value = (value * z + c) % p
    return value


def branch_value(terms, x, y, z, p):
    return sum(int(t['integer_coefficient'])
               * pow(x, t['x_C_exponent'], p)
               * pow(y, t['y_C_exponent'], p)
               * pow(z, t['x_E_exponent'], p) for t in terms) % p


def main():
    path = HERE / 'audit_protocol.json'
    protocol = json.loads(path.read_text())
    for name, source in INPUTS.items():
        assert sha256(source.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    sage = json.loads(INPUTS['multiplicity_result'].read_text())
    field = json.loads(INPUTS['factor_certificate'].read_text())
    branch = json.loads(INPUTS['branch_formula'].read_text())
    gate = runpy.run_path(str(INPUTS['fast_gate_source']))
    mod_fraction = gate['mod_fraction']
    arithmetic_class = gate['PolynomialArithmetic']
    results = []
    for prime_row in sage['results']:
        p = int(prime_row['prime'])
        rational_roots = 0
        repeated_roots = 0
        branch_zero = 0
        gcd_degrees = []
        for source in prime_row['rows']:
            x, y = map(int, source['C_point'])
            for factor in field['factors']:
                degree = len(factor['coefficients_low_to_high']) - 1
                arith = arithmetic_class(p)
                coefficients = [sum(mod_fraction(c, p) * pow(x, i, p)
                                    for i, c in enumerate(vector)) % p
                                for vector in factor['coefficients_low_to_high']]
                coefficients = arith.normal(coefficients)
                assert len(coefficients) - 1 == degree
                derivative = [(i * coefficients[i]) % p
                              for i in range(1, len(coefficients))]
                repeated = arith.gcd(coefficients, derivative)
                xp = arith.powmod([0, 1], p, coefficients)
                rational = arith.gcd(coefficients, arith.sub(xp, [0, 1]))
                matching = [r for r in source['roots'] if r['factor_degree'] == degree]
                assert len(matching) == len(rational) - 1
                rational_roots += len(matching)
                gcd_degrees.append({'C_point': source['C_point'],
                                    'factor_degree': degree,
                                    'derivative_gcd_degree': len(repeated) - 1,
                                    'rational_root_count': len(matching)})
                for row in matching:
                    z = int(row['x_E'])
                    assert evaluate(coefficients, z, p) == 0
                    derivative_zero = evaluate(derivative, z, p) == 0
                    assert derivative_zero == row['derivative_zero']
                    bn = branch_value(branch['numerator_terms'], x, y, z, p)
                    bd = branch_value(branch['denominator_terms'], x, y, z, p)
                    assert (bn == 0) == row['branch_numerator_zero']
                    assert (bd == 0) == row['branch_denominator_zero']
                    assert derivative_zero == (bn == 0) == (bd == 0)
                    repeated_roots += derivative_zero
                    branch_zero += bn == 0 and bd == 0
        assert repeated_roots == prime_row['quartic_repeated'] + prime_row['octic_repeated']
        assert branch_zero == prime_row['branch_zero']
        results.append({'prime': str(p), 'rational_factor_roots': rational_roots,
                        'repeated_roots': repeated_roots,
                        'branch_zero_roots': branch_zero,
                        'gcd_degrees': gcd_degrees})
    out = {'status': 'PASS_INDEPENDENT_DERIVATIVE_GCD_AND_BRANCH_AUDIT',
           'protocol_sha256': sha256(path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'results': results}
    (HERE / 'audit_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'],
                      'summary': [{k: r[k] for k in ('prime', 'rational_factor_roots',
                        'repeated_roots', 'branch_zero_roots')}
                        for r in results]}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
