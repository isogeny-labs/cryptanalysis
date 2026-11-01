"""Check repeated right reductions with right Kummer square classes."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import NumberField, PolynomialRing, QQ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def base_element(v, alpha, K):
    return sum((K(QQ(c)) * alpha ** i for i, c in enumerate(v)), K(0))


def relative_element(v, alpha, s, K, L):
    return sum((L(base_element(w, alpha, K)) * s ** i for i, w in enumerate(v)), L(0))


def main():
    control_path = HERE / 'right_kummer_protocol.json'
    control = json.loads(control_path.read_text())
    assert control['status'] == 'FROZEN_BEFORE_RIGHT_KUMMER_CHECK'
    for name, key in [('observations.json', 'observation_sha256'),
                      ('transferred_predictions.json', 'transferred_predictions_sha256'),
                      ('protocol.json', 'protocol_sha256')]:
        assert sha256((HERE / name).read_bytes()).hexdigest() == control[key]
    kp = ROOT / control['kummer_result_path']
    assert sha256(kp.read_bytes()).hexdigest() == control['kummer_result_sha256']
    protocol = json.loads((HERE / 'protocol.json').read_text())
    cert_path = ROOT / protocol['input_paths']['factor_certificate']
    assert sha256(cert_path.read_bytes()).hexdigest() == protocol['input_sha256']['factor_certificate']
    cert = json.loads(cert_path.read_text())
    kummer = json.loads(kp.read_text())
    assert kummer['status'] == 'PASS_KUMMER_SQUARE_CLASS_TEST'
    right = next(r for r in kummer['rows'] if r['side'] == 'right')
    K = NumberField(PolynomialRing(QQ, 'x')(
        [QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    alpha = K.gen()
    L = K.extension(PolynomialRing(K, 't').gen() ** 2 - 2, 's')
    s = L.gen()
    radicands = [relative_element(v, alpha, s, K, L) for v in right['radicands']]
    ideals = [L.ideal(v) for v in radicands]
    rows = []
    for p, j in control['unresolved_right_places']:
        P = L.primes_above(p)[j]
        F = P.residue_field()
        q = int(F.cardinality())
        local = []
        for D, ideal in zip(radicands, ideals):
            valuation = int(ideal.valuation(P))
            if valuation % 2:
                local.append({'valuation': valuation, 'character': None,
                              'status': 'ODD_VALUATION'})
                continue
            unit = F(D / (L(p) ** valuation))
            if unit == 0:
                local.append({'valuation': valuation, 'character': None,
                              'status': 'ZERO_UNIT_RESIDUE'})
                continue
            chi = unit ** ((q - 1) // 2)
            assert chi in (F(1), F(-1))
            local.append({'valuation': valuation, 'character': 1 if chi == F(1) else -1,
                          'unit_residue': str(unit), 'status': 'PASS_UNIT_CHARACTER'})
        if all(x['status'] == 'PASS_UNIT_CHARACTER' for x in local):
            chars = [x['character'] for x in local]
            assert chars[2] == chars[0] * chars[1]
            degrees = [1, 1, 1, 1] if chars[:2] == [1, 1] else [2, 2]
            status = 'RIGHT_KUMMER_CLASSIFIED'
        else:
            degrees, status = None, 'UNRESOLVED_RIGHT_KUMMER'
        rows.append({'prime': p, 'right_place_index': j,
                     'right_ideal_generators': [str(v) for v in P.gens()],
                     'base_residue_degree': int(P.residue_class_degree()),
                     'right_local_data': local, 'observed_right_relative_degrees': degrees,
                     'status': status})
        print(json.dumps({'prime': p, 'right_place_index': j, 'status': status},
                         sort_keys=True), flush=True)
    out = {'status': 'PASS_RIGHT_KUMMER_CHECK' if all(
               r['status'] == 'RIGHT_KUMMER_CLASSIFIED' for r in rows)
           else 'PARTIAL_RIGHT_KUMMER_CHECK',
           'right_kummer_protocol_sha256': sha256(control_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'rows': rows}
    (HERE / 'right_kummer_observations.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'rows': len(rows)}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
