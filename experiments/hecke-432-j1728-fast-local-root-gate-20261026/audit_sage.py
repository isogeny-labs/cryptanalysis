"""Independent Sage finite-field source and resolvent root replay."""
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
}


def expression(terms, x, y, F):
    return sum((F(QQ(term['coefficient']))
                * x ** term['x_power'] * y ** term['y_power']
                for term in terms), F(0))


def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    ap = HERE / 'audit_protocol.json'
    audit_protocol = json.loads(ap.read_text())
    rp = HERE / 'result.json'
    assert sha256(rp.read_bytes()).hexdigest() == audit_protocol['result_sha256']
    result = json.loads(rp.read_text())
    for name, path in INPUTS.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    field = json.loads(INPUTS['field_certificate'].read_text())
    coordinate = json.loads(INPUTS['coordinate_map'].read_text())['source_j']
    terms = json.loads(INPUTS['resolvent'].read_text())['terms']
    audited = []
    for cell in result['cells']:
        p = cell['prime']
        F = GF(p)
        Rx = PolynomialRing(F, 'x')
        f = Rx([F(QQ(c)) for c in field['field_polynomial_coefficients_low_to_high']])
        source_roots = sorted(int(x) for x, _ in f.roots())
        assert source_roots == cell['field_poly_rational_x_roots']
        source_points = []
        undefined = []
        Rz = PolynomialRing(F, 'z')
        z = Rz.gen()
        fiber_rows = []
        for raw_x in source_roots:
            x = F(raw_x)
            Fy = PolynomialRing(F, 'y')
            yvar = Fy.gen()
            for y, _ in (yvar ** 2 + yvar - x ** 3 + 7).roots():
                numerator = expression(coordinate['numerator'], x, y, F)
                denominator = expression(coordinate['denominator'], x, y, F)
                if not denominator:
                    undefined.append([int(x), int(y)])
                    continue
                if numerator + 1728 * denominator:
                    continue
                source_points.append([int(x), int(y)])
                R = sum((F(int(term['integer_coefficient']))
                         * x ** term['x_C_exponent']
                         * y ** term['y_C_exponent']
                         * z ** term['x_E_exponent'] for term in terms), Rz.zero())
                roots = [xe for xe, _ in R.roots()]
                plus = [xe for xe in roots if xe ** 3 + 432 and (xe ** 3 + 432).is_square()]
                zero = [xe for xe in roots if xe ** 3 + 432 == 0]
                fiber_rows.append({
                    'C_point': [int(x), int(y)], 'resolvent_degree': int(R.degree()),
                    'rational_x_E_roots': len(roots),
                    'nonzero_square_x_E_roots': len(plus),
                    'zero_square_x_E_roots': len(zero),
                    'rational_CE_pairs': 2 * len(plus) + len(zero),
                })
        assert sorted(source_points) == cell['source_points']
        assert sorted(undefined) == cell['undefined_source_j_points']
        expected = [{key: row[key] for key in (
            'C_point', 'resolvent_degree', 'rational_x_E_roots',
            'nonzero_square_x_E_roots', 'zero_square_x_E_roots',
            'rational_CE_pairs')} for row in cell['fibers']]
        assert sorted(fiber_rows, key=lambda row: row['C_point']) == sorted(
            expected, key=lambda row: row['C_point'])
        audited.append({'prime': p, 'source_points': len(source_points),
                        'rational_CE_pairs': sum(row['rational_CE_pairs']
                                                 for row in fiber_rows)})
        print(json.dumps(audited[-1], sort_keys=True), flush=True)
    out = {'status': 'PASS_INDEPENDENT_SAGE_FAST_LOCAL_GATE_REPLAY',
           'audit_protocol_sha256': sha256(ap.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'audited_cells': audited}
    (HERE / 'audit.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')


if __name__ == '__main__':
    main()
