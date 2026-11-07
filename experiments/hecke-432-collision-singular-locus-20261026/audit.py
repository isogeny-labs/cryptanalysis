"""Independent dual-number replay of all recorded B-resolvent gradients."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def multiply(a, b, p):
    return (a[0]*b[0] % p, (a[0]*b[1]+a[1]*b[0]) % p)


def powers(a, n, p):
    out = [(1, 0)]
    for _ in range(n):
        out.append(multiply(out[-1], a, p))
    return out


def dual_value(terms, c, t, p, direction):
    x, y = c
    if direction == 'T':
        dx, dy, dt = 0, 0, 1
    else:
        dx, dy, dt = (2*y+1) % p, 3*x*x % p, 0
    max_x = max(row['x_C_exponent'] for row in terms)
    max_y = max(row['y_C_exponent'] for row in terms)
    max_t = max(row['x_B_exponent'] for row in terms)
    xp, yp, tp = (powers((x, dx), max_x, p), powers((y, dy), max_y, p),
                  powers((t, dt), max_t, p))
    total = (0, 0)
    for row in terms:
        monomial = multiply(multiply(xp[row['x_C_exponent']],
                                     yp[row['y_C_exponent']], p),
                            tp[row['x_B_exponent']], p)
        coefficient = int(row['integer_coefficient']) % p
        total = ((total[0]+coefficient*monomial[0]) % p,
                 (total[1]+coefficient*monomial[1]) % p)
    return total


def main():
    protocol_path, refinement_path = HERE/'protocol.json', HERE/'refinement_protocol.json'
    protocol, refinement = (json.loads(path.read_text()) for path in
                            (protocol_path, refinement_path))
    for record in protocol['inputs'].values():
        assert sha256(Path(record['path']).read_bytes()).hexdigest() == record['sha256']
    for record in refinement['inputs'].values():
        assert sha256(Path(record['path']).read_bytes()).hexdigest() == record['sha256']
    result = json.loads((HERE/'result.json').read_text())
    refined = json.loads((HERE/'refined_result.json').read_text())
    assert result['protocol_sha256'] == sha256(protocol_path.read_bytes()).hexdigest()
    assert result['source_code_sha256'] == sha256((HERE/'screen.py').read_bytes()).hexdigest()
    assert refined['protocol_sha256'] == sha256(refinement_path.read_bytes()).hexdigest()
    assert refined['source_code_sha256'] == sha256((HERE/'refined_screen.py').read_bytes()).hexdigest()
    jacobian_path = HERE/'jacobian_protocol.json'
    jacobian_protocol = json.loads(jacobian_path.read_text())
    for record in jacobian_protocol['inputs'].values():
        assert sha256(Path(record['path']).read_bytes()).hexdigest() == record['sha256']
    jacobian_result = json.loads((HERE/'jacobian_result.json').read_text())
    assert jacobian_result['protocol_sha256'] == sha256(jacobian_path.read_bytes()).hexdigest()
    assert jacobian_result['source_code_sha256'] == sha256((HERE/'jacobian_screen.py').read_bytes()).hexdigest()
    rows_path = HERE/'gradient_rows.json'
    assert result['gradient_rows_sha256'] == sha256(rows_path.read_bytes()).hexdigest()
    rows = json.loads(rows_path.read_text())
    terms = json.loads(Path(protocol['inputs']['b_resolvent']['path']).read_text())['terms']
    prior_keys = set()
    for p in protocol['primes']:
        prior = json.loads(Path(protocol['inputs'][f'p{p}_result']['path']).read_text())
        block = prior['primes'][str(p)] if 'primes' in prior else prior
        for i, shard in enumerate(block['shards']):
            record = protocol['inputs'][f'p{p}_shard_{i:02d}']
            for row in json.loads(Path(record['path']).read_text()):
                key = (p, *row['C_point'], *row['E_point'], *row['B_point'])
                assert key not in prior_keys
                prior_keys.add(key)
    audited_keys = set()
    counts = Counter()
    jacobian_counts = Counter()
    discrepancies = []
    for row in rows:
        p, c, b = row['prime'], row['C_point'], row['B_point']
        key = (p, *c, *row['E_point'], *b)
        assert key in prior_keys and key not in audited_keys
        audited_keys.add(key)
        value_t, dt = dual_value(terms, c, b[0], p, 'T')
        value_c, dc = dual_value(terms, c, b[0], p, 'C')
        if value_t or value_c or dt != row['dT'] or dc != row['dC']:
            discrepancies.append({'key': key, 'value_T': value_t, 'value_C': value_c,
                                  'replayed_dT': dt, 'replayed_dC': dc})
        singular = dt == dc == 0
        y_zero = b[1] == 0
        double = row['multiplicity'] > 1
        counts[(p, singular, y_zero, double)] += 1
        db = 2*b[1]*dt % p
        jacobian_counts[(p, dc == 0, db == 0, double)] += 1
        assert row['singular'] == singular
        assert double == (singular or y_zero)
        assert double == (dc == 0 and db == 0)
    assert audited_keys == prior_keys and len(rows) == 6120
    assert not discrepancies
    for p in protocol['primes']:
        actual = [{'singular': a, 'y_B_zero': b, 'double': c, 'count': n}
                  for (q, a, b, c), n in sorted(counts.items()) if q == p]
        assert actual == refined['primes'][str(p)]['classification']
        assert not refined['primes'][str(p)]['mismatches']
        jac_actual = [{'C_derivative_zero': a, 'B_derivative_zero': b,
                       'double': c, 'count': n}
                      for (q, a, b, c), n in sorted(jacobian_counts.items()) if q == p]
        assert jac_actual == jacobian_result['primes'][str(p)]['classification']
        assert not jacobian_result['primes'][str(p)]['mismatches']
    out = {'status': 'PASS_INDEPENDENT_DUAL_NUMBER_GRADIENT_AUDIT',
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'refinement_protocol_sha256': sha256(refinement_path.read_bytes()).hexdigest(),
           'triples': len(rows), 'gradient_discrepancies': discrepancies,
           'refined_rule_mismatches': refined['total_mismatches'],
           'restricted_jacobian_mismatches': jacobian_result['total_mismatches'],
           'jacobian_protocol_sha256': sha256(jacobian_path.read_bytes()).hexdigest(),
           'classification': refined['primes']}
    (HERE/'audit.json').write_text(json.dumps(out, sort_keys=True, indent=2)+'\n')
    print(json.dumps({'status': out['status'], 'triples': len(rows),
                      'gradient_discrepancies': len(discrepancies),
                      'refined_rule_mismatches': refined['total_mismatches'],
                      'restricted_jacobian_mismatches': jacobian_result['total_mismatches']}))


if __name__ == '__main__':
    main()
