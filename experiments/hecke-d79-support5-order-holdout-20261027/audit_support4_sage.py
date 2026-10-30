"""Independent Sage class, group-law, candidate and rank audit."""
import hashlib
import importlib.util
import itertools
import json
from collections import Counter
from pathlib import Path

from sage.all import (EllipticCurve_from_j, GF, QQ, classical_modular_polynomial,
                      hilbert_class_polynomial, matrix)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())
POST_CLASS = json.loads((HERE / 'post_class.json').read_text())
POST_SOURCE = json.loads((HERE / 'post_source.json').read_text())
POST_ANALYSIS = json.loads((HERE / 'post_analysis.json').read_text())


def pinned(path, sha):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != sha:
        raise ValueError('PIN_MISMATCH:' + str(path))
    return json.loads(raw)


def sparse(raw):
    return {int(k): int(v) for k, v in raw.items() if v}


def rank(rows, field):
    return int(matrix(field, len(rows), 40,
                      lambda i, j: rows[i].get(j, 0)).rank()) if rows else 0


def main():
    classes = pinned(HERE/'class-result.json', POST_CLASS['sha256']['class_result'])
    sources = pinned(HERE/'source-result.json', POST_SOURCE['sha256']['source_result'])
    analysis = pinned(HERE/'analysis.json', POST_ANALYSIS['sha256']['analysis.json'])
    source_path = ROOT / PLAN['source_path']
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != PLAN['source_sha256']:
        raise ValueError('SOURCE_MISMATCH')
    spec = importlib.util.spec_from_file_location('hecke_d79_priority_audit', source_path)
    H = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(H)
    prefix_path = ROOT / PLAN['prefix_runner_path']
    if hashlib.sha256(prefix_path.read_bytes()).hexdigest() != PLAN['prefix_runner_sha256']:
        raise ValueError('PREFIX_RUNNER_MISMATCH')
    prefix_spec = importlib.util.spec_from_file_location('hecke_d79_priority_fiber_audit', prefix_path)
    Prefix = importlib.util.module_from_spec(prefix_spec)
    prefix_spec.loader.exec_module(Prefix)
    funcs, jfun = H.build([13])
    modpoly = classical_modular_polynomial(13)
    receipts = []
    for frozen in classes['cases']:
        p, v = frozen['p'], frozen['v']
        saved = next(x for x in sources['cases'] if x['p'] == p)
        measured = next(x for x in analysis['cases'] if x['p'] == p)
        R = H.Reduced(p, funcs, jfun, [13])
        E, Fp = R.E, R.Fp
        if int(E.cardinality()) != frozen['curve_order']:
            raise ValueError('CURVE_ORDER_MISMATCH')
        class_set = set()
        strata = []
        for f in (1, 2, 4):
            pts = set()
            for root in hilbert_class_polynomial(-79*f*f).change_ring(Fp).roots(multiplicities=False):
                j = int(root)
                if j in (0, 1728 % p):
                    continue
                if abs(int(EllipticCurve_from_j(Fp(j)).trace_of_frobenius())) == 2*v:
                    pts.update((int(P[0]), int(P[1])) for P in R.points_with_j(Fp(j)))
            class_set |= pts
            strata.append({'conductor': f, 'points': len(pts)})
        if class_set != {tuple(x) for x in frozen['class_points']} or len(class_set) != 40:
            raise ValueError('CLASS_SET_MISMATCH')
        points = [E(x, y) for x, y in frozen['class_points']]
        projected = [(frozen['curve_order']//5)*P for P in points]
        T = next((Q for Q in projected if Q != E(0)), None)
        if T is None:
            residues = [0]*40
        else:
            lookup = {k*T: k for k in range(5)}
            residues = [lookup[Q] for Q in projected]
        if residues != frozen['projection_residues']:
            raise ValueError('PROJECTION_MISMATCH')
        buckets = {r: [i for i, x in enumerate(residues) if x == r]
                   for r in sorted(set(residues))}
        priority = [bucket[offset] for offset in range(max(map(len, buckets.values())))
                    for r, bucket in sorted(buckets.items()) if offset < len(bucket)]
        if priority != frozen['priority_order']:
            raise ValueError('PRIORITY_ORDER_MISMATCH')
        base = [sparse(x['row']) for x in frozen['base_rows']]
        for row in base:
            if sum((coeff*points[i] for i, coeff in row.items()), E(0)) != E(0):
                raise ValueError('BASE_GROUP_MISMATCH')
        totals = []
        fiber_cache = {}
        for item in saved['degree13_sources']:
            point = points[item['source']]
            pattern = [[int(f.degree()), int(mult)] for f, mult in R.neighbour_x(13, point).factor()]
            if pattern != item['factor_pattern'] or item['status'] != 'OUTSIDE_CLASS_TRACE':
                raise ValueError('SOURCE_PATTERN_OR_STATUS_MISMATCH')
            replayed, _ = Prefix.lift_source(item['source'], point, R, jfun,
                                             points, {}, fiber_cache, modpoly, pattern)
            if replayed != {k: value for k, value in item.items() if k != 'lift_wall_ns'}:
                raise ValueError('FIBER_REPLAY_MISMATCH')
            if sum(x['size'] for x in item['orbits']) != 14:
                raise ValueError('ORBIT_SIZE_MISMATCH')
            total = sum((E(x, y) for x, y in item['outside_traces']), E(0))
            row_total = sum((coeff*points[i] for i, coeff in sparse(item['class_part']).items()), E(0))
            if total + row_total != E(0):
                raise ValueError('SOURCE_GROUP_MISMATCH')
            totals.append(total)
        def pair_sums(terms):
            return {(i, j, a, b): a*terms[i] + b*terms[j]
                    for i in range(40) for j in range(i+1, 40)
                    for a in (-1, 1) for b in (-1, 1)}
        direct_pairs, hecke_pairs = pair_sums(points), pair_sums(totals)
        def zero(terms, pairs, inds, signs):
            if len(inds) == 1:
                return terms[inds[0]] == E(0)
            if len(inds) == 2:
                return pairs[inds[0], inds[1], signs[0], signs[1]] == E(0)
            left = pairs[inds[0], inds[1], signs[0], signs[1]]
            if len(inds) == 3:
                return left == -signs[2]*terms[inds[2]]
            right = pairs[inds[2], inds[3], signs[2], signs[3]]
            return left == -right
        direct, hecke = [], []
        for support in range(1, 5):
            for inds in itertools.combinations(range(40), support):
                for rest in itertools.product((-1, 1), repeat=support-1):
                    signs = (1,) + rest
                    if zero(points, direct_pairs, inds, signs):
                        direct.append({'indices': list(inds), 'coefficients': list(signs),
                                       'row': {str(i): s for i, s in zip(inds, signs)}})
                    if zero(totals, hecke_pairs, inds, signs):
                        row = Counter()
                        for i, s in zip(inds, signs):
                            for k, coeff in sparse(saved['degree13_sources'][i]['class_part']).items():
                                row[k] += s*coeff
                        hecke.append({'sources': list(inds), 'coefficients': list(signs),
                                      'row': {str(k): coeff for k, coeff in sorted(row.items()) if coeff}})
        if direct != measured['direct_candidates'] or hecke != measured['hecke_candidates']:
            raise ValueError('CANDIDATE_SET_MISMATCH')
        baseline = base + [sparse(x['row']) for x in direct]
        if rank(baseline, QQ) != measured['direct_baseline_rank_qq']:
            raise ValueError('BASELINE_RANK_MISMATCH')
        for label in ('ascending', 'priority'):
            seen = set()
            steps = measured['paths'][label]['steps']
            for step in steps:
                seen.add(step['source'])
                rows = baseline + [sparse(x['row']) for x in hecke if set(x['sources']) <= seen]
                if (rank(rows, QQ) != step['rank_qq'] or
                    rank(rows, GF(frozen['largest_prime_factor'])) != step['rank_mod_q']):
                    raise ValueError('RANK_PATH_MISMATCH')
        receipts.append({'p': p, 'status': 'PASS', 'strata': strata,
                         'class_points': len(points), 'degree13_sources': len(totals),
                         'direct_candidates': len(direct), 'hecke_candidates': len(hecke),
                         'ascending_final_rank': measured['paths']['ascending']['steps'][-1]['rank_qq'],
                         'priority_final_rank': measured['paths']['priority']['steps'][-1]['rank_qq']})
        print(json.dumps({'p': p, 'status': 'PASS', 'direct': len(direct),
                          'hecke': len(hecke)}), flush=True)
    out = {'schema': 'hecke-d79-priority-sage-audit-v1', 'status': 'PASS', 'cases': receipts}
    (HERE/'audit-support4.json').write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
