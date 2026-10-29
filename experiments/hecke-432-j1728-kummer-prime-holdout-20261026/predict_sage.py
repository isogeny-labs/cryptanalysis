"""Predict unseen-prime quartic splitting from frozen Kummer square classes."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import NumberField, PolynomialRing, QQ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def lift_vector(values, alpha, K):
    return sum((K(QQ(value)) * alpha ** i for i, value in enumerate(values)), K(0))


def lift_relative(values, alpha, s, K, L):
    return sum((L(lift_vector(vector, alpha, K)) * s ** i
                for i, vector in enumerate(values)), L(0))


def save(rows, protocol_path, status):
    out = {'status': status, 'rows': rows,
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest()}
    (HERE / 'predictions.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    paths = {name: ROOT / rel for name, rel in protocol['input_paths'].items()}
    for name, path in paths.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    cert = json.loads(paths['factor_certificate'].read_text())
    kummer = json.loads(paths['kummer_result'].read_text())
    support = json.loads(paths['relative_discriminant_support'].read_text())
    assert kummer['status'] == 'PASS_KUMMER_SQUARE_CLASS_TEST'
    assert support['fixed_integer_in_left_discriminant_ideal'] == 96
    K = NumberField(PolynomialRing(QQ, 'x')(
        [QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    alpha = K.gen()
    L = K.extension(PolynomialRing(K, 't').gen() ** 2 - 2, 's')
    s = L.gen()
    radicands = {row['side']: [lift_relative(v, alpha, s, K, L)
                                 for v in row['radicands']]
                 for row in kummer['rows']}
    assert set(radicands) == set(protocol['target_sides'])
    ideals = {side: [L.ideal(value) for value in values]
              for side, values in radicands.items()}
    rows = []
    for p in protocol['rational_primes']:
        assert 96 % p != 0
        places = L.primes_above(p)
        assert sum(int(P.residue_class_degree()) for P in places) == 36
        for i, P in enumerate(places):
            assert int(P.absolute_ramification_index()) == 1
            F = P.residue_field()
            q = int(F.cardinality())
            f_base = int(P.residue_class_degree())
            assert q == p ** f_base
            for side in protocol['target_sides']:
                local = []
                for D, ideal in zip(radicands[side], ideals[side]):
                    v = int(ideal.valuation(P))
                    if v % 2:
                        local.append({'valuation': v, 'quadratic_character': None,
                                      'unit_residue': None, 'status': 'ODD_VALUATION'})
                        continue
                    unit = F(D / (L(p) ** v))
                    assert unit != 0
                    chi = unit ** ((q - 1) // 2)
                    assert chi in (F(1), F(-1))
                    local.append({'valuation': v,
                                  'quadratic_character': 1 if chi == F(1) else -1,
                                  'unit_residue': str(unit), 'status': 'PASS_UNIT_CHARACTER'})
                if all(item['status'] == 'PASS_UNIT_CHARACTER' for item in local):
                    characters = [item['quadratic_character'] for item in local]
                    assert characters[2] == characters[0] * characters[1]
                    degrees = [1, 1, 1, 1] if characters[:2] == [1, 1] else [2, 2]
                    status = 'PREDICTED'
                else:
                    degrees, status = None, 'ODD_VALUATION'
                rows.append({'prime': p, 'base_place_index': i, 'side': side,
                             'ideal_generators': [str(x) for x in P.gens()],
                             'base_residue_degree': f_base,
                             'radicand_local_data': local,
                             'predicted_relative_degrees': degrees,
                             'status': status})
        save(rows, protocol_path, 'PARTIAL_UNSEEN_PRIME_KUMMER_PREDICTIONS')
        print(json.dumps({'prime': p, 'rows': sum(row['prime'] == p for row in rows)},
                         sort_keys=True), flush=True)
    save(rows, protocol_path, 'PASS_UNSEEN_PRIME_KUMMER_PREDICTIONS')
    print(json.dumps({'status': 'PASS_UNSEEN_PRIME_KUMMER_PREDICTIONS',
                      'rows': len(rows),
                      'unpredicted': sum(row['status'] != 'PREDICTED' for row in rows)},
                     sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
