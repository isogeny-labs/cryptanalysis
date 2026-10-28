"""Independent finite-field audit of p919 pair, B-gcd and chain sets."""
import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = 919


def curve_points(kind):
    roots = defaultdict(list)
    for y in range(P):
        roots[y*y % P].append(y)
    return [(x, (z-1)*pow(2, -1, P) % P if kind == 'C' else z)
            for x in range(P)
            for z in roots[(4*(x*x*x-7)+1 if kind == 'C' else x*x*x+432) % P]]


def value_at(terms, x, y):
    total = 0
    for term in terms:
        coeff = term['coefficient']
        a, b = (map(int, coeff.split('/')) if '/' in coeff else (int(coeff), 1))
        total += a*pow(b, -1, P)*pow(x, term['x_power'], P)*pow(y, term['y_power'], P)
    return total % P


def j_value(record, c):
    denominator = value_at(record['denominator'], *c)
    return None if not denominator else -value_at(record['numerator'], *c)*pow(denominator, -1, P) % P


def trim(a):
    a = list(a)
    while len(a) > 1 and a[-1] == 0:
        a.pop()
    return a


def divide(a, b):
    a, b = trim(a), trim(b)
    assert any(b)
    q = [0]*max(1, len(a)-len(b)+1)
    inv = pow(b[-1], -1, P)
    while len(a) >= len(b) and any(a):
        v, shift = a[-1]*inv % P, len(a)-len(b)
        q[shift] = v
        for i, coeff in enumerate(b):
            a[i+shift] = (a[i+shift]-v*coeff) % P
        a = trim(a)
    return trim(q), a


def mul(a, b):
    out = [0]*(len(a)+len(b)-1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i+j] = (out[i+j]+x*y) % P
    return trim(out)


def add(a, b):
    return trim([((a[i] if i < len(a) else 0)+(b[i] if i < len(b) else 0)) % P
                 for i in range(max(len(a), len(b)))])


def sub(a, b):
    return add(a, [(-x) % P for x in b])


def extended_gcd(a, b):
    r0, r1 = trim(a), trim(b)
    s0, s1, t0, t1 = [1], [0], [0], [1]
    while any(r1):
        q, r = divide(r0, r1)
        r0, r1 = r1, r
        s0, s1 = s1, sub(s0, mul(q, s1))
        t0, t1 = t1, sub(t0, mul(q, t1))
    inv = pow(r0[-1], -1, P)
    return tuple(trim([x*inv % P for x in a]) for a in (r0, s0, t0))


def horner(poly, x):
    out = 0
    for a in reversed(poly):
        out = (out*x+a) % P
    return out


def specialize(terms, c):
    x, y = c
    out = [0]*13
    for term in terms:
        i = term['x_B_exponent']
        out[i] = (out[i]+int(term['integer_coefficient']) *
                  pow(x, term['x_C_exponent'], P)*pow(y, term['y_C_exponent'], P)) % P
    return trim(out)


def chain_key(row):
    return row['source_label'], tuple(row['source_ainvs']), tuple(row['pair'])


def b_add(a, b):
    if a is None:
        return b
    if b is None:
        return a
    x1, y1 = a
    x2, y2 = b
    if x1 == x2 and (y1+y2) % P == 0:
        return None
    slope = ((3*x1*x1)*pow(2*y1, -1, P) if a == b else
             (y2-y1)*pow((x2-x1) % P, -1, P)) % P
    x3 = (slope*slope-x1-x2) % P
    return x3, (slope*(x1-x3)-y1) % P


def b_mul(n, point):
    out = None
    while n:
        if n & 1:
            out = b_add(out, point)
        point = b_add(point, point)
        n >>= 1
    return out


