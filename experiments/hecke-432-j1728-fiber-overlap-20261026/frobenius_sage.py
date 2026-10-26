"""Factor the pinned degree-18 source polynomial at six fixed primes."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import GF, PolynomialRing, QQ, ZZ, prod

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'holdout_result': HERE / 'holdout_result.json',
    'multiplicity_result': HERE / 'multiplicity_result.json',
    'factor_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'prime_result': ROOT / 'experiments/hecke-432-j1728-octic-factor-search-20261026/prime_result.json',
    'control_result': ROOT / 'experiments/hecke-432-j1728-octic-factor-search-20261026/control_result.json',
    'large_prime_result': ROOT / 'experiments/hecke-432-j1728-norm-power-20261026/large_prime_result.json',
}


def main():
    path = HERE / 'frobenius_protocol.json'
    protocol = json.loads(path.read_text())
    for name, source in INPUTS.items():
        assert sha256(source.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    field = json.loads(INPUTS['factor_certificate'].read_text())
    rows = []
    for raw in protocol['primes']:
        p = ZZ(raw)
        assert p.is_prime(proof=True)
        F = GF(p)
        Rx = PolynomialRing(F, 'x')
        f = Rx([F(QQ(c)) for c in field['field_polynomial_coefficients_low_to_high']])
        assert f.degree() == 18
        factorization = f.factor()
        assert factorization.unit() * prod(q ** m for q, m in factorization) == f
        roots = [str(int(x)) for x, _ in f.roots()]
        pieces = [{'degree': int(q.degree()), 'multiplicity': int(m),
                   'coefficients_low_to_high': [str(int(c)) for c in q.list()]}
                  for q, m in factorization]
        assert sum(piece['degree'] * piece['multiplicity'] for piece in pieces) == 18
        rows.append({'prime': str(p), 'prime_proved': True,
                     'leading_unit': str(int(factorization.unit())),
                     'factor_degrees_with_multiplicity':
                         [[piece['degree'], piece['multiplicity']] for piece in pieces],
                     'rational_roots': roots, 'factors': pieces})
    out = {'status': 'PASS_SIX_PRIME_SOURCE_FROBENIUS_FACTORIZATION',
           'protocol_sha256': sha256(path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'rows': rows}
    (HERE / 'frobenius_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'],
                      'summary': [{'prime': row['prime'],
                                   'degrees': row['factor_degrees_with_multiplicity'],
                                   'rational_roots': len(row['rational_roots'])}
                                  for row in rows]}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
