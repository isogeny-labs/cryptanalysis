"""Independent finite-field polynomial replay at the two new gate exceptions."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import GF, PolynomialRing, QQ

HERE = Path(__file__).resolve().parent


def evaluate(coefficients, x, F):
    value = F(0)
    for raw in reversed(coefficients):
        value = value * x + F(QQ(raw))
    return value


def branch_value(terms, x, y, xe, F):
    return sum((F(int(term['integer_coefficient']))
                * x ** term['x_C_exponent']
                * y ** term['y_C_exponent']
                * xe ** term['x_E_exponent'] for term in terms), F(0))


def main():
    protocol_path = HERE / 'sage_replay_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_INDEPENDENT_SAGE_EXCEPTION_REPLAY'
    inputs = {}
    for name, (raw_path, digest) in protocol['inputs'].items():
        path = Path(raw_path)
        assert sha256(path.read_bytes()).hexdigest() == digest
        inputs[name] = json.loads(path.read_text())
    direct = inputs['exception_result']
    cert = inputs['field_certificate']
    frozen = json.loads((HERE / 'exception_protocol.json').read_text())
    resolvent_path = Path(frozen['inputs']['resolvent'][0])
    branch_path = Path(frozen['inputs']['branch_formula'][0])
    assert sha256(resolvent_path.read_bytes()).hexdigest() == frozen['inputs']['resolvent'][1]
    assert sha256(branch_path.read_bytes()).hexdigest() == frozen['inputs']['branch_formula'][1]
    terms = json.loads(resolvent_path.read_text())['terms']
    branch = json.loads(branch_path.read_text())
    cells = []
    for cell in direct['cells']:
        p = cell['prime']
        F = GF(p)
        Rx = PolynomialRing(F, 'x')
        field_poly = Rx([F(QQ(c)) for c in
                         cert['field_polynomial_coefficients_low_to_high']])
        source_points = []
        pairs = []
        for x, multiplicity in field_poly.roots():
            assert multiplicity >= 1
            denominator = evaluate(cert['source_y_denominator_coefficients_low_to_high'], x, F)
            assert denominator
            y = evaluate(cert['source_y_numerator_coefficients_low_to_high'], x, F) / denominator
            assert y * y + y == x ** 3 - 7
            source_points.append([int(x), int(y)])
            Rz = PolynomialRing(F, 'z')
            z = Rz.gen()
            specialized = Rz.zero()
            for term in terms:
                specialized += (F(int(term['integer_coefficient']))
                                * x ** term['x_C_exponent']
                                * y ** term['y_C_exponent']
                                * z ** term['x_E_exponent'])
            for xe, _ in specialized.roots():
                square = xe ** 3 + 432
                if not square.is_square():
                    continue
                ys = [F(0)] if square == 0 else [square.sqrt(), -square.sqrt()]
                for ye in ys:
                    assert ye * ye == square
                    numerator = branch_value(branch['numerator_terms'], x, y, xe, F)
                    branch_denominator = branch_value(branch['denominator_terms'], x, y, xe, F)
                    pairs.append({'C_point': [int(x), int(y)],
                                  'E_point': [int(xe), int(ye)],
                                  'branch_numerator': int(numerator),
                                  'branch_denominator': int(branch_denominator)})
        expected_sources = {tuple(row['C_point']) for row in cell['rows']}
        assert expected_sources.issubset({tuple(row) for row in source_points})
        expected_pairs = {(tuple(row['C_point']), tuple(row['E_point']))
                          for row in cell['rows']}
        actual_pairs = {(tuple(row['C_point']), tuple(row['E_point']))
                        for row in pairs}
        assert actual_pairs == expected_pairs
        assert len(source_points) == cell['C_points']
        assert all(row['branch_denominator'] == 0 for row in pairs)
        cells.append({'prime': p, 'source_points': source_points, 'pairs': pairs})
        print(json.dumps({'prime': p, 'source_points': len(source_points),
                          'pairs': len(pairs)}, sort_keys=True), flush=True)
    output = {'status': 'PASS_INDEPENDENT_SAGE_NEW_EXCEPTION_REPLAY',
              'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
              'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
              'cells': cells}
    (HERE / 'sage_replay.json').write_text(json.dumps(output, sort_keys=True, indent=2) + '\n')


if __name__ == '__main__':
    main()