def main():
    protocol_path = HERE/'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    inputs = {}
    for name, record in protocol['inputs'].items():
        path = Path(record['path'])
        assert sha256(path.read_bytes()).hexdigest() == record['sha256'], name
        if path.suffix == '.json':
            inputs[name] = json.loads(path.read_text())
    screen_path, result_path, gcd_path = (HERE/x for x in ('screen_result.json', 'result.json', 'gcd_rows.json'))
    screen, result, gcd_rows = (json.loads(x.read_text()) for x in (screen_path, result_path, gcd_path))
    assert screen['protocol_sha256'] == result['protocol_sha256'] == sha256(protocol_path.read_bytes()).hexdigest()
    assert screen['source_code_sha256'] == sha256((HERE/'screen.py').read_bytes()).hexdigest()
    assert result['source_code_sha256'] == sha256((HERE/'recover_sage.py').read_bytes()).hexdigest()
    assert result['screen_result_sha256'] == sha256(screen_path.read_bytes()).hexdigest()
    assert result['gcd_rows_sha256'] == sha256(gcd_path.read_bytes()).hexdigest()
    pair_rows = []
    for shard in screen['shards']:
        path = HERE/shard['file']
        assert sha256(path.read_bytes()).hexdigest() == shard['sha256']
        block = json.loads(path.read_text())
        assert len(block) == shard['rows']
        pair_rows.extend(block)
    pair_keys = {(*r['C_point'], *r['E_point']) for r in pair_rows}
    assert len(pair_keys) == len(pair_rows) == screen['resolvent_pairs']
    # Independently enumerate all rational pairs satisfying the resolvent.
    coeffs_by_c = {}
    for c in curve_points('C'):
        out = [0]*13
        for term in inputs['resolvent']['terms']:
            i = term['x_E_exponent']
            out[i] = (out[i]+int(term['integer_coefficient']) *
                      pow(c[0], term['x_C_exponent'], P) *
                      pow(c[1], term['y_C_exponent'], P)) % P
        coeffs_by_c[c] = out
    expected_pairs = {(*c, *e) for c, coeffs in coeffs_by_c.items()
                      for e in curve_points('E') if horner(coeffs, e[0]) == 0}
    assert pair_keys == expected_pairs
    assert len(gcd_rows) == len(pair_rows)
    pair_by_key = {(*row['C_point'], *row['E_point']): row for row in pair_rows}
    checked = set()
    b_squares = defaultdict(list)
    for y in range(P):
        b_squares[y*y % P].append(y)
    for row in gcd_rows:
        c, e = row['C_point'], row['E_point']
        key = (*c, *e)
        assert key in pair_by_key and key not in checked
        checked.add(key)
        xe, ye = e
        polynomial = specialize(inputs['b_resolvent']['terms'], c)
        cubic = [(-64) % P, 0, (-xe) % P, 1]
        gcd, s, t = extended_gcd(polynomial, cubic)
        assert gcd == row['gcd_coefficients_low_to_high']
        assert add(mul(s, polynomial), mul(t, cubic)) == gcd
        assert not any(divide(polynomial, gcd)[1])
        assert not any(divide(cubic, gcd)[1])
        assert len(gcd)-1 == row['gcd_degree']
        roots = [x for x in range(P) if horner(gcd, x) == 0]
        candidates = sorted([x, y] for x in roots for y in b_squares[(x**3-16) % P]
                            if x and (x**3-64)*pow(x*x, -1, P) % P == xe
                            and y*(x**3+128)*pow(x, -3, P) % P == ye)
        assert candidates == row['B_candidates'] == [pair_by_key[key]['B_point']]
    assert checked == pair_keys
    generated = {}
    for shard in result['shards']:
        path = HERE/shard['file']
        assert sha256(path.read_bytes()).hexdigest() == shard['sha256']
        block = json.loads(path.read_text())
        assert len(block) == shard['rows']
        for row in block:
            key = (*row['C_point'], *row['E_point'], *row['B_point'])
            assert key not in generated
            chains = {chain_key(candidate) for candidate in row['chain_candidates']}
            assert len(chains) == len(row['chain_candidates'])
            generated[key] = chains
    coord, intermediate = inputs['coordinate'], inputs['intermediate']
    by_js = defaultdict(list)
    for c in coeffs_by_c:
        js = tuple(j_value(record, c) for record in
                   (coord['source_j'], intermediate['j3'], intermediate['j9'], coord['target_j']))
        by_js[js].append(c)
    models = {(tuple(row['curve_ainvs']), row['label']): row
              for row in inputs['audit_census']['rows']}
    expected = defaultdict(set)
    for row in inputs['audit_image']['rows']:
        model = models[(tuple(row['source_ainvs']), row['source_label'])]
        i, j = row['pair']
        assert 0 <= i < len(model['two_paths']) and 0 <= j < len(model['three_paths'])
        js = (model['j'], *(edge['target_j'] for edge in model['three_paths'][j]))
        assert len(by_js[js]) == 1
        assert len(row['B_candidates']) == 1 and row['B_candidates'][0] is not None
        b = row['B_candidates'][0]
        x, y = b
        e = ((x**3-64)*pow(x*x, -1, P) % P,
             y*(x**3+128)*pow(x, -3, P) % P)
        key = (*by_js[js][0], *e, *b)
        candidate = chain_key(row)
        assert candidate not in expected[key]
        expected[key].add(candidate)
    missing = sorted(set(expected)-set(generated))
    extra = sorted(set(generated)-set(expected))
    wrong = sorted(key for key in set(expected)&set(generated)
                   if expected[key] != generated[key])
    assert not missing and not extra and not wrong
    assert len(expected) == len(generated) == len(pair_rows)
    assert sum(map(len, expected.values())) == len(inputs['audit_image']['rows']) == 1296
    histogram = dict(sorted(Counter(map(len, expected.values())).items()))
    assert histogram == {int(k): v for k, v in result['candidate_count_histogram'].items()}
    double_b = sorted({key[4:] for key, chains in expected.items() if len(chains) == 2})
    cube_roots = [x for x in range(P) if pow(x, 3, P) == 1]
    y_roots = [y for y in range(P) if y*y % P == (-15) % P]
    assert cube_roots == [1, 52, 866] and y_roots == [297, 622]
    assert double_b == sorted((x, y) for x in cube_roots for y in y_roots)
    assert all(b_mul(434, b) is None and all(b_mul(434//q, b) is not None
               for q in (2, 7, 31)) for b in double_b)
    out = {'status': 'PASS_INDEPENDENT_P919_DIRECT_INVERSE_AUDIT',
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'complete_rational_resolvent_pairs': len(expected_pairs),
           'integer_bezout_certificates': len(checked),
           'valid_triples': len(generated), 'source_chains': 1296,
           'candidate_count_histogram': histogram,
           'double_fiber_B_points': [list(b) for b in double_b],
           'double_fiber_B_equations': 'x_B^3=1, y_B^2=-15 (mod 919)',
           'double_fiber_B_point_orders': [434]*len(double_b),
           'missing_triples': missing, 'extra_triples': extra,
           'incorrect_candidate_sets': wrong}
    (HERE/'audit.json').write_text(json.dumps(out, sort_keys=True, indent=2)+'\n')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
