"""Independent polynomial-product and Frobenius-gcd splitting audit."""
import json
import runpy
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'frobenius_result': HERE / 'frobenius_result.json',
    'factor_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'fast_gate_source': ROOT / 'experiments/hecke-432-j1728-fast-local-root-gate-20261026/run.py',
}


def main():
    path = HERE / 'frobenius_audit_protocol.json'
    protocol = json.loads(path.read_text())
    for name, source in INPUTS.items():
        assert sha256(source.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    registered = json.loads(INPUTS['frobenius_result'].read_text())
    field = json.loads(INPUTS['factor_certificate'].read_text())
    gate = runpy.run_path(str(INPUTS['fast_gate_source']))
    rows = []
    for row in registered['rows']:
        p = int(row['prime'])
        arithmetic = gate['PolynomialArithmetic'](p)
        f = arithmetic.normal([gate['mod_fraction'](c, p)
                               for c in field['field_polynomial_coefficients_low_to_high']])
        product = [int(row['leading_unit']) % p]
        for piece in row['factors']:
            q = arithmetic.normal([int(c) for c in piece['coefficients_low_to_high']])
            assert len(q) - 1 == piece['degree']
            for _ in range(piece['multiplicity']):
                product = arithmetic.mul(product, q)
        assert product == f and len(f) - 1 == 18
        derivative = [(i * f[i]) % p for i in range(1, len(f))]
        assert len(arithmetic.gcd(f, derivative)) - 1 == 0
        gcd_degrees = []
        for extension_degree in (1, 2, 3):
            xp = arithmetic.powmod([0, 1], p ** extension_degree, f)
            gcd_degrees.append(len(arithmetic.gcd(f, arithmetic.sub(xp, [0, 1]))) - 1)
        assert gcd_degrees[0] == len(row['rational_roots'])
        rows.append({'prime': str(p), 'gcd_degrees_for_extensions_1_2_3': gcd_degrees,
                     'factor_product_exact': True,
                     'source_squarefree': True,
                     'polynomial_multiplications':
                         arithmetic.counts['polynomial_multiplications']})
    assert [r['gcd_degrees_for_extensions_1_2_3'] for r in rows] == [
        [18, 18, 18], [18, 18, 18], [18, 18, 18],
        [2, 18, 2], [0, 0, 18], [0, 0, 18]]
    out = {'status': 'PASS_INDEPENDENT_SIX_PRIME_FROBENIUS_GCD_AUDIT',
           'protocol_sha256': sha256(path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'rows': rows}
    (HERE / 'frobenius_audit_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'rows': rows}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
