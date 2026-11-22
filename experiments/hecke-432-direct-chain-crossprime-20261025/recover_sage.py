"""Recover p883/p997 source chains using only frozen C,E,B inverse triples."""
import importlib.util
import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'
from sage.all import EllipticCurve_from_j, GF, QQ

HERE = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def j_value(record, c, field):
    x, y = map(field, c)
    def value(terms):
        return sum((field(QQ(t['coefficient'])) * x**t['x_power'] *
                    y**t['y_power'] for t in terms), field(0))
    denominator = value(record['denominator'])
    assert denominator
    return int(-value(record['numerator']) / denominator)


def e_image(b, p):
    x, y = b
    assert x
    return ((pow(x, 3, p) - 64) * pow(x*x, -1, p) % p,
            y * (pow(x, 3, p) + 128) * pow(x, -3, p) % p)


def source_model(j, p, field):
    curve = EllipticCurve_from_j(field(j))
    if p == 997:
        return 'generic', curve
    trace = p + 1 - curve.cardinality()
    if trace in (20, 52):
        return 'base', curve
    curve = curve.quadratic_twist(field.multiplicative_generator())
    assert p + 1 - curve.cardinality() in (20, 52)
    return 'quadratic_twist', curve


def main():
    protocol_path = HERE/'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_CROSSPRIME_DIRECT_CHAIN_INVERSE'
    for name, record in protocol['inputs'].items():
        assert sha256(Path(record['path']).read_bytes()).hexdigest() == record['sha256'], name
    inputs = {name: json.loads(Path(record['path']).read_text())
              for name, record in protocol['inputs'].items()
              if name not in protocol['audit_only_inputs'] and
              Path(record['path']).suffix == '.json'}
    paths = module('direct_crossprime_paths', protocol['inputs']['path_enumerator']['path']).paths
    forward883 = module('direct_crossprime_forward883', protocol['inputs']['forward_883']['path'])
    forward997 = module('direct_crossprime_forward997', protocol['inputs']['forward_997']['path'])
    results = {}
    for p in (883, 997):
        field = GF(p)
        coord, intermediate = inputs['coordinate'], inputs[f'intermediate_{p}']
        pair_rows = [row for i in range(4 if p == 883 else 8)
                     for row in inputs[f'gcd_{p}_{i:02d}']]
        assert len(pair_rows) == inputs['gcd_result']['primes'][str(p)]['pair_count']
        target_by_c = defaultdict(dict)
        for row in pair_rows:
            assert len(row['B_candidates']) == 1
            c = tuple(row['C_point'])
            target = (*row['E_point'], *row['B_candidates'][0])
            assert target not in target_by_c[c]
            target_by_c[c][target] = row
        generated = defaultdict(set)
        models = {}
        evaluations = matches = 0
        unmatched = []
        for count, (c, targets) in enumerate(sorted(target_by_c.items()), 1):
            js = [j_value(record, c, field) for record in
                  (coord['source_j'], intermediate['j3'], intermediate['j9'], coord['target_j'])]
            label, curve = source_model(js[0], p, field)
            ainvs = tuple(map(int, curve.ainvs()))
            model_key = label, ainvs
            if model_key not in models:
                models[model_key] = list(paths(curve, 2, 4)), list(paths(curve, 3, 3))
            two, three = models[model_key]
            for j, edges3 in enumerate(three):
                if [js[0], *(edge['target_j'] for edge in edges3)] != js:
                    continue
                for i, edges2 in enumerate(two):
                    evaluations += 1
                    if p == 883:
                        value = forward883.evaluate(list(ainvs), edges2, edges3, coord)
                        outputs = [(e_image(b, p), tuple(b)) for b in value['B_points']]
                    else:
                        value = forward997.one(p, list(ainvs), edges2, edges3, coord, intermediate)
                        outputs = [(tuple(projection['E_point']), tuple(b))
                                   for projection in value['projections']
                                   for b in projection['B_preimages'] if b is not None]
                    hit = False
                    for e, b in outputs:
                        target = (*e, *b)
                        if target in targets:
                            matches += 1
                            hit = True
                            generated[(*c, *target)].add((label, ainvs, i, j))
                    if not hit:
                        unmatched.append({'C_point': list(c), 'source_ainvs': list(ainvs),
                                          'source_label': label, 'pair': [i, j]})
            if count % 25 == 0:
                print(json.dumps({'prime': p, 'C_points_completed': count,
                                  'evaluations': evaluations, 'matches': matches}), flush=True)
        rows = []
        for c, targets in sorted(target_by_c.items()):
            for target, row in sorted(targets.items()):
                chains = sorted(generated.get((*c, *target), set()))
                rows.append({'C_point': list(c), 'E_point': row['E_point'],
                             'B_point': row['B_candidates'][0],
                             'chain_candidates': [{'source_label': label,
                                                   'source_ainvs': list(ainvs), 'pair': [i, j]}
                                                  for label, ainvs, i, j in chains]})
        shards = []
        for offset in range(0, len(rows), 250):
            path = HERE/f'p{p}-candidates-{offset//250:02d}.json'
            block = rows[offset:offset+250]
            path.write_text(json.dumps(block, sort_keys=True, separators=(',', ':'))+'\n')
            shards.append({'file': path.name, 'rows': len(block),
                           'sha256': sha256(path.read_bytes()).hexdigest()})
        histogram = dict(sorted(Counter(len(r['chain_candidates']) for r in rows).items()))
        results[str(p)] = {'status': 'COMPLETE' if histogram == {1: len(rows)} and not unmatched else 'PARTIAL',
                           'input_pairs': len(pair_rows), 'valid_triples': len(rows),
                           'C_points': len(target_by_c), 'source_models': len(models),
                           'raw_forward_evaluations': evaluations, 'matched_outputs': matches,
                           'unmatched_evaluations': unmatched,
                           'candidate_count_histogram': histogram, 'shards': shards}
        print(json.dumps({'prime': p, **{k: results[str(p)][k] for k in
                          ('status', 'valid_triples', 'raw_forward_evaluations',
                           'matched_outputs', 'candidate_count_histogram')}}, sort_keys=True), flush=True)
    result = {'status': 'COMPLETE_CROSSPRIME_DIRECT_CHAIN_INVERSE' if all(
              r['status'] == 'COMPLETE' for r in results.values()) else 'PARTIAL_CROSSPRIME_DIRECT_CHAIN_INVERSE',
              'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
              'source_code_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
              'primes': results}
    (HERE/'result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')


if __name__ == '__main__':
    main()
