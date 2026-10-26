"""Independent integer-polynomial and SymPy replay of the source fiber."""
import json
import os
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

os.environ.setdefault('SYMPY_GROUND_TYPES', 'python')
from sympy import Poly, sqrt_mod, symbols  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def mod_q(raw, p):
    q = Fraction(raw)
    return q.numerator * pow(q.denominator, -1, p) % p


def trim(a):
    while len(a) > 1 and a[-1] == 0:
        a.pop()
    return a


def add(a, b, p):
    return trim([((a[i] if i < len(a) else 0) +
                  (b[i] if i < len(b) else 0)) % p
                 for i in range(max(len(a), len(b)))])


def scale(a, c, p):
    return trim([x * c % p for x in a])


def mul(a, b, p):
    out = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] = (out[i + j] + x * y) % p
    return trim(out)


def evaluate_terms(terms, x, y, p):
    return sum(mod_q(t['coefficient'], p) * pow(x, t['x_power'], p)
               * pow(y, t['y_power'], p) for t in terms) % p


def poly_terms(terms, p):
    assert max(t['y_power'] for t in terms) <= 1
    parts = [[0], [0]]
    for term in terms:
        target = parts[term['y_power']]
        i = term['x_power']
        target.extend([0] * max(0, i + 1 - len(target)))
        target[i] = (target[i] + mod_q(term['coefficient'], p)) % p
    return [trim(part) for part in parts]


def roots(coefficients, p):
    z = symbols('z')
    poly = Poly(sum(int(c) * z ** i for i, c in enumerate(coefficients)), z,
                modulus=p)
    return sorted(int(root) % p for root in poly.ground_roots())


def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    direct_path = HERE / 'exception_result.json'
    direct = json.loads(direct_path.read_text())
    field_path = ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json'
    coordinate_path = ROOT / 'experiments/hecke-27-coordinate-bridge-20261025/coordinate_map.json'
    resolvent_path = ROOT / 'experiments/hecke-432-relative-resolvent-20261025/relative_resolvent.json'
    for name, path in [('field_certificate', field_path),
                       ('coordinate_map', coordinate_path),
                       ('resolvent', resolvent_path)]:
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    field = json.loads(field_path.read_text())
    coordinate = json.loads(coordinate_path.read_text())['source_j']
    resolvent = json.loads(resolvent_path.read_text())['terms']
    rows = []
    for cell in direct['cells']:
        p = cell['prime']
        num_a, num_b = poly_terms(coordinate['numerator'], p)
        den_a, den_b = poly_terms(coordinate['denominator'], p)
        A = add(num_a, scale(den_a, 1728, p), p)
        B = add(num_b, scale(den_b, 1728, p), p)
        # H=A+B*y and y^2+y=x^3-7; clear B^2 after y=-A/B.
        resultant = add(add(mul(A, A, p), scale(mul(A, B, p), -1, p), p),
                        mul(mul(B, B, p), [7, 0, 0, -1], p), p)
        f = [mod_q(c, p) for c in field['field_polynomial_coefficients_low_to_high']]
        square = mul(f, f, p)
        assert len(resultant) == len(square) == 37
        factor = resultant[-1] * pow(square[-1], -1, p) % p
        assert resultant == scale(square, factor, p)
        field_roots = roots(f, p)
        assert field_roots == cell['field_poly_roots']
        sources = []
        pairs = []
        resolvent_roots = []
        root_diagnostics = []
        for x in field_roots:
            discriminant = (4 * pow(x, 3, p) - 27) % p
            y_formula_denominator = sum(
                mod_q(c, p) * pow(x, i, p)
                for i, c in enumerate(field['source_y_denominator_coefficients_low_to_high'])) % p
            y_formula_numerator = sum(
                mod_q(c, p) * pow(x, i, p)
                for i, c in enumerate(field['source_y_numerator_coefficients_low_to_high'])) % p
            root_diagnostics.append({
                'x_C': x, 'source_y_formula_numerator': y_formula_numerator,
                'source_y_formula_denominator': y_formula_denominator,
                'curve_discriminant': discriminant,
                'curve_discriminant_legendre': pow(discriminant, (p - 1) // 2, p),
            })
            for root in sqrt_mod(discriminant, p, all_roots=True):
                y = ((int(root) - 1) * pow(2, -1, p)) % p
                assert (y * y + y - x ** 3 + 7) % p == 0
                numerator = evaluate_terms(coordinate['numerator'], x, y, p)
                denominator = evaluate_terms(coordinate['denominator'], x, y, p)
                if denominator and (numerator + 1728 * denominator) % p == 0:
                    sources.append([x, y])
                    coefficients = [0] * 13
                    for term in resolvent:
                        i = term['x_E_exponent']
                        coefficients[i] = (coefficients[i]
                            + int(term['integer_coefficient'])
                            * pow(x, term['x_C_exponent'], p)
                            * pow(y, term['y_C_exponent'], p)) % p
                    for xe in roots(coefficients, p):
                        resolvent_roots.append({'C_point': [x, y], 'x_E': xe})
                        for ye in sqrt_mod((xe ** 3 + 432) % p, p, all_roots=True):
                            pairs.append({'C_point': [x, y],
                                          'E_point': [xe, int(ye)]})
        assert sorted(sources) == cell['source_points']
        assert sorted(pairs, key=str) == sorted(
            ({'C_point': r['C_point'], 'E_point': r['E_point']}
             for r in cell['pairs']), key=str)
        rows.append({'prime': p, 'source_resultant_scalar_mod_p': factor,
                     'field_poly_roots': field_roots,
                     'root_diagnostics': root_diagnostics,
                     'source_points': sources,
                     'resolvent_roots': resolvent_roots,
                     'rational_CE_pairs': len(pairs)})
    out = {'status': 'PASS_INDEPENDENT_SOURCE_FIBER_AND_E_REPLAY',
           'direct_result_sha256': sha256(direct_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'rows': rows}
    (HERE / 'exception_audit.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'rows': rows}, sort_keys=True))


if __name__ == '__main__':
    main()
