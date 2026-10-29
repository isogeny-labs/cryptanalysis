"""Prospective p1367 B lift and source-chain multiplicity test."""
import importlib.util
import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'
from sage.all import EllipticCurve, EllipticCurve_from_j, GF, PolynomialRing, QQ

HERE = Path(__file__).resolve().parent
P = 1367


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def specialize(terms, c, field, ring):
    x, y = map(field, c)
    t = ring.gen()
    return sum((field(int(row['integer_coefficient'])) *
                x**row['x_C_exponent'] * y**row['y_C_exponent'] *
                t**row['x_B_exponent'] for row in terms), ring.zero())


def j_value(record, c, field):
    x, y = map(field, c)
    def value(terms):
        return sum((field(QQ(term['coefficient'])) * x**term['x_power'] *
                    y**term['y_power'] for term in terms), field(0))
    denominator = value(record['denominator'])
    assert denominator
    return int(-value(record['numerator'])/denominator)


def main():
    protocol_path = HERE/'inverse_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_P1367_INVERSE'
    for name, record in protocol['inputs'].items():
        assert sha256(Path(record['path']).read_bytes()).hexdigest() == record['sha256'], name
    screen_path = HERE/'screen_result.json'
    screen = json.loads(screen_path.read_text())
    assert screen['protocol_sha256'] == sha256((HERE/'protocol.json').read_bytes()).hexdigest()
    rows_path = HERE/'source_free_rows.json'
    assert screen['rows_sha256'] == sha256(rows_path.read_bytes()).hexdigest()
    all_pairs = json.loads(rows_path.read_text())
    assert len(all_pairs) == screen['resolvent_pairs']
    pairs = [row for row in all_pairs if row['status'] == 'VALID']
    assert len(pairs) == screen['valid_triples']
    inputs = {name: json.loads(Path(record['path']).read_text())
              for name, record in protocol['inputs'].items()
              if name not in protocol.get('audit_only_inputs', []) and
              Path(record['path']).suffix == '.json'}
    paths = module('p919_inverse_paths', protocol['inputs']['path_enumerator']['path']).paths
    forward = module('p919_inverse_forward', protocol['inputs']['forward_evaluator']['path'])
    field = GF(P)
    ring = PolynomialRing(field, 'T')
    t = ring.gen()
    curve_b = EllipticCurve(field, [0, 0, 0, 0, -16])
    terms = inputs['b_resolvent']['terms']
    coord, intermediate = inputs['coordinate'], inputs['intermediate']
    triples_by_c = defaultdict(dict)
    gcd_hist = Counter()
    gcd_rows = []
    for pair in pairs:
        c, e = pair['C_point'], pair['E_point']
        xe, ye = map(field, e)
        polynomial = specialize(terms, c, field, ring)
        assert polynomial.degree() == 12
        common = polynomial.gcd(t**3-xe*t**2-64)
        bpoints = set()
        for x, _ in common.roots():
            for point in curve_b.lift_x(x, all=True):
                y = point[1]
                if x and (x**3-64)/x**2 == xe and y*(x**3+128)/x**3 == ye:
                    bpoints.add((int(x), int(y)))
        bpoints = sorted(bpoints)
        gcd_hist[(int(common.degree()), len(bpoints))] += 1
        assert pair['status'] == 'VALID' and [list(b) for b in bpoints] == [pair['B_point']]
        gcd_rows.append({'C_point': c, 'E_point': e, 'gcd_degree': int(common.degree()),
                         'gcd_coefficients_low_to_high': list(map(int, common.list())),
                         'B_candidates': [list(b) for b in bpoints]})
        for b in bpoints:
            key = (*e, *b)
            assert key not in triples_by_c[tuple(c)]
            triples_by_c[tuple(c)][key] = pair
    generated = defaultdict(set)
    models = {}
    evaluations = matches = 0
    unmatched = []
    for count, (c, targets) in enumerate(sorted(triples_by_c.items()), 1):
        js = [j_value(record, c, field) for record in
              (coord['source_j'], intermediate['j3'], intermediate['j9'], coord['target_j'])]
        curve = EllipticCurve_from_j(field(js[0]))
        ainvs = tuple(map(int, curve.ainvs()))
        if ainvs not in models:
            models[ainvs] = list(paths(curve, 2, 4)), list(paths(curve, 3, 3))
        two, three = models[ainvs]
        for j, edges3 in enumerate(three):
            if [js[0], *(edge['target_j'] for edge in edges3)] != js:
                continue
            for i, edges2 in enumerate(two):
                evaluations += 1
                output = forward.one(P, list(ainvs), edges2, edges3, coord, intermediate)
                assert len(output['B_candidates']) == 1
                b = output['B_candidates'][0]
                assert b is not None
                x, y = b
                e = ((pow(x, 3, P)-64)*pow(x*x, -1, P) % P,
                     y*(pow(x, 3, P)+128)*pow(x, -3, P) % P)
                key = (*e, *b)
                if key in targets:
                    matches += 1
                    label = ('j0_base' if js[0] == 0 else
                             'j1728_base' if js[0] == 1728 % P else 'generic')
                    generated[(*c, *key)].add((label, ainvs, i, j))
                else:
                    unmatched.append({'C_point': list(c), 'source_ainvs': list(ainvs),
                                      'pair': [i, j], 'B_point': b})
        if count % 25 == 0:
            print(json.dumps({'C_points_completed': count, 'evaluations': evaluations,
                              'matches': matches}), flush=True)
    rows = []
    for c, targets in sorted(triples_by_c.items()):
        for target, pair in sorted(targets.items()):
            chains = sorted(generated.get((*c, *target), set()))
            rows.append({'C_point': list(c), 'E_point': pair['E_point'],
                         'B_point': pair['B_point'],
                         'chain_candidates': [{'source_label': label,
                                               'source_ainvs': list(ainvs), 'pair': [i, j]}
                                              for label, ainvs, i, j in chains]})
    shards = []
    for offset in range(0, len(rows), 250):
        path = HERE/f'holdout-candidates-{offset//250:02d}.json'
        block = rows[offset:offset+250]
        path.write_text(json.dumps(block, sort_keys=True, separators=(',', ':'))+'\n')
        shards.append({'file': path.name, 'rows': len(block),
                       'sha256': sha256(path.read_bytes()).hexdigest()})
    gcd_path = HERE/'holdout_gcd_rows.json'
    gcd_path.write_text(json.dumps(gcd_rows, sort_keys=True, separators=(',', ':'))+'\n')
    histogram = dict(sorted(Counter(len(row['chain_candidates']) for row in rows).items()))
    predictions = json.loads((HERE/'prediction_result.json').read_text())
    assert predictions['protocol_sha256'] == sha256((HERE/'prediction_protocol.json').read_bytes()).hexdigest()
    expected_j1728 = {(*row['C_point'], *row['E_point'], *row['B_point']): row['predicted_multiplicity']
                      for row in predictions['predictions']}
    prediction_failures = []
    jacobian_mismatches = []
    for row in rows:
        key = (*row['C_point'], *row['E_point'], *row['B_point'])
        prior = next(r for r in pairs if r['C_point'] == row['C_point'] and r['E_point'] == row['E_point'])
        actual_count = len(row['chain_candidates'])
        if key in expected_j1728 and actual_count != expected_j1728[key]:
            prediction_failures.append({'C_point': row['C_point'], 'E_point': row['E_point'],
                                        'B_point': row['B_point'],
                                        'expected_count': expected_j1728[key], 'actual_count': actual_count})
        jacobian_expected = 2 if prior['predicted_double'] else 1
        if actual_count != jacobian_expected:
            jacobian_mismatches.append({'C_point': row['C_point'], 'E_point': row['E_point'],
                                        'B_point': row['B_point'],
                                        'jacobian_expected': jacobian_expected, 'actual_count': actual_count})
    assert len(expected_j1728) == len(predictions['predictions'])
    result = {'status': 'PASS_P1367_J1728_27_PATH_PREDICTION' if
              not prediction_failures and not unmatched else 'FAIL_P1367_J1728_27_PATH_PREDICTION',
              'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
              'screen_result_sha256': sha256(screen_path.read_bytes()).hexdigest(),
              'source_code_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
              'input_pairs': len(pairs), 'valid_triples': len(rows),
              'C_points': len(triples_by_c), 'source_models': len(models),
              'gcd_degree_candidate_histogram': [{'gcd_degree': degree,
                                                  'B_candidates': candidates, 'count': count}
                                                 for (degree, candidates), count in sorted(gcd_hist.items())],
              'gcd_rows_sha256': sha256(gcd_path.read_bytes()).hexdigest(),
              'raw_forward_evaluations': evaluations, 'matched_raw': matches,
              'unmatched_outputs': unmatched,
              'prediction_failures': prediction_failures,
              'jacobian_baseline_mismatches': jacobian_mismatches,
              'j1728_predicted_triples': len(expected_j1728),
              'sign_branch_triples': sum(row['B_point'][1] == 0 for row in rows),
              'candidate_count_histogram': histogram, 'shards': shards}
    (HERE/'holdout_result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({key: result[key] for key in ('status', 'valid_triples',
                                                  'raw_forward_evaluations', 'matched_raw',
                                                  'candidate_count_histogram')}, sort_keys=True))


if __name__ == '__main__':
    main()
