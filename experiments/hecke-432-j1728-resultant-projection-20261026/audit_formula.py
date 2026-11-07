"""Independent modular reduction and eight-term resultant-formula audit."""
import json
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'result': HERE / 'result.json',
    'relative_b_resolvent': ROOT / 'experiments/hecke-432-b-coordinate-resolvent-20261025/relative_b_resolvent.json',
    'relative_xe_resolvent': ROOT / 'experiments/hecke-432-relative-resolvent-20261025/relative_resolvent.json',
    'multiplicity_result': ROOT / 'experiments/hecke-432-j1728-fiber-overlap-20261026/multiplicity_result.json',
    'branch_gcd_result': ROOT / 'experiments/hecke-432-j1728-derivative-ideal-20261026/result.json',
}


class Polys:
    def __init__(self, p):
        self.p = p
        self.products = 0

    def norm(self, coeffs):
        result = [int(v) % self.p for v in coeffs]
        while result and result[-1] == 0:
            result.pop()
        return result

    def add(self, a, b):
        return self.norm([(a[i] if i < len(a) else 0) +
                          (b[i] if i < len(b) else 0)
                          for i in range(max(len(a), len(b)))])

    def scale(self, a, k):
        return self.norm([k * v for v in a])

    def mul(self, a, b):
        self.products += 1
        if not a or not b:
            return []
        out = [0] * (len(a) + len(b) - 1)
        for i, v in enumerate(a):
            for j, w in enumerate(b):
                out[i + j] += v * w
        return self.norm(out)

    def value(self, a, z):
        value = 0
        for c in reversed(a):
            value = (value * z + c) % self.p
        return value


def coefficients(terms, x, y, degree, exponent, p):
    result = [0] * (degree + 1)
    for term in terms:
        k = term[exponent]
        result[k] = (result[k] + int(term['integer_coefficient'])
                     * pow(x, term['x_C_exponent'], p)
                     * pow(y, term['y_C_exponent'], p)) % p
    return result


def remainder_coefficients(pb, poly):
    c_acc, b_acc, a_acc = [], [], []
    c, b, a = [1], [], []
    for coeff in pb:
        c_acc = poly.add(c_acc, poly.scale(c, coeff))
        b_acc = poly.add(b_acc, poly.scale(b, coeff))
        a_acc = poly.add(a_acc, poly.scale(a, coeff))
        c, b, a = poly.scale(a, 64), c, poly.add(b, poly.mul(a, [0, 1]))
    return a_acc, b_acc, c_acc


def resultant_formula(a, b, c, poly):
    mul = poly.mul
    scale = poly.scale
    z = [0, 1]
    a2, b2, c2 = mul(a, a), mul(b, b), mul(c, c)
    terms = [scale(mul(a2, a), 4096),
             scale(mul(mul(a2, c), z), -128),
             scale(mul(mul(a, b2), z), 64),
             scale(mul(mul(a, b), c), -192),
             mul(mul(a, c2), [0, 0, 1]),
             scale(mul(b2, b), 64),
             mul(mul(b, c2), z),
             mul(c2, c)]
    result = []
    for term in terms:
        result = poly.add(result, term)
    return result


def main():
    path = HERE / 'audit_protocol.json'
    protocol = json.loads(path.read_text())
    for name, source in INPUTS.items():
        assert sha256(source.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    prior = json.loads(INPUTS['result'].read_text())
    b_terms = json.loads(INPUTS['relative_b_resolvent'].read_text())['terms']
    x_terms = json.loads(INPUTS['relative_xe_resolvent'].read_text())['terms']
    roots = json.loads(INPUTS['multiplicity_result'].read_text())['results']
    gcd = json.loads(INPUTS['branch_gcd_result'].read_text())['results']
    prior_map = {(r['prime'], tuple(r['C_point'])): r for r in prior['rows']}
    results = []
    total_roots = 0
    for field, common in zip(roots, gcd):
        p = int(field['prime'])
        assert p == int(common['prime'])
        common_map = {(tuple(r['C_point']), r['x_E']): r for r in common['rows']}
        for source in field['rows']:
            x, y = map(int, source['C_point'])
            key = (field['prime'], tuple(source['C_point']))
            saved = prior_map[key]
            poly = Polys(p)
            pb = coefficients(b_terms, x, y, 12, 'x_B_exponent', p)
            xe = poly.norm(coefficients(x_terms, x, y, 12, 'x_E_exponent', p))
            a, b, c = remainder_coefficients(pb, poly)
            q = resultant_formula(a, b, c, poly)
            assert q == [int(v) for v in saved['resultant_coefficients_low_to_high']]
            assert q == poly.scale(xe, int(saved['scalar']))
            derivative = poly.norm([i * q[i] for i in range(1, len(q))])
            for root in source['roots']:
                z = int(root['x_E'])
                check = common_map[(tuple(source['C_point']), root['x_E'])]
                assert poly.value(q, z) == poly.value(xe, z) == 0
                assert (poly.value(derivative, z) == 0) == (
                    check['common_B_gcd_degree'] == 2)
                total_roots += 1
            results.append({'prime': field['prime'], 'C_point': source['C_point'],
                            'resultant_degree': len(q) - 1,
                            'coefficient_identity': True,
                            'rational_roots_checked': len(source['roots']),
                            'polynomial_multiplications': poly.products})
    assert len(results) == protocol['source_points'] and total_roots == protocol['rational_roots']
    out = {'status': 'PASS_INDEPENDENT_EIGHT_TERM_RESULTANT_AUDIT',
           'protocol_sha256': sha256(path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'source_points_checked': len(results), 'rational_roots_checked': total_roots,
           'rows': results}
    (HERE / 'audit_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({k: out[k] for k in ('status', 'source_points_checked',
          'rational_roots_checked')}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
