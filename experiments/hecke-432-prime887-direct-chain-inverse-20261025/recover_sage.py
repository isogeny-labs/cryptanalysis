"""Recover all p887 kernel chains directly from rational C,E,B triples.

The corrected source census is audit-only and is never loaded here.
"""
import importlib.util
import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'
from sage.all import EllipticCurve, EllipticCurve_from_j, GF, PolynomialRing, QQ

HERE = Path(__file__).resolve().parent
P = 887


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def j_value(record, c, field):
    xc, yc = (field(a) for a in c)
    def value(terms):
        return sum((field(QQ(term['coefficient'])) * xc**term['x_power']
                    * yc**term['y_power'] for term in terms), field(0))
    denominator = value(record['denominator'])
    assert denominator
    return int(-value(record['numerator'])/denominator)


def models_for_j(j, field, primitive):
    j = field(j)
    if j == 0:
        # The j=0 base and twist paths represent the same coarse source orbits.
        return [('j0_base', EllipticCurve(field, [0, 0, 0, 0, 1]))]
    if j == field(1728):
        return [('j1728_base', EllipticCurve(field, [0, 0, 0, 1, 0])),
                ('j1728_twist', EllipticCurve(field, [0, 0, 0, primitive, 0]))]
    return [('generic', EllipticCurve_from_j(j))]


def special_orbit_map(curve, two, three, kernel, extension):
    ring = PolynomialRing(extension, 'x')
    x = ring.gen()
    p2 = [ring(kernel.chain(curve, edges)[0].kernel_polynomial().monic())
          for edges in two]
    p3 = [ring(kernel.chain(curve, edges)[0].kernel_polynomial().monic())
          for edges in three]
    records = {(i, j): (a, b) for i, a in enumerate(p2) for j, b in enumerate(p3)}
    unseen = set(records)
    canonical = {}
    while unseen:
        representative = min(unseen)
        a2, a3 = records[representative]
        orbit = {pair for pair, (b2, b3) in records.items()
                 if b2 == a2(x/-extension(1)).monic()
                 and b3 == a3(x/-extension(1)).monic()}
        orbit.add(representative)
        assert orbit <= unseen and len(orbit) == 2
        for pair in orbit:
            canonical[pair] = representative
        unseen.difference_update(orbit)
    assert len(canonical) == len(records)
    return canonical


def e_image(b):
    x, y = b
    assert x
    return ((pow(x, 3, P)-64)*pow(x*x, -1, P) % P,
            y*(pow(x, 3, P)+128)*pow(x, -3, P) % P)


