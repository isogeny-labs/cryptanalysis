"""Recover the original rational source fiber at a denominator exception."""
import importlib.util
import json
from hashlib import sha256
from pathlib import Path

from sage.all import GF, PolynomialRing, QQ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'field_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'coordinate_map': ROOT / 'experiments/hecke-27-coordinate-bridge-20261025/coordinate_map.json',
    'resolvent': ROOT / 'experiments/hecke-432-relative-resolvent-20261025/relative_resolvent.json',
    'branch_formula': ROOT / 'experiments/hecke-432-b-coordinate-resolvent-20261025/branch_formula.json',
}
INVERSE = ROOT / 'experiments/hecke-432-inverse-filter-crossprime-20261025/inverse_filter.py'


def load(path):
    spec = importlib.util.spec_from_file_location('frozen_inverse_filter', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expression(terms, x, y, F):
    return sum((F(QQ(term['coefficient'])) * x ** term['x_power']
                * y ** term['y_power'] for term in terms), F(0))


def main():
    pp = HERE / 'protocol.json'
    protocol = json.loads(pp.read_text())
    ep = HERE / 'exception_protocol.json'
    exception_protocol = json.loads(ep.read_text())
    scan_path = HERE / 'scan_result.json'
    assert sha256(scan_path.read_bytes()).hexdigest() == exception_protocol['input_scan_result_sha256']
    assert sha256(INVERSE.read_bytes()).hexdigest() == exception_protocol['inverse_filter_sha256']
    scan = json.loads(scan_path.read_text())
    primes = [row['prime'] for row in scan['new_exception_cells']]
    assert primes == exception_protocol['new_exception_primes']
    for name, path in INPUTS.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    cert = json.loads(INPUTS['field_certificate'].read_text())
    coord = json.loads(INPUTS['coordinate_map'].read_text())['source_j']
    resolvent = json.loads(INPUTS['resolvent'].read_text())
    branch = json.loads(INPUTS['branch_formula'].read_text())
    inverse = load(INVERSE)
    cells = []
    for p in primes:
        F = GF(p)
        Rx = PolynomialRing(F, 'x')
        x = Rx.gen()
        Ry = PolynomialRing(Rx, 'y')
        y = Ry.gen()
        curve = y * y + y - x ** 3 + 7
        H = expression(coord['numerator'], x, y, F) + 1728 * expression(coord['denominator'], x, y, F)
        source_eliminant = H.resultant(curve)
        field_poly = Rx([F(QQ(c)) for c in cert['field_polynomial_coefficients_low_to_high']])
        assert source_eliminant.degree() == 36
        assert source_eliminant.monic() == (field_poly * field_poly).monic()
        sources = []
        all_field_roots = []
        zero_y_formula = []
        for x0, _ in field_poly.roots():
            x0 = F(x0)
            all_field_roots.append(int(x0))
            Fy = PolynomialRing(F, 'v')
            v = Fy.gen()
            for y0, _ in (v * v + v - x0 ** 3 + 7).roots():
                y0 = F(y0)
                numerator = expression(coord['numerator'], x0, y0, F)
                denominator = expression(coord['denominator'], x0, y0, F)
                if denominator and numerator + 1728 * denominator == 0:
                    sources.append((x0, y0))
                    formula_den = sum((F(QQ(c)) * x0 ** i for i, c in enumerate(
                        cert['source_y_denominator_coefficients_low_to_high'])), F(0))
                    if not formula_den:
                        zero_y_formula.append([int(x0), int(y0)])
        pairs = []
        for x0, y0 in sources:
            Rz = PolynomialRing(F, 'z')
            z = Rz.gen()
            specialized = sum((F(int(term['integer_coefficient']))
                               * x0 ** term['x_C_exponent']
                               * y0 ** term['y_C_exponent']
                               * z ** term['x_E_exponent']
                               for term in resolvent['terms']), Rz.zero())
            for xe, _ in specialized.roots():
                square = xe ** 3 + 432
                if not square.is_square():
                    continue
                ys = [F(0)] if square == 0 else [square.sqrt(), -square.sqrt()]
                for ye in ys:
                    classification = inverse.evaluate_pair(
                        (int(x0), int(y0)), (int(xe), int(ye)), p,
                        resolvent, branch)
                    pairs.append({'C_point': [int(x0), int(y0)],
                                  'E_point': [int(xe), int(ye)],
                                  **classification})
        cell = {'prime': p, 'modular_eliminant_equals_field_poly_square': True,
                'field_poly_roots': sorted(all_field_roots),
                'source_points': sorted([[int(x0), int(y0)] for x0, y0 in sources]),
                'zero_source_y_formula_points': sorted(zero_y_formula),
                'rational_CE_pairs': len(pairs), 'pairs': pairs}
        cells.append(cell)
        print(json.dumps({'prime': p, 'field_poly_roots': len(all_field_roots),
                          'source_points': len(sources),
                          'zero_y_formula_points': len(zero_y_formula),
                          'rational_CE_pairs': len(pairs)}, sort_keys=True), flush=True)
    out = {'status': 'EXACT_DIRECT_DENOMINATOR_EXCEPTION_CLASSIFICATION',
           'protocol_sha256': sha256(pp.read_bytes()).hexdigest(),
           'exception_protocol_sha256': sha256(ep.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'cells': cells}
    (HERE / 'exception_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')


if __name__ == '__main__':
    main()
