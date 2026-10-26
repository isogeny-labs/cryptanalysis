"""Independent Sage root factorization and source-image audit at three primes."""
import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'
from sage.all import EllipticCurve, GF, PolynomialRing, QQ
from inverse_filter import evaluate_pair

HERE = Path(__file__).resolve().parent


def map_value(record, point, field):
    def polynomial(terms):
        return sum((field(QQ(t['coefficient'])) * point[0]**t['x_power']
                    * point[1]**t['y_power'] for t in terms), field(0))
    denominator = polynomial(record['denominator'])
    return None if denominator == 0 else int(-polynomial(record['numerator']) / denominator)


def branch_value(terms, cp, xe, field):
    return sum((field(int(t['integer_coefficient']))
                * cp[0]**t['x_C_exponent'] * cp[1]**t['y_C_exponent']
                * xe**t['x_E_exponent'] for t in terms), field(0))


def image_e(b, field):
    x, y = (field(a) for a in b)
    assert x != 0
    return (int((x**3-64)/x**2), int(y*(x**3+128)/x**3))


def source_pairs(p, field, c_points, inputs):
    out = defaultdict(list)
    if p == 997:
        index_to_b = {}
        for fiber in inputs['p997_fibers']['fibers']:
            for index in fiber['source_indices']:
                assert index not in index_to_b
                index_to_b[index] = fiber['B_point']
        rows = inputs['p997_pairs']['rows']
        assert len(rows) == len(index_to_b) == 1800
        for index, row in enumerate(rows):
            key = (*row['C_point'], *row['E_point'])
            out[key].append(index_to_b[index])
        return out, len(rows)

    maps = inputs['coordinate']
    intermediate = inputs['intermediate']
    by_js = defaultdict(list)
    for cp in c_points:
        js = tuple(map_value(record, cp, field) for record in
                   (maps['source_j'], intermediate['j3'], intermediate['j9'], maps['target_j']))
        by_js[js].append((int(cp[0]), int(cp[1])))
    if p == 883:
        models = {tuple(row['curve_ainvs']): row for row in inputs['p883_census']['rows']}
        rows = inputs['p883_image']['rows']
        for row in rows:
            model = models[tuple(row['source_ainvs'])]
            _, j = row['pair']
            js = (model['j'], *(edge['target_j'] for edge in model['three_paths'][j]))
            assert len(by_js[js]) == 1 and len(row['B_points']) == 1
            b = row['B_points'][0]
            out[(*by_js[js][0], *image_e(b, field))].append(b)
    else:
        models = {(tuple(row['curve_ainvs']), row['label']): row
                  for row in inputs['p887_census']['rows']}
        rows = sum((inputs[f'p887_rows_{i:02d}'] for i in range(4)), [])
        for row in rows:
            model = models[(tuple(row['source_ainvs']), row['source_label'])]
            _, j = row['pair']
            js = (model['j'], *(edge['target_j'] for edge in model['three_paths'][j]))
            assert len(by_js[js]) == 1
            b = row['B_point']
            out[(*by_js[js][0], *image_e(b, field))].append(b)
    return out, len(rows)


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    inputs = {}
    for name, record in protocol['inputs'].items():
        path = Path(record['path'])
        assert sha256(path.read_bytes()).hexdigest() == record['sha256']
        inputs[name] = json.loads(path.read_text())
    produced = json.loads((HERE/'result.json').read_text())
    assert produced['protocol_sha256'] == sha256(protocol_path.read_bytes()).hexdigest()
    audit = {'status': 'PASS_CROSSPRIME_SAGE_AND_SOURCE_AUDIT', 'primes': {}}
    for p in protocol['primes']:
        field = GF(p)
        curve_c = EllipticCurve(field, [0, 0, 1, 0, -7])
        curve_e = EllipticCurve(field, [0, 0, 0, 0, 432])
        c_points = [point for point in curve_c.points() if not point.is_zero()]
        ring = PolynomialRing(field, 'T')
        T = ring.gen()
        terms_by_exponent = [[] for _ in range(13)]
        for term in inputs['resolvent']['terms']:
            terms_by_exponent[term['x_E_exponent']].append(term)
        seen = {}
        for cp in c_points:
            coeffs = [branch_value(terms, cp, field(1), field)
                      for terms in terms_by_exponent]
            polynomial = sum((a*T**i for i, a in enumerate(coeffs)), ring.zero())
            assert polynomial != 0
            for xe, multiplicity in polynomial.roots():
                for ep in curve_e.lift_x(xe, all=True):
                    key = (int(cp[0]), int(cp[1]), int(ep[0]), int(ep[1]))
                    numerator = branch_value(inputs['branch']['numerator_terms'], cp, xe, field)
                    denominator = branch_value(inputs['branch']['denominator_terms'], cp, xe, field)
                    if denominator == 0:
                        value = {'status': 'ZERO_DENOMINATOR', 'numerator': int(numerator)}
                    else:
                        xb = numerator / denominator
                        yden = xb**3+128
                        if xb == 0 or yden == 0:
                            value = {'status': 'Y_INVERSE_UNDEFINED', 'x_B': int(xb)}
                        else:
                            yb = ep[1]*xb**3/yden
                            value = ({'status': 'VALID', 'B_point': [int(xb), int(yb)]}
                                     if yb**2 == xb**3-16 and xe*xb**2 == xb**3-64
                                     else {'status': 'BRANCH_EQUATION_FAILURE',
                                           'B_point': [int(xb), int(yb)]})
                    assert key not in seen
                    seen[key] = value
        saved = {}
        for shard in produced['primes'][str(p)]['pair_shards']:
            path = HERE / shard['file']
            assert sha256(path.read_bytes()).hexdigest() == shard['sha256']
            block = json.loads(path.read_text())
            assert len(block) == shard['rows']
            for row in block:
                key = (*row['C_point'], *row['E_point'])
                assert key not in saved
                saved[key] = {k: v for k, v in row.items() if k not in ('C_point', 'E_point')}
        assert seen == saved
        assert all(evaluate_pair(key[:2], key[2:], p,
                                 inputs['resolvent'], inputs['branch']) == value
                   for key, value in seen.items())
        assert evaluate_pair((0, 0), (0, 0), p,
                             inputs['resolvent'], inputs['branch'])['status'] == 'POINT_OFF_CURVE'
        c_control = (int(c_points[0][0]), int(c_points[0][1]))
        assert any(evaluate_pair(c_control, (int(ep[0]), int(ep[1])), p,
                                 inputs['resolvent'], inputs['branch'])['status'] == 'NOT_RESOLVENT_ROOT'
                   for ep in curve_e.points() if not ep.is_zero())
        sources, source_count = source_pairs(p, field, c_points, inputs)
        valid = {key: row['B_point'] for key, row in seen.items() if row['status'] == 'VALID'}
        assert set(valid) == set(sources)
        assert all(tuple(valid[key]) in {tuple(b) for b in values}
                   for key, values in sources.items())
        extras = sorted(set(seen)-set(sources))
        audit['primes'][str(p)] = {
            'C_group_order': int(curve_c.cardinality()),
            'E_group_order': int(curve_e.cardinality()),
            'resolvent_pairs': len(seen), 'valid_pairs': len(valid),
            'source_chains': source_count, 'source_pairs': len(sources),
            'source_pair_multiplicity_histogram': dict(sorted(Counter(map(len, sources.values())).items())),
            'status_histogram': dict(sorted(Counter(row['status'] for row in seen.values()).items())),
            'extra_resolvent_pairs': [list(key) for key in extras],
            'missing_valid_source_pairs': 0, 'incorrect_B_branches': 0}
        print(json.dumps({'prime': p, **{k: audit['primes'][str(p)][k] for k in
                          ('resolvent_pairs', 'valid_pairs', 'source_chains', 'source_pairs')}},
                         sort_keys=True), flush=True)
    (HERE/'audit.json').write_text(json.dumps(audit, sort_keys=True, indent=2)+'\n')


if __name__ == '__main__':
    main()
