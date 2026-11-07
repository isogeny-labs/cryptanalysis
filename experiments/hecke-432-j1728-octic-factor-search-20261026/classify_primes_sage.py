"""Proof-grade prime split and original source/branch classification."""
import importlib.util
import json
from hashlib import sha256
from pathlib import Path

from sage.all import GF, PolynomialRing, QQ, ZZ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'composite_divisor_result': HERE / 'composite_divisor_result.json',
    'replay_protocol': HERE / 'replay_protocol.json',
    'pm1_result': HERE / 'pm1_result.json',
    'factor_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'coordinate_map': ROOT / 'experiments/hecke-27-coordinate-bridge-20261025/coordinate_map.json',
    'resolvent': ROOT / 'experiments/hecke-432-relative-resolvent-20261025/relative_resolvent.json',
    'branch_formula': ROOT / 'experiments/hecke-432-b-coordinate-resolvent-20261025/branch_formula.json',
    'source_helpers': ROOT / 'experiments/hecke-432-j1728-norm-power-20261026/classify_large_sage.py',
}


def classify(p, field, coord, resolvent, branch, helpers):
    F = GF(p)
    Rx = PolynomialRing(F, 'x')
    f = Rx([F(QQ(c)) for c in field['field_polynomial_coefficients_low_to_high']])
    sources = []
    for x, _ in f.roots():
        Ry = PolynomialRing(F, 'y')
        yvar = Ry.gen()
        for y, _ in (yvar ** 2 + yvar - x ** 3 + 7).roots():
            numerator = helpers.source_expression(coord['numerator'], x, y, F)
            denominator = helpers.source_expression(coord['denominator'], x, y, F)
            if denominator and numerator + 1728 * denominator == 0:
                sources.append((x, y))
    Rz = PolynomialRing(F, 'z')
    zvar = Rz.gen()
    rows = []
    for x, y in sources:
        R = helpers.chain_expression(resolvent, x, y, zvar, F)
        roots = R.roots()
        pairs = []
        for z, _ in roots:
            rhs = z ** 3 + 432
            if not rhs.is_square():
                continue
            y_values = [F(0)] if rhs == 0 else [rhs.sqrt(), -rhs.sqrt()]
            for ye in y_values:
                assert ye ** 2 == rhs
                bn = helpers.chain_expression(branch['numerator_terms'], x, y, z, F)
                bd = helpers.chain_expression(branch['denominator_terms'], x, y, z, F)
                factor_degrees = []
                for factor in field['factors']:
                    value = F(0)
                    for vector in reversed(factor['coefficients_low_to_high']):
                        coefficient = Rx([F(QQ(c)) for c in vector])(x)
                        value = value * z + coefficient
                    if value == 0:
                        factor_degrees.append(len(factor['coefficients_low_to_high']) - 1)
                pairs.append({'E_point': [str(int(z)), str(int(ye))],
                              'branch_numerator_zero': bool(bn == 0),
                              'branch_denominator_zero': bool(bd == 0),
                              'base_factor_degrees': factor_degrees})
        rows.append({'C_point': [str(int(x)), str(int(y))],
                     'rational_x_E_roots': len(roots), 'pairs': pairs})
    rows.sort(key=lambda row: row['C_point'])
    return {'prime': str(p), 'class_mod_24': int(p % 24),
            'field_poly_rational_roots': len(f.roots()),
            'rational_C_points': len(sources),
            'rational_CE_pairs': sum(len(row['pairs']) for row in rows),
            'zero_branch_pairs': sum(pair['branch_denominator_zero']
                                     for row in rows for pair in row['pairs']),
            'rows': rows}


def main():
    protocol_path = HERE / 'prime_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    for name, path in INPUTS.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    factors = [ZZ(n) for n in protocol['factors']]
    composite = ZZ(protocol['composite_divisor'])
    assert len(factors) == 2 and factors[0] * factors[1] == composite
    original = ZZ(json.loads((HERE / 'pm1_protocol.json').read_text())['input_integer'])
    assert original % composite == 0
    for p in factors:
        assert p.is_prime(proof=True)
    spec = importlib.util.spec_from_file_location('source_helpers', INPUTS['source_helpers'])
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    field = json.loads(INPUTS['factor_certificate'].read_text())
    coord = json.loads(INPUTS['coordinate_map'].read_text())['source_j']
    resolvent = json.loads(INPUTS['resolvent'].read_text())['terms']
    branch = json.loads(INPUTS['branch_formula'].read_text())
    rows = [classify(p, field, coord, resolvent, branch, helpers) for p in factors]
    out = {'status': 'PROVED_PRIME_SPLIT_AND_SOURCE_REPLAY',
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'composite_divisor': str(composite),
           'prime_factors': [str(p) for p in factors],
           'prime_factors_proved': True,
           'remaining_cofactor': str(original // composite),
           'rows': rows}
    (HERE / 'prime_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'],
                      'counts': [{k: row[k] for k in ('prime', 'rational_C_points',
                                  'rational_CE_pairs', 'zero_branch_pairs')}
                                 for row in rows]}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
