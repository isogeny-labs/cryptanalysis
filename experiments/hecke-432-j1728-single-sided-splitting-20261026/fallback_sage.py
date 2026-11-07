"""Resolve repeated left reductions using left Kummer unit characters."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import NumberField, PolynomialRing, QQ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def lift_base(v, alpha, K):
    return sum((K(QQ(c)) * alpha ** i for i, c in enumerate(v)), K(0))


def lift_relative(v, alpha, s, K, L):
    return sum((L(lift_base(w, alpha, K)) * s ** i for i, w in enumerate(v)), L(0))


def main():
    fallback_path = HERE / 'fallback_protocol.json'
    fallback = json.loads(fallback_path.read_text())
    first_path = HERE / 'predictions.json'
    assert sha256(first_path.read_bytes()).hexdigest() == fallback['first_predictions_sha256']
    protocol_path = HERE / 'protocol.json'
    assert sha256(protocol_path.read_bytes()).hexdigest() == fallback['protocol_sha256']
    protocol = json.loads(protocol_path.read_text())
    source_paths = {name: ROOT / rel for name, rel in protocol['input_paths'].items()}
    for name, path in source_paths.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    kp = ROOT / fallback['kummer_result_path']
    assert sha256(kp.read_bytes()).hexdigest() == fallback['kummer_result_sha256']
    cert = json.loads(source_paths['factor_certificate'].read_text())
    kummer = json.loads(kp.read_text())
    assert kummer['status'] == 'PASS_KUMMER_SQUARE_CLASS_TEST'
    left = next(r for r in kummer['rows'] if r['side'] == 'left')
    K = NumberField(PolynomialRing(QQ, 'x')(
        [QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    alpha = K.gen()
    L = K.extension(PolynomialRing(K, 't').gen() ** 2 - 2, 's')
    s = L.gen()
    radicands = [lift_relative(v, alpha, s, K, L) for v in left['radicands']]
    ideals = [L.ideal(v) for v in radicands]
    rows = []
    for p, i, j in fallback['unresolved_left_places']:
        P = L.primes_above(p)[i]
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
            local.append({'valuation': valuation,
                          'character': 1 if chi == F(1) else -1,
                          'unit_residue': str(unit), 'status': 'PASS_UNIT_CHARACTER'})
        if all(x['status'] == 'PASS_UNIT_CHARACTER' for x in local):
            chars = [x['character'] for x in local]
            assert chars[2] == chars[0] * chars[1]
            degrees = [1, 1, 1, 1] if chars[:2] == [1, 1] else [2, 2]
            status = 'PREDICTED_BY_LEFT_KUMMER'
        else:
            degrees = None
            status = 'UNRESOLVED_LEFT_KUMMER'
        rows.append({'prime': p, 'left_place_index': i, 'right_place_index': j,
                     'base_residue_degree': int(P.residue_class_degree()),
                     'left_local_data': local,
                     'predicted_right_relative_degrees': degrees, 'status': status})
        print(json.dumps({'prime': p, 'left_place_index': i, 'status': status},
                         sort_keys=True), flush=True)
    out = {'status': 'PASS_LEFT_KUMMER_FALLBACK' if all(
               r['status'] == 'PREDICTED_BY_LEFT_KUMMER' for r in rows)
           else 'PARTIAL_LEFT_KUMMER_FALLBACK',
           'fallback_protocol_sha256': sha256(fallback_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'rows': rows}
    (HERE / 'fallback_predictions.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'rows': len(rows)}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
