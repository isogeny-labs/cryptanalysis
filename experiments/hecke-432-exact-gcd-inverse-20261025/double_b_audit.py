"""Independently join corrected p887 double source pairs to gcd B candidates."""
import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = 887


def c_points():
    squares = defaultdict(list)
    for y in range(P):
        squares[y*y % P].append(y)
    out = []
    for x in range(P):
        for value in squares[(4*(x*x*x-7)+1) % P]:
            out.append((x, (value-1)*pow(2, -1, P) % P))
    return out


def j_value(record, point):
    x, y = point
    def evaluate(terms):
        out = 0
        for term in terms:
            coefficient = term['coefficient']
            numerator, denominator = (map(int, coefficient.split('/'))
                                      if '/' in coefficient else (int(coefficient), 1))
            out += numerator*pow(denominator, -1, P)*pow(x, term['x_power'], P)*pow(y, term['y_power'], P)
        return out % P
    denominator = evaluate(record['denominator'])
    return None if denominator == 0 else -evaluate(record['numerator'])*pow(denominator, -1, P) % P


def image_e(b):
    x, y = b
    assert x
    return ((x**3-64)*pow(x*x, -1, P) % P,
            y*(x**3+128)*pow(x, -3, P) % P)


def main():
    protocol_path = HERE/'double_b_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    inputs = {}
    for name, record in protocol['inputs'].items():
        path = Path(record['path'])
        assert sha256(path.read_bytes()).hexdigest() == record['sha256']
        inputs[name] = json.loads(path.read_text())
    maps = inputs['coordinate']
    intermediate = inputs['intermediate']
    by_js = defaultdict(list)
    for cp in c_points():
        js = tuple(j_value(record, cp) for record in
                   (maps['source_j'], intermediate['j3'], intermediate['j9'], maps['target_j']))
        by_js[js].append(cp)
    models = {(tuple(row['curve_ainvs']), row['label']): row
              for row in inputs['census']['rows']}
    sources = defaultdict(list)
    for i in range(4):
        for row in inputs[f'corrected_{i:02d}']:
            model = models[(tuple(row['source_ainvs']), row['source_label'])]
            js = (model['j'], *(edge['target_j'] for edge in model['three_paths'][row['pair'][1]]))
            assert len(by_js[js]) == 1
            b = tuple(row['B_point'])
            key = (*by_js[js][0], *image_e(b))
            sources[key].append({'B_point': b, 'source_label': row['source_label'],
                                 'source_ainvs': row['source_ainvs'], 'pair': row['pair']})
    gcd_candidates = {}
    for i in range(4):
        for row in inputs[f'gcd_{i:02d}']:
            key = (*row['C_point'], *row['E_point'])
            assert key not in gcd_candidates
            gcd_candidates[key] = {tuple(b) for b in row['B_candidates']}
    assert len(sources) == 864 and len(gcd_candidates) == 872
    assert Counter(map(len, sources.values())) == {1: 856, 2: 8}
    assert all(gcd_candidates[key] == {source['B_point'] for source in values}
               for key, values in sources.items())
    doubles = [{'C_point': list(key[:2]), 'E_point': list(key[2:]),
                'B_point': list(next(iter(gcd_candidates[key]))),
                'source_chains': [{k: v for k, v in source.items() if k != 'B_point'}
                                  for source in values]}
               for key, values in sorted(sources.items()) if len(values) == 2]
    assert len(doubles) == 8
    out = {'status': 'PASS_ALL_P887_DOUBLE_SOURCES_SHARE_GCD_B',
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_chains': sum(map(len, sources.values())),
           'source_pairs': len(sources), 'double_pairs': doubles,
           'extra_resolvent_pairs_without_B': len(set(gcd_candidates)-set(sources))}
    (HERE/'double_b_audit.json').write_text(json.dumps(out, sort_keys=True, indent=2)+'\n')
    print(json.dumps({key: out[key] for key in ('status', 'source_chains',
                                               'source_pairs', 'extra_resolvent_pairs_without_B')},
                     sort_keys=True))


if __name__ == '__main__':
    main()
