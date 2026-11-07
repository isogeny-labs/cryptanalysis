"""Independent checked-Sage replay of cubic/quadratic gcd and branch identity."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

from sage.all import GF, PolynomialRing, ZZ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'result': HERE / 'result.json',
    'multiplicity_result': ROOT / 'experiments/hecke-432-j1728-fiber-overlap-20261026/multiplicity_result.json',
    'relative_b_resolvent': ROOT / 'experiments/hecke-432-b-coordinate-resolvent-20261025/relative_b_resolvent.json',
    'branch_formula': ROOT / 'experiments/hecke-432-b-coordinate-resolvent-20261025/branch_formula.json',
}


def main():
    path = HERE / 'audit_protocol.json'
    protocol = json.loads(path.read_text())
    for name, source in INPUTS.items():
        assert sha256(source.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    saved = json.loads(INPUTS['result'].read_text())
    relative = json.loads(INPUTS['relative_b_resolvent'].read_text())
    branch = json.loads(INPUTS['branch_formula'].read_text())
    assert branch['source_sha256'] == sha256(INPUTS['relative_b_resolvent'].read_bytes()).hexdigest()
    rows = []
    for idx, field in enumerate(saved['results']):
        p = ZZ(field['prime'])
        assert p.is_prime(proof=True)
        Fp = GF(p)
        RT = PolynomialRing(Fp, 'T')
        T = RT.gen()
        histogram = Counter()
        quadratic_rational_counts = []
        checked = 0
        for root in field['rows']:
            x, y = map(lambda v: Fp(int(v)), root['C_point'])
            z = Fp(int(root['x_E']))
            PB = sum((Fp(int(term['integer_coefficient']))
                      * x ** term['x_C_exponent']
                      * y ** term['y_C_exponent']
                      * T ** term['x_B_exponent']
                      for term in relative['terms']), RT.zero())
            F = T ** 3 - z * T ** 2 - 64
            R = PB % F
            a, b, c = R[2], R[1], R[0]
            D = b * (a * z + b) - a * c
            N = 64 * a * a - c * (a * z + b)
            assert D * T - N == a * (a * F - T * R) + (a * z + b) * R
            assert bool(D == 0 and N == 0) == root['branch_values_zero']
            G = F.gcd(R).monic()
            assert G.degree() == root['common_B_gcd_degree']
            assert [str(int(v)) for v in G.list()] == root['gcd_coefficients_low_to_high']
            assert G.gcd(G.derivative()).degree() == 0
            if G.degree() == 2:
                rational_count = len(G.roots())
                quadratic_rational_counts.append(rational_count)
                assert rational_count == protocol['audit_targets'][
                    'quadratic_rational_root_counts'][idx]
            histogram[int(G.degree())] += 1
            checked += 1
        assert {str(k): v for k, v in histogram.items()} == protocol[
            'audit_targets']['gcd_degrees'][idx]
        rows.append({'prime': str(p), 'roots_checked': checked,
                     'gcd_degree_histogram': dict(sorted(histogram.items())),
                     'quadratic_rational_B_root_counts': quadratic_rational_counts})
    assert len(rows[-1]['quadratic_rational_B_root_counts']) == protocol[
        'audit_targets']['quadratic_irreducible_count_last_prime']
    out = {'status': 'PASS_INDEPENDENT_SAGE_CUBIC_GCD_AND_BRANCH_IDENTITY_AUDIT',
           'protocol_sha256': sha256(path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'rows': rows}
    (HERE / 'audit_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
