"""Independent frozen-source audit of direct p883/p997 chain recovery."""
import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def c_points(p):
    roots = defaultdict(list)
    for y in range(p):
        roots[y*y % p].append(y)
    return [(x, (root-1)*pow(2, -1, p) % p)
            for x in range(p) for root in roots[(4*(x*x*x-7)+1) % p]]


def j_value(record, c, p):
    x, y = c
    def value(terms):
        total = 0
        for t in terms:
            coefficient = t['coefficient']
            a, b = (map(int, coefficient.split('/')) if '/' in coefficient
                    else (int(coefficient), 1))
            total += a*pow(b, -1, p)*pow(x, t['x_power'], p)*pow(y, t['y_power'], p)
        return total % p
    denominator = value(record['denominator'])
    return None if not denominator else -value(record['numerator'])*pow(denominator, -1, p) % p


def e_image(b, p):
    x, y = b
    return ((x**3-64)*pow(x*x, -1, p) % p,
            y*(x**3+128)*pow(x, -3, p) % p)


def chain_key(row):
    return row['source_label'], tuple(row['source_ainvs']), tuple(row['pair'])


def main():
    protocol_path = HERE/'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    inputs = {}
    for name, record in protocol['inputs'].items():
        path = Path(record['path'])
        assert sha256(path.read_bytes()).hexdigest() == record['sha256'], name
        if path.suffix == '.json':
            inputs[name] = json.loads(path.read_text())
    result = json.loads((HERE/'result.json').read_text())
    assert result['protocol_sha256'] == sha256(protocol_path.read_bytes()).hexdigest()
    assert result['source_code_sha256'] == sha256((HERE/'recover_sage.py').read_bytes()).hexdigest()
    audits = {}
    for p in (883, 997):
        run = result['primes'][str(p)]
        generated = {}
        for shard in run['shards']:
            path = HERE/shard['file']
            assert sha256(path.read_bytes()).hexdigest() == shard['sha256']
            rows = json.loads(path.read_text())
            assert len(rows) == shard['rows']
            for row in rows:
                key = (*row['C_point'], *row['E_point'], *row['B_point'])
                assert key not in generated
                values = {chain_key(candidate) for candidate in row['chain_candidates']}
                assert len(values) == len(row['chain_candidates'])
                generated[key] = values
        expected = defaultdict(set)
        if p == 883:
            coord, intermediate = inputs['coordinate'], inputs['intermediate_883']
            by_js = defaultdict(list)
            for c in c_points(p):
                js = tuple(j_value(record, c, p) for record in
                           (coord['source_j'], intermediate['j3'], intermediate['j9'], coord['target_j']))
                by_js[js].append(c)
            models = {tuple(row['curve_ainvs']): row
                      for row in inputs['audit_census_883']['rows']}
            for row in inputs['audit_image_883']['rows']:
                model = models[tuple(row['source_ainvs'])]
                i, j = row['pair']
                assert 0 <= i < len(model['two_paths']) and 0 <= j < len(model['three_paths'])
                js = (model['j'], *(edge['target_j'] for edge in model['three_paths'][j]))
                assert len(by_js[js]) == 1
                assert len(row['B_points']) == 1
                b = row['B_points'][0]
                key = (*by_js[js][0], *e_image(b, p), *b)
                candidate = model['variant'], tuple(row['source_ainvs']), (i, j)
                assert candidate not in expected[key]
                expected[key].add(candidate)
        else:
            source = inputs['audit_lift_997']['rows']
            models = {(tuple(row['curve_ainvs']), row['label']): row
                      for row in inputs['audit_census_997']['rows']}
            source_to_b = {}
            for fiber in inputs['audit_fibers_997']['fibers']:
                for index in fiber['source_indices']:
                    assert index not in source_to_b
                    source_to_b[index] = fiber['B_point']
            assert set(source_to_b) == set(range(len(source)))
            for index, row in enumerate(source):
                model = models[(tuple(row['source_ainvs']), row['source_label'])]
                i, j = row['pair']
                assert 0 <= i < len(model['two_paths']) and 0 <= j < len(model['three_paths'])
                b = source_to_b[index]
                assert tuple(row['E_point']) == e_image(b, p)
                key = (*row['C_point'], *row['E_point'], *b)
                candidate = chain_key(row)
                assert candidate not in expected[key]
                expected[key].add(candidate)
        gcd_rows = [row for i in range(4 if p == 883 else 8)
                    for row in inputs[f'gcd_{p}_{i:02d}']]
        inverse_keys = {(*r['C_point'], *r['E_point'], *r['B_candidates'][0])
                        for r in gcd_rows if r['B_candidates']}
        missing = sorted(set(expected)-set(generated))
        extra = sorted(set(generated)-set(expected))
        wrong = sorted(k for k in set(expected)&set(generated) if expected[k] != generated[k])
        assert inverse_keys == set(generated) == set(expected)
        assert not missing and not extra and not wrong
        histogram = dict(sorted(Counter(map(len, generated.values())).items()))
        audits[str(p)] = {'valid_triples': len(generated),
                          'recovered_source_chains': sum(map(len, generated.values())),
                          'candidate_count_histogram': histogram,
                          'missing_triples': missing, 'extra_triples': extra,
                          'incorrect_candidate_sets': wrong}
    assert audits['883']['recovered_source_chains'] == 864
    assert audits['997']['recovered_source_chains'] == 1800
    out = {'status': 'PASS_INDEPENDENT_CROSSPRIME_CHAIN_AUDIT',
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'primes': audits}
    (HERE/'audit.json').write_text(json.dumps(out, sort_keys=True, indent=2)+'\n')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
