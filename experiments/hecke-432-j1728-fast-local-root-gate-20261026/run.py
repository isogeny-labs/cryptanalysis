"""Count rational C-E pairs with fixed-degree finite-field polynomial gcds."""
import json
import os
from collections import Counter
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

os.environ.setdefault('SYMPY_GROUND_TYPES', 'python')
from sympy import Poly, isprime, sqrt_mod, symbols  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'field_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'coordinate_map': ROOT / 'experiments/hecke-27-coordinate-bridge-20261025/coordinate_map.json',
    'resolvent': ROOT / 'experiments/hecke-432-relative-resolvent-20261025/relative_resolvent.json',
    'bad_prime_audit': ROOT / 'experiments/hecke-432-j1728-sqrt2-resultants-20261026/bad_prime_audit.json',
    'million_exception_result': ROOT / 'experiments/hecke-432-j1728-sqrt2-million-20261026/exception_result.json',
    'ten_million_exception_result': ROOT / 'experiments/hecke-432-j1728-octic-collision-holdout-20261026/exception_result.json',
}


def mod_fraction(raw, p):
    q = Fraction(raw)
    return q.numerator * pow(q.denominator, -1, p) % p


def evaluate_terms(terms, x, y, p):
    return sum(mod_fraction(t['coefficient'], p)
               * pow(x, t['x_power'], p) * pow(y, t['y_power'], p)
               for t in terms) % p


class PolynomialArithmetic:
    def __init__(self, p):
        self.p = p
        self.counts = Counter()

    def normal(self, coefficients):
        a = [int(c) % self.p for c in coefficients]
        while a and a[-1] == 0:
            a.pop()
        return a

    def add(self, a, b):
        return self.normal([(a[i] if i < len(a) else 0) +
                            (b[i] if i < len(b) else 0)
                            for i in range(max(len(a), len(b)))])

    def sub(self, a, b):
        return self.normal([(a[i] if i < len(a) else 0) -
                            (b[i] if i < len(b) else 0)
                            for i in range(max(len(a), len(b)))])

    def mul(self, a, b):
        self.counts['polynomial_multiplications'] += 1
        self.counts['coefficient_product_terms'] += len(a) * len(b)
        if not a or not b:
            return []
        out = [0] * (len(a) + len(b) - 1)
        for i, x in enumerate(a):
            for j, y in enumerate(b):
                out[i + j] = (out[i + j] + x * y) % self.p
        return self.normal(out)

    def remainder(self, a, modulus):
        assert modulus
        self.counts['polynomial_remainders'] += 1
        current = self.normal(a)
        top_inverse = pow(modulus[-1], -1, self.p)
        while len(current) >= len(modulus):
            offset = len(current) - len(modulus)
            scale = current[-1] * top_inverse % self.p
            for j, c in enumerate(modulus):
                current[offset + j] = (current[offset + j] - scale * c) % self.p
            while current and current[-1] == 0:
                current.pop()
        return current

    def gcd(self, a, b):
        self.counts['polynomial_gcds'] += 1
        a, b = self.normal(a), self.normal(b)
        while b:
            a, b = b, self.remainder(a, b)
        if not a:
            return []
        lead_inverse = pow(a[-1], -1, self.p)
        return self.normal([c * lead_inverse for c in a])

    def powmod(self, base, exponent, modulus):
        assert exponent >= 0 and modulus
        self.counts['modular_exponentiations'] += 1
        result = [1]
        base = self.remainder(base, modulus)
        while exponent:
            if exponent & 1:
                result = self.remainder(self.mul(result, base), modulus)
            exponent >>= 1
            if exponent:
                base = self.remainder(self.mul(base, base), modulus)
        return result


