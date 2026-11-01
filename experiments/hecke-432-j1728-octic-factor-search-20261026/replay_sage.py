"""Proof-grade divisor check and source/branch replay for a p-1 factor."""
import importlib.util
import json
from hashlib import sha256
from pathlib import Path

from sage.all import GF, PolynomialRing, QQ, ZZ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'pm1_result': HERE / 'pm1_result.json',
    'factor_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'coordinate_map': ROOT / 'experiments/hecke-27-coordinate-bridge-20261025/coordinate_map.json',
    'resolvent': ROOT / 'experiments/hecke-432-relative-resolvent-20261025/relative_resolvent.json',
    'branch_formula': ROOT / 'experiments/hecke-432-b-coordinate-resolvent-20261025/branch_formula.json',
    'source_helpers': ROOT / 'experiments/hecke-432-j1728-norm-power-20261026/classify_large_sage.py',
}


def main():
    protocol_path = HERE / 'replay_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    for name, path in INPUTS.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    p = ZZ(protocol['candidate_divisor'])
    factor_run = json.loads(INPUTS['pm1_result'].read_text())
    assert any(int(row['gcd']) == p and row['status'] == 'FACTOR'
               for row in factor_run['rows'])
    original = ZZ(json.loads((HERE / 'pm1_protocol.json').read_text())['input_integer'])
    assert original % p == 0 and 1 < p < original
    prime = bool(p.is_prime(proof=True))
    out = {'status': 'PROVED_PRIME_SOURCE_REPLAY' if prime else 'COMPOSITE_DIVISOR',
           'prime_divisor': str(p), 'divisor_is_prime_proof': prime,
           'quotient': str(original // p),
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest()}
    if prime:
        spec = importlib.util.spec_from_file_location('source_helpers', INPUTS['source_helpers'])
        helpers = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helpers)
        F = GF(p)
        field = json.loads(INPUTS['factor_certificate'].read_text())
        coord = json.loads(INPUTS['coordinate_map'].read_text())['source_j']
        resolvent = json.loads(INPUTS['resolvent'].read_text())['terms']
        branch = json.loads(INPUTS['branch_formula'].read_text())
        Rx = PolynomialRing(F, 'x')
        xvar = Rx.gen()
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
            pairs = []
            for z, _ in R.roots():
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
                         'rational_x_E_roots': len(R.roots()), 'pairs': pairs})
        rows.sort(key=lambda row: row['C_point'])
        out.update({'rational_C_points': len(sources),
                    'rational_CE_pairs': sum(len(row['pairs']) for row in rows),
                    'zero_branch_pairs': sum(pair['branch_denominator_zero']
                                             for row in rows for pair in row['pairs']),
                    'rows': rows})
    (HERE / 'replay_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({key: out.get(key) for key in ('status', 'prime_divisor',
          'rational_C_points', 'rational_CE_pairs', 'zero_branch_pairs')},
          sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
