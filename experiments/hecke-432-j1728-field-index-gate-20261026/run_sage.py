"""Compute defining-polynomial and maximal-order discriminants exactly."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import GF, NumberField, PolynomialRing, QQ, ZZ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'factor_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'root_support_result': ROOT / 'experiments/hecke-432-j1728-root-prime-support-20261026/result.json',
}


def valuation(n, p):
    n = abs(ZZ(n))
    v = 0
    while n and n % p == 0:
        n //= p
        v += 1
    return v


def save(path, data):
    path.write_text(json.dumps(data, sort_keys=True, indent=2) + '\n')


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    for name, path in INPUTS.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    cert = json.loads(INPUTS['factor_certificate'].read_text())
    root = json.loads(INPUTS['root_support_result'].read_text())
    R = PolynomialRing(QQ, 'x')
    f = R([QQ(x) for x in cert['field_polynomial_coefficients_low_to_high']])
    assert f.degree() == 18 and f.is_monic() and f.is_irreducible()
    polynomial_disc = ZZ(f.discriminant())
    assert polynomial_disc != 0
    primes = [ZZ(p) for p in protocol['local_primes']]
    support = set()
    for row in root['rows']:
        support.update(p for p, _ in row['complete_common_gcd_factorization'])
    assert support == set(primes)
    local = []
    for p in primes:
        fp = f.change_ring(GF(p))
        local.append({'prime': int(p), 'polynomial_discriminant_valuation': valuation(polynomial_disc, p),
                      'mod_p_squarefree': bool(fp.is_squarefree()),
                      'mod_p_factor_degrees': [[int(q.degree()), int(e)] for q, e in fp.factor()]})
    partial = {'status': 'POLYNOMIAL_DISCRIMINANT_COMPLETE',
               'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
               'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
               'field_degree': 18,
               'polynomial_discriminant': str(polynomial_disc),
               'polynomial_discriminant_digits': len(str(abs(polynomial_disc))),
               'local': local}
    save(HERE / 'polynomial_result.json', partial)
    print(json.dumps({'status': partial['status'], 'digits': partial['polynomial_discriminant_digits'],
                      'valuations': [[row['prime'], row['polynomial_discriminant_valuation']] for row in local]},
                     sort_keys=True), flush=True)
    K = NumberField(f, 'alpha')
    field_disc = ZZ(K.discriminant())
    ratio = ZZ(polynomial_disc // field_disc)
    assert field_disc and polynomial_disc == field_disc * ratio and ratio > 0
    index, exact = ratio.sqrtrem()
    assert exact == 0
    for row in local:
        p = ZZ(row['prime'])
        vd = valuation(field_disc, p)
        vi = valuation(index, p)
        assert row['polynomial_discriminant_valuation'] == vd + 2 * vi
        row['field_discriminant_valuation'] = vd
        row['order_index_valuation'] = vi
    result = {**partial, 'status': 'PASS_FIELD_INDEX_DISCRIMINANT_IDENTITY',
              'field_discriminant': str(field_disc), 'order_index': str(index),
              'index_identity': True}
    save(HERE / 'result.json', result)
    print(json.dumps({'status': result['status'], 'index_digits': len(str(index)),
                      'local': [[r['prime'], r['field_discriminant_valuation'], r['order_index_valuation']]
                                for r in local]}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
