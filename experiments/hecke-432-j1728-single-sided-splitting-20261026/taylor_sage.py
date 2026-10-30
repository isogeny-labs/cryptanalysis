"""Resolve right quartic double-linear clusters by normalized Taylor data."""
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


def save(rows, protocol_path, status):
    out = {'status': status, 'rows': rows,
           'taylor_protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest()}
    (HERE / 'taylor_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')


def main():
    control_path = HERE / 'taylor_protocol.json'
    control = json.loads(control_path.read_text())
    assert control['status'] == 'FROZEN_BEFORE_RIGHT_TAYLOR_REPLAY'
    assert sha256((HERE / 'protocol.json').read_bytes()).hexdigest() == control['protocol_sha256']
    obs_path = HERE / 'observations.json'
    assert sha256(obs_path.read_bytes()).hexdigest() == control['observation_sha256']
    observations = json.loads(obs_path.read_text())
    obs_rows = {(r['prime'], r['right_place_index']): r for r in observations['rows']}
    protocol = json.loads((HERE / 'protocol.json').read_text())
    cert_path = ROOT / protocol['input_paths']['factor_certificate']
    split_path = ROOT / protocol['input_paths']['split_certificate']
    assert sha256(cert_path.read_bytes()).hexdigest() == control['factor_certificate_sha256']
    assert sha256(split_path.read_bytes()).hexdigest() == control['split_certificate_sha256']
    cert = json.loads(cert_path.read_text())
    split = json.loads(split_path.read_text())
    K = NumberField(PolynomialRing(QQ, 'x')(
        [QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    alpha = K.gen()
    L = K.extension(PolynomialRing(K, 't').gen() ** 2 - 2, 's')
    s = L.gen()
    quartic = next(r for r in split['records'] if r['base_degree'] == 8)['factors'][1]
    Lz = PolynomialRing(L, 'z')
    g = Lz([relative_element(v, alpha, s, K, L)
            for v in quartic['coefficients_low_to_high']])
    assert g.degree() == 4 and g.is_monic()
    rows = []
    for site in control['sites']:
        p, j = site['prime'], site['right_place_index']
        P = L.primes_above(p)[j]
        assert int(P.absolute_ramification_index()) == 1
        assert [str(v) for v in P.gens()] == site['right_ideal_generators']
        assert int(P.residue_class_degree()) == site['base_residue_degree']
        source = obs_rows[p, j]
        assert source['status'] == 'REPEATED_RIGHT_REDUCTION'
        F = P.residue_field()
        Fz = PolynomialRing(F, 'z')
        reduced = Fz([F(c) for c in g.list()])
        factors = list(reduced.factor())
        assert sorted((int(h.degree()), int(e)) for h, e in factors) == \
            [(1, 1), (1, 1), (1, 2)]
        double_h = next(h for h, e in factors if e == 2)
        root_residue = -double_h[0] / double_h[1]
        root_lift = L(F.lift(root_residue))
        assert F(root_lift) == root_residue
        g0 = g(root_lift)
        g1 = g.derivative()(root_lift)
        g2 = g.derivative().derivative()(root_lift)
        v0 = int(L.ideal(g0).valuation(P))
        v1 = int(L.ideal(g1).valuation(P))
        assert v0 >= 2 and v1 >= 1
        A = F(g2 / 2)
        B = F(g1 / p)
        C = F(g0 / (p * p))
        assert A != 0
        lifted = g(root_lift + L(p) * Lz.gen()) / (p * p)
        reduced_taylor = Fz([F(c) for c in lifted.list()])
        assert reduced_taylor == Fz([C, B, A])
        delta = B * B - 4 * A * C
        assert delta != 0
        q = int(F.cardinality())
        assert q == p ** int(P.residue_class_degree())
        chi = delta ** ((q - 1) // 2)
        assert chi in (F(1), F(-1))
        square = chi == F(1)
        degrees = [1, 1, 1, 1] if square else [1, 1, 2]
        rows.append({'prime': p, 'right_place_index': j,
                     'right_ideal_generators': site['right_ideal_generators'],
                     'base_residue_degree': int(P.residue_class_degree()),
                     'double_residue_root': str(root_residue),
                     'root_lift_sha256': sha256(str(root_lift).encode()).hexdigest(),
                     'g_value_valuation': v0, 'g_derivative_valuation': v1,
                     'normalized_taylor_coefficients': [str(A), str(B), str(C)],
                     'normalized_polynomial_identity_checked': True,
                     'normalized_discriminant': str(delta),
                     'discriminant_character': 1 if square else -1,
                     'observed_right_relative_degrees': degrees,
                     'status': 'TAYLOR_CLASSIFIED'})
        save(rows, control_path, 'PARTIAL_RIGHT_TAYLOR_CLASSIFICATION')
        print(json.dumps({'prime': p, 'right_place_index': j,
                          'discriminant_character': 1 if square else -1,
                          'relative_degrees': degrees}, sort_keys=True), flush=True)
    save(rows, control_path, 'PASS_RIGHT_TAYLOR_CLASSIFICATION')
    print(json.dumps({'status': 'PASS_RIGHT_TAYLOR_CLASSIFICATION',
                      'rows': len(rows)}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
