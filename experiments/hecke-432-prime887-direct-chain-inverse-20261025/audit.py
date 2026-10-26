"""Independent corrected-source audit of direct p887 chain recovery."""
import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = 887


def c_points():
    square_roots = defaultdict(list)
    for y in range(P):
        square_roots[y*y % P].append(y)
    points = []
    for x in range(P):
        for root in square_roots[(4*(x*x*x-7)+1) % P]:
            points.append((x, (root-1)*pow(2, -1, P) % P))
    return points


def j_value(record, point):
    x, y = point
    def evaluate(terms):
        total = 0
        for term in terms:
            coefficient = term['coefficient']
            numerator, denominator = (map(int, coefficient.split('/'))
                                      if '/' in coefficient else (int(coefficient), 1))
            total += numerator*pow(denominator, -1, P)*pow(x, term['x_power'], P)*pow(y, term['y_power'], P)
        return total % P
    denominator = evaluate(record['denominator'])
    return None if denominator == 0 else -evaluate(record['numerator'])*pow(denominator, -1, P) % P


def e_image(b):
    x, y = b
    assert x
    return ((x**3-64)*pow(x*x, -1, P) % P,
            y*(x**3+128)*pow(x, -3, P) % P)


def chain_key(record):
    return (record['source_label'], tuple(record['source_ainvs']), tuple(record['pair']))


def main():
    protocol_path = HERE/'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    inputs = {}
    for name, record in protocol['inputs'].items():
        path = Path(record['path'])
        assert sha256(path.read_bytes()).hexdigest() == record['sha256']
        inputs[name] = json.loads(path.read_text()) if path.suffix == '.json' else path
    result = json.loads((HERE/'result.json').read_text())
    assert result['protocol_sha256'] == sha256(protocol_path.read_bytes()).hexdigest()
    assert result['source_code_sha256'] == sha256((HERE/'recover_sage.py').read_bytes()).hexdigest()
    assert result['status'] == 'COMPLETE_DIRECT_P887_CHAIN_INVERSE'
    assert result['input_pairs'] == 872 and result['valid_triples'] == 864
    assert result['raw_forward_evaluations'] == result['matched_raw'] == 880
    assert not result['unmatched_outputs']
    generated = {}
    for shard in result['shards']:
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
    assert len(generated) == 864
    assert Counter(map(len, generated.values())) == {1: 856, 2: 8}
    maps = inputs['coordinate']
    intermediate = inputs['intermediate']
    by_js = defaultdict(list)
    for c in c_points():
        js = tuple(j_value(record, c) for record in
                   (maps['source_j'], intermediate['j3'], intermediate['j9'], maps['target_j']))
        by_js[js].append(c)
    models = {(tuple(row['curve_ainvs']), row['label']): row
              for row in inputs['audit_census']['rows']}
    expected = defaultdict(set)
    for i in range(4):
        for row in inputs[f'audit_corrected_{i:02d}']:
            model = models[(tuple(row['source_ainvs']), row['source_label'])]
            index2, index3 = row['pair']
            assert 0 <= index2 < len(model['two_paths'])
            assert 0 <= index3 < len(model['three_paths'])
            js = (model['j'], *(edge['target_j'] for edge in model['three_paths'][index3]))
            assert len(by_js[js]) == 1
            b = row['B_point']
            key = (*by_js[js][0], *e_image(b), *b)
            candidate = chain_key(row)
            assert candidate not in expected[key]
            expected[key].add(candidate)
    assert len(expected) == 864
    assert sum(map(len, expected.values())) == 872
    missing = sorted(set(expected)-set(generated))
    extra = sorted(set(generated)-set(expected))
    incorrect = sorted(key for key in set(expected)&set(generated)
                       if expected[key] != generated[key])
    assert not missing and not extra and not incorrect
    gcd_rows = []
    for i in range(4):
        gcd_rows.extend(inputs[f'gcd_{i:02d}'])
    assert len(gcd_rows) == 872
    valid = {(*row['C_point'], *row['E_point'], *row['B_candidates'][0])
             for row in gcd_rows if row['B_candidates']}
    assert valid == set(generated)
    assert sum(not row['B_candidates'] for row in gcd_rows) == 8
    double_keys = [{'C_point': list(key[:2]), 'E_point': list(key[2:4]),
                    'B_point': list(key[4:]),
                    'chain_candidates': [{'source_label': label,
                                          'source_ainvs': list(ainvs), 'pair': list(pair)}
                                         for label, ainvs, pair in sorted(expected[key])]}
                   for key in sorted(expected) if len(expected[key]) == 2]
    assert len(double_keys) == 8
    out = {'status': 'PASS_INDEPENDENT_DIRECT_CHAIN_AUDIT',
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'input_resolvent_pairs': len(gcd_rows), 'valid_triples': len(generated),
           'recovered_source_chains': sum(map(len, generated.values())),
           'candidate_count_histogram': dict(sorted(Counter(map(len, generated.values())).items())),
           'missing_triples': missing, 'extra_triples': extra,
           'incorrect_candidate_sets': incorrect,
           'exceptional_pairs_without_B': 8,
           'double_pairs': double_keys}
    (HERE/'audit.json').write_text(json.dumps(out, sort_keys=True, indent=2)+'\n')
    print(json.dumps({key: out[key] for key in ('status', 'valid_triples',
                                               'recovered_source_chains',
                                               'candidate_count_histogram')}, sort_keys=True))


if __name__ == '__main__':
    main()