def source_points(p, field, coordinate):
    symbol = symbols('t')
    coefficients = [mod_fraction(c, p)
                    for c in field['field_polynomial_coefficients_low_to_high']]
    f = Poly(sum(c * symbol ** i for i, c in enumerate(coefficients)),
             symbol, modulus=p)
    roots = sorted(int(root) % p for root in f.ground_roots())
    points = []
    undefined_map = []
    for x in roots:
        discriminant = (4 * pow(x, 3, p) - 27) % p
        for root in sqrt_mod(discriminant, p, all_roots=True):
            y = ((int(root) - 1) * pow(2, -1, p)) % p
            assert (y * y + y - x ** 3 + 7) % p == 0
            numerator = evaluate_terms(coordinate['numerator'], x, y, p)
            denominator = evaluate_terms(coordinate['denominator'], x, y, p)
            if not denominator:
                undefined_map.append([x, y])
            elif (numerator + 1728 * denominator) % p == 0:
                points.append([x, y])
    return roots, sorted(points), sorted(undefined_map)


def fiber_gate(p, x, y, terms):
    arithmetic = PolynomialArithmetic(p)
    R = [0] * 13
    for term in terms:
        i = term['x_E_exponent']
        R[i] = (R[i] + int(term['integer_coefficient'])
                * pow(x, term['x_C_exponent'], p)
                * pow(y, term['y_C_exponent'], p)) % p
    R = arithmetic.normal(R)
    if not R:
        return {'status': 'DEGENERATE_ZERO_RESOLVENT', 'C_point': [x, y]}
    if len(R) == 1:
        rational_x = []
    else:
        frobenius_remainder = arithmetic.powmod([0, 1], p, R)
        rational_x = arithmetic.gcd(R, arithmetic.sub(frobenius_remainder, [0, 1]))
    if len(rational_x) <= 1:
        nonzero_square_roots, zero_square_roots = [], []
    else:
        e_square = arithmetic.remainder([432, 0, 0, 1], rational_x)
        zero_square_roots = arithmetic.gcd(rational_x, e_square)
        character = arithmetic.powmod(e_square, (p - 1) // 2, rational_x)
        nonzero_square_roots = arithmetic.gcd(
            rational_x, arithmetic.sub(character, [1]))
    rational_x_count = max(0, len(rational_x) - 1)
    nonzero_square_count = max(0, len(nonzero_square_roots) - 1)
    zero_square_count = max(0, len(zero_square_roots) - 1)
    return {
        'status': 'EXACT_LOCAL_POLYNOMIAL_GCD_GATE',
        'C_point': [x, y], 'resolvent_degree': len(R) - 1,
        'rational_x_E_roots': rational_x_count,
        'nonzero_square_x_E_roots': nonzero_square_count,
        'zero_square_x_E_roots': zero_square_count,
        'rational_CE_pairs': 2 * nonzero_square_count + zero_square_count,
        'arithmetic_counts': dict(sorted(arithmetic.counts.items())),
    }


def main():
    pp = HERE / 'protocol.json'
    protocol = json.loads(pp.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_FAST_LOCAL_GATE_IMPLEMENTATION'
    for name, path in INPUTS.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    field = json.loads(INPUTS['field_certificate'].read_text())
    coordinate = json.loads(INPUTS['coordinate_map'].read_text())['source_j']
    terms = json.loads(INPUTS['resolvent'].read_text())['terms']
    cells = []
    for p in protocol['prime_cells']:
        assert isprime(p) and p % 24 == 11
        roots, points, undefined_map = source_points(p, field, coordinate)
        fibers = [fiber_gate(p, x, y, terms) for x, y in points]
        assert all(row['status'] == 'EXACT_LOCAL_POLYNOMIAL_GCD_GATE'
                   for row in fibers)
        total = sum(row['rational_CE_pairs'] for row in fibers)
        assert total == protocol['expected_rational_CE_pairs'][str(p)]
        cells.append({'prime': p, 'field_poly_rational_x_roots': roots,
                      'source_points': points, 'undefined_source_j_points': undefined_map,
                      'rational_CE_pairs': total, 'fibers': fibers})
        print(json.dumps({'prime': p, 'source_points': len(points),
                          'rational_CE_pairs': total}, sort_keys=True), flush=True)
    out = {'status': 'PASS_FAST_LOCAL_GCD_REPLAY_OF_ELEVEN_EXCEPTIONS',
           'protocol_sha256': sha256(pp.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'cells': cells}
    (HERE / 'result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')


if __name__ == '__main__':
    main()
