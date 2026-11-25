"""Independent integer-polynomial gcd and rational B-point audit."""
import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def trim(poly):
    poly = list(poly)
    while len(poly) > 1 and poly[-1] == 0:
        poly.pop()
    return poly


def divide(a, b, p):
    a, b = trim(a), trim(b)
    assert any(b)
    quotient = [0]*max(1, len(a)-len(b)+1)
    inverse = pow(b[-1], -1, p)
    while len(a) >= len(b) and any(a):
        scale = a[-1]*inverse % p
        offset = len(a)-len(b)
        quotient[offset] = scale
        for i, coefficient in enumerate(b):
            a[i+offset] = (a[i+offset]-scale*coefficient) % p
        a = trim(a)
    return trim(quotient), a


def remainder(a, b, p):
    return divide(a, b, p)[1]


def poly_add(a, b, p):
    return trim([((a[i] if i < len(a) else 0)+(b[i] if i < len(b) else 0)) % p
                 for i in range(max(len(a), len(b)))])


def poly_sub(a, b, p):
    return poly_add(a, [(-coefficient) % p for coefficient in b], p)


def poly_mul(a, b, p):
    out = [0]*(len(a)+len(b)-1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i+j] = (out[i+j]+x*y) % p
    return trim(out)


def polynomial_gcd(a, b, p):
    a, b = trim(a), trim(b)
    while any(b):
        a, b = b, remainder(a, b, p)
    inverse = pow(a[-1], -1, p)
    return trim([coefficient*inverse % p for coefficient in a])


def extended_gcd(a, b, p):
    r0, r1 = trim(a), trim(b)
    s0, s1 = [1], [0]
    t0, t1 = [0], [1]
    while any(r1):
        quotient, remainder_poly = divide(r0, r1, p)
        r0, r1 = r1, remainder_poly
        s0, s1 = s1, poly_sub(s0, poly_mul(quotient, s1, p), p)
        t0, t1 = t1, poly_sub(t0, poly_mul(quotient, t1, p), p)
    inverse = pow(r0[-1], -1, p)
    return tuple(trim([coefficient*inverse % p for coefficient in poly])
                 for poly in (r0, s0, t0))


def horner(coefficients, x, p):
    value = 0
    for coefficient in reversed(coefficients):
        value = (value*x+coefficient) % p
    return value


def specialize(terms, c, p):
    xc, yc = c
    coefficients = [0]*13
    for term in terms:
        i = term['x_B_exponent']
        coefficients[i] = (coefficients[i]+int(term['integer_coefficient'])
                           * pow(xc, term['x_C_exponent'], p)
                           * pow(yc, term['y_C_exponent'], p)) % p
    return trim(coefficients)


def b_points_by_x(p):
    squares = defaultdict(list)
    for y in range(p):
        squares[y*y % p].append(y)
    return {x: squares[(x**3-16) % p] for x in range(p)}


