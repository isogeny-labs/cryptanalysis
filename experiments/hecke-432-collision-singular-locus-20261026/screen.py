"""Evaluate the exact B-resolvent gradient at complete inverse triples."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def evaluate(terms, c, t, p):
    x, y = c
    dcx, dcy = (2*y+1) % p, 3*x*x % p
    value = dt = dc = 0
    for row in terms:
        coeff = int(row['integer_coefficient']) % p
        a, b, k = (row['x_C_exponent'], row['y_C_exponent'], row['x_B_exponent'])
        base = coeff*pow(x, a, p)*pow(y, b, p)*pow(t, k, p)
        value = (value+base) % p
        if k:
            dt = (dt+coeff*k*pow(x, a, p)*pow(y, b, p)*pow(t, k-1, p)) % p
        if a:
            dc = (dc+dcx*coeff*a*pow(x, a-1, p)*pow(y, b, p)*pow(t, k, p)) % p
        if b:
            dc = (dc+dcy*coeff*b*pow(x, a, p)*pow(y, b-1, p)*pow(t, k, p)) % p
    return value, dt, dc


def main():
    protocol_path = HERE/'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_SINGULAR_LOCUS_SCREEN'
    for name, record in protocol['inputs'].items():
        assert sha256(Path(record['path']).read_bytes()).hexdigest() == record['sha256'], name
    terms = json.loads(Path(protocol['inputs']['b_resolvent']['path']).read_text())['terms']
    result = {'status': 'COMPLETE_SINGULAR_LOCUS_SCREEN',
              'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
              'source_code_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
              'primes': {}}
    all_rows = []
    for p in protocol['primes']:
        prior = json.loads(Path(protocol['inputs'][f'p{p}_result']['path']).read_text())
        block = prior['primes'][str(p)] if 'primes' in prior else prior
        rows = []
        for i, shard in enumerate(block['shards']):
            record = protocol['inputs'][f'p{p}_shard_{i:02d}']
            assert Path(record['path']).name == shard['file']
            assert record['sha256'] == shard['sha256']
            rows.extend(json.loads(Path(record['path']).read_text()))
        assert len(rows) == block['valid_triples']
        counts = Counter()
        mismatches = []
        for row in rows:
            c, b = row['C_point'], row['B_point']
            value, dt, dc = evaluate(terms, c, b[0], p)
            assert value == 0
            multiplicity = len(row['chain_candidates'])
            # Genericity is a property of j, not the census label: p883
            # calls ordinary generic-j models base/quadratic_twist.
            generic = all(int(candidate['source_ainvs'][3]) % p != 0 and
                          int(candidate['source_ainvs'][4]) % p != 0
                          for candidate in row['chain_candidates'])
            singular = dt == 0 and dc == 0
            counts[(generic, multiplicity, dt == 0, dc == 0)] += 1
            if generic and ((multiplicity > 1) != singular):
                mismatches.append({'C_point': c, 'E_point': row['E_point'],
                                   'B_point': b, 'multiplicity': multiplicity,
                                   'dT': dt, 'dC': dc})
            all_rows.append({'prime': p, 'C_point': c, 'E_point': row['E_point'],
                             'B_point': b, 'multiplicity': multiplicity,
                             'generic_source': generic, 'dT': dt, 'dC': dc,
                             'singular': singular})
        result['primes'][str(p)] = {'valid_triples': len(rows),
                                   'classification': [
                                       {'generic_source': key[0], 'multiplicity': key[1],
                                        'dT_zero': key[2], 'dC_zero': key[3], 'count': count}
                                       for key, count in sorted(counts.items())],
                                   'generic_prediction_mismatches': mismatches}
        print(json.dumps({'prime': p, 'triples': len(rows),
                          'generic_prediction_mismatches': len(mismatches),
                          'classification': result['primes'][str(p)]['classification']},
                         sort_keys=True), flush=True)
    rows_path = HERE/'gradient_rows.json'
    rows_path.write_text(json.dumps(all_rows, sort_keys=True, separators=(',', ':'))+'\n')
    result['gradient_rows_sha256'] = sha256(rows_path.read_bytes()).hexdigest()
    result['status'] = ('PASS_GENERIC_SINGULARITY_PREDICTION' if
                        all(not r['generic_prediction_mismatches'] for r in result['primes'].values())
                        else 'FAIL_GENERIC_SINGULARITY_PREDICTION')
    (HERE/'result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({'status': result['status'], 'rows': len(all_rows)}))


if __name__ == '__main__':
    main()