def main():
    protocol_path = HERE/'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_DIRECT_P887_CHAIN_INVERSE'
    for name, record in protocol['inputs'].items():
        path = Path(record['path'])
        assert sha256(path.read_bytes()).hexdigest() == record['sha256']
    assert all(name.startswith('audit_') for name in protocol['audit_only_inputs'])
    inputs = {name: json.loads(Path(record['path']).read_text())
              for name, record in protocol['inputs'].items()
              if name not in protocol['audit_only_inputs'] and Path(record['path']).suffix == '.json'}
    paths = load_module('direct_inverse_paths', Path(protocol['inputs']['path_enumerator']['path'])).paths
    forward = load_module('direct_inverse_forward', Path(protocol['inputs']['forward_evaluator']['path']))
    kernel = load_module('direct_inverse_kernel', Path(protocol['inputs']['kernel_transport']['path']))
    field = GF(P)
    extension = GF(P**2, 'u')
    primitive = field.multiplicative_generator()
    coord, intermediate = inputs['coordinate'], inputs['intermediate']
    pair_rows = []
    for i in range(4):
        pair_rows.extend(inputs[f'gcd_{i:02d}'])
    assert len(pair_rows) == inputs['gcd_result']['primes'][str(P)]['pair_count'] == 872
    target_by_c = defaultdict(dict)
    for row in pair_rows:
        c = tuple(row['C_point'])
        key = (*row['E_point'], *row['B_candidates'][0]) if row['B_candidates'] else None
        if key is not None:
            assert key not in target_by_c[c]
            target_by_c[c][key] = row
    assert sum(map(len, target_by_c.values())) == 864
    generated = defaultdict(set)
    raw_evaluations = 0
    matched_raw = 0
    unmatched_outputs = []
    model_cache = {}
    for count, (c, target_keys) in enumerate(sorted(target_by_c.items()), 1):
        js = [j_value(record, c, field) for record in
              (coord['source_j'], intermediate['j3'], intermediate['j9'], coord['target_j'])]
        for label, curve in models_for_j(js[0], field, primitive):
            ainvs = tuple(int(a) for a in curve.ainvs())
            model_key = (label, ainvs)
            if model_key not in model_cache:
                two = list(paths(curve, 2, 4))
                three = list(paths(curve, 3, 3))
                orbit = (special_orbit_map(curve, two, three, kernel, extension)
                         if label.startswith('j1728') else
                         {(i, j): (i, j) for i in range(len(two)) for j in range(len(three))})
                model_cache[model_key] = (two, three, orbit)
            two, three, orbit = model_cache[model_key]
            for j, edges3 in enumerate(three):
                if [js[0], *(edge['target_j'] for edge in edges3)] != js:
                    continue
                for i, edges2 in enumerate(two):
                    raw_evaluations += 1
                    value = forward.one(P, list(ainvs), edges2, edges3, coord, intermediate)
                    assert len(value['B_candidates']) == 1
                    b = value['B_candidates'][0]
                    assert b is not None
                    target_key = (*e_image(b), *b)
                    if target_key in target_keys:
                        matched_raw += 1
                        ii, jj = orbit[(i, j)]
                        generated[(*c, *target_key)].add((label, ainvs, ii, jj))
                    else:
                        unmatched_outputs.append({'C_point': list(c), 'source_label': label,
                                                  'source_ainvs': list(ainvs), 'pair': [i, j],
                                                  'B_point': b, 'E_point': list(e_image(b))})
        if count % 25 == 0:
            print(json.dumps({'C_points_completed': count, 'raw_evaluations': raw_evaluations,
                              'matched_raw': matched_raw}), flush=True)
    out_rows = []
    for c, targets in sorted(target_by_c.items()):
        for target, row in sorted(targets.items()):
            key = (*c, *target)
            keys = sorted(generated.get(key, set()))
            out_rows.append({'C_point': list(c), 'E_point': row['E_point'],
                             'B_point': row['B_candidates'][0],
                             'chain_candidates': [{'source_label': label,
                                                   'source_ainvs': list(ainvs),
                                                   'pair': [i, j]}
                                                  for label, ainvs, i, j in keys]})
    shards = []
    for offset in range(0, len(out_rows), 250):
        path = HERE/f'candidates-{offset//250:02d}.json'
        block = out_rows[offset:offset+250]
        path.write_text(json.dumps(block, sort_keys=True, separators=(',', ':'))+'\n')
        shards.append({'file': path.name, 'rows': len(block),
                       'sha256': sha256(path.read_bytes()).hexdigest()})
    candidate_hist = dict(sorted(Counter(len(row['chain_candidates']) for row in out_rows).items()))
    result = {'status': 'COMPLETE_DIRECT_P887_CHAIN_INVERSE' if 0 not in candidate_hist and not unmatched_outputs else 'PARTIAL_DIRECT_P887_CHAIN_INVERSE',
              'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
              'source_code_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
              'input_pairs': len(pair_rows), 'valid_triples': len(out_rows),
              'C_points': len(target_by_c), 'source_models_enumerated': len(model_cache),
              'raw_forward_evaluations': raw_evaluations, 'matched_raw': matched_raw,
              'unmatched_outputs': unmatched_outputs,
              'candidate_count_histogram': candidate_hist, 'shards': shards}
    (HERE/'result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({key: result[key] for key in ('status', 'valid_triples', 'C_points',
                                                  'raw_forward_evaluations', 'matched_raw',
                                                  'candidate_count_histogram')}, sort_keys=True))


if __name__ == '__main__':
    main()