def main():
    protocol_path = HERE/'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    inputs = {}
    for name, record in protocol['inputs'].items():
        path = Path(record['path'])
        assert sha256(path.read_bytes()).hexdigest() == record['sha256']
        inputs[name] = json.loads(path.read_text())
    result = json.loads((HERE/'result.json').read_text())
    assert result['protocol_sha256'] == sha256(protocol_path.read_bytes()).hexdigest()
    assert result['source_code_sha256'] == sha256((HERE/'gcd_inverse_sage.py').read_bytes()).hexdigest()
    out = {'status': 'PASS_INDEPENDENT_INTEGER_GCD_AUDIT', 'primes': {}}
    terms = inputs['b_resolvent']['terms']
    previous = inputs['crossprime_result']
    for p in protocol['primes']:
        by_x = b_points_by_x(p)
        source_free_pairs = {}
        for shard in previous['primes'][str(p)]['pair_shards']:
            path = Path(protocol['inputs'][f"p{p}_{int(shard['file'].split('-')[-1].split('.')[0]):02d}"]['path'])
            assert sha256(path.read_bytes()).hexdigest() == shard['sha256']
            for row in json.loads(path.read_text()):
                key = (*row['C_point'], *row['E_point'])
                assert key not in source_free_pairs
                source_free_pairs[key] = row
        audited = set()
        histogram = Counter()
        special = []
        bezout_checks = 0
        for shard in result['primes'][str(p)]['shards']:
            path = HERE/shard['file']
            assert sha256(path.read_bytes()).hexdigest() == shard['sha256']
            rows = json.loads(path.read_text())
            assert len(rows) == shard['rows']
            for row in rows:
                c, e = row['C_point'], row['E_point']
                key = (*c, *e)
                assert key in source_free_pairs and key not in audited
                audited.add(key)
                xe, ye = e
                P = specialize(terms, c, p)
                cubic = [(-64) % p, 0, (-xe) % p, 1]
                common = polynomial_gcd(P, cubic, p)
                bezout_g, bezout_s, bezout_t = extended_gcd(P, cubic, p)
                assert bezout_g == common
                assert poly_add(poly_mul(bezout_s, P, p),
                                poly_mul(bezout_t, cubic, p), p) == common
                assert not any(remainder(P, common, p))
                assert not any(remainder(cubic, common, p))
                bezout_checks += 1
                assert len(P)-1 == row['P_B_degree']
                assert common == row['gcd_coefficients_low_to_high']
                assert len(common)-1 == row['gcd_degree']
                roots = [x for x in range(p) if horner(common, x, p) == 0]
                assert roots == sorted(r['x_B'] for r in row['rational_x_B_roots'])
                candidates = []
                for x in roots:
                    assert horner(P, x, p) == horner(cubic, x, p) == 0
                    for y in by_x[x]:
                        if x and ((x**3-64)*pow(x*x, -1, p)-xe) % p == 0 and (
                                y*(x**3+128)*pow(x, -3, p)-ye) % p == 0:
                            candidates.append([x, y])
                candidates.sort()
                assert candidates == row['B_candidates']
                old = source_free_pairs[key]
                assert (candidates == [old['B_point']]) if old['status'] == 'VALID' else not candidates
                histogram[(old['status'], len(common)-1, len(candidates))] += 1
                if old['status'] != 'VALID':
                    special.append({'C_point': c, 'E_point': e,
                                    'gcd_coefficients_low_to_high': common,
                                    'rational_x_B_roots': roots,
                                    'B_candidates': candidates})
        assert audited == set(source_free_pairs)
        assert len(audited) == result['primes'][str(p)]['pair_count']
        prior_source = inputs['crossprime_audit']['primes'][str(p)]
        assert prior_source['source_pairs'] == histogram[('VALID', 1, 1)]
        assert prior_source['source_chains'] == sum(
            int(multiplicity)*count for multiplicity, count in
            prior_source['source_pair_multiplicity_histogram'].items())
        out['primes'][str(p)] = {'audited_pairs': len(audited),
                               'verified_bezout_and_divisibility_certificates': bezout_checks,
                               'source_chains': prior_source['source_chains'],
                               'source_pair_multiplicity_histogram': prior_source['source_pair_multiplicity_histogram'],
                               'status_gcd_degree_candidate_histogram': [
                                   {'branch_status': key[0], 'gcd_degree': key[1],
                                    'B_candidates': key[2], 'count': count}
                                   for key, count in sorted(histogram.items())],
                               'exceptional_pairs': special}
        assert out['primes'][str(p)]['status_gcd_degree_candidate_histogram'] == (
            result['primes'][str(p)]['gcd_status_degree_candidate_histogram'])
    (HERE/'audit.json').write_text(json.dumps(out, sort_keys=True, indent=2)+'\n')
    print(json.dumps({'status': out['status'],
                      'pair_counts': {p: r['audited_pairs'] for p, r in out['primes'].items()}},
                     sort_keys=True))


if __name__ == '__main__':
    main()
