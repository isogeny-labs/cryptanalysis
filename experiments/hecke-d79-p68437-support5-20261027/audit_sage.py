"""Exhaustive 10,528,128-pattern-per-arm Sage audit of support-five rows."""
import hashlib
import itertools
import json
import resource
import time
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())
POST = json.loads((HERE / 'post_run.json').read_text())


def pinned(name):
    item = PLAN['frozen'][name]
    raw = (ROOT / item['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != item['sha256']:
        raise ValueError('PARENT_PIN_MISMATCH:' + name)
    return json.loads(raw)


def sparse(raw):
    return {int(k): int(v) for k, v in raw.items() if v}


def rank(rows, field):
    return int(matrix(field, len(rows), 40,
                      lambda i, j: rows[i].get(j, 0)).rank()) if rows else 0


def exhaustive(terms):
    neg = [-P for P in terms]
    pairs = {(l, m, d, e): (terms[l] if d == 1 else neg[l]) +
             (terms[m] if e == 1 else neg[m])
             for l, m in itertools.combinations(range(40), 2)
             for d, e in itertools.product((-1, 1), repeat=2)}
    found = set()
    count = 0
    for i, j, k, l, m in itertools.combinations(range(40), 5):
        for b, c in itertools.product((-1, 1), repeat=2):
            left = (terms[i] + (terms[j] if b == 1 else neg[j]) +
                    (terms[k] if c == 1 else neg[k]))
            for d, e in itertools.product((-1, 1), repeat=2):
                count += 1
                if left == -pairs[l, m, d, e]:
                    found.add(((i, j, k, l, m), (1, b, c, d, e)))
    return found, count


def main():
    raw = (HERE/'result.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != POST['result_sha256']:
        raise ValueError('RESULT_PIN_MISMATCH')
    result = json.loads(raw)
    cls = next(x for x in pinned('class-result.json')['cases'] if x['p'] == PLAN['p'])
    src = next(x for x in pinned('source-result.json')['cases'] if x['p'] == PLAN['p'])
    prior = next(x for x in pinned('analysis.json')['cases'] if x['p'] == PLAN['p'])
    if pinned('audit.json')['status'] != 'PASS':
        raise ValueError('PARENT_AUDIT_NOT_PASS')
    E = EllipticCurve(GF(PLAN['p']), [0, -1, 1, -10, -20])
    if int(E.cardinality()) != PLAN['curve_order']:
        raise ValueError('CURVE_ORDER_MISMATCH')
    points = [E(x, y) for x, y in cls['class_points']]
    totals = [sum((E(x, y) for x, y in item['outside_traces']), E(0))
              for item in src['degree13_sources']]
    baseline = [sparse(x['row']) for x in cls['base_rows']]
    baseline += [sparse(x['row']) for x in prior['direct_candidates']]
    baseline += [sparse(x['row']) for x in prior['hecke_candidates']]
    if rank(baseline, QQ) != 34 or rank(baseline, GF(109)) != 34:
        raise ValueError('BASELINE_RANK_MISMATCH')
    out = {'schema': 'hecke-d79-p68437-support5-audit-v1',
           'status': 'RUNNING', 'arms': {}, 'curve_order': int(E.cardinality()),
           'nonzero_q_projection_points': sum((PLAN['curve_order']//109)*P != E(0)
                                              for P in points)}
    path = HERE/'audit.json'
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    new_rows = {}
    for label, terms in [('direct', points), ('hecke', totals)]:
        t0 = time.perf_counter_ns()
        found, trials = exhaustive(terms)
        wall_ns = time.perf_counter_ns() - t0
        expected = result['arms'][label]['candidates']
        key = 'indices' if label == 'direct' else 'sources'
        expected_set = {(tuple(x[key]), tuple(x['coefficients'])) for x in expected}
        if found != expected_set or trials != 10528128:
            raise ValueError('EXHAUSTIVE_SET_MISMATCH:' + label)
        rows = []
        for item in expected:
            inds, signs = item[key], item['coefficients']
            if label == 'direct':
                computed = dict(zip(inds, signs))
            else:
                computed = Counter()
                for source, sign in zip(inds, signs):
                    for i, coeff in sparse(src['degree13_sources'][source]['class_part']).items():
                        computed[i] += sign*coeff
                computed = {i: coeff for i, coeff in computed.items() if coeff}
            row = sparse(item['row'])
            if row != computed or sum((coeff*points[i] for i, coeff in row.items()), E(0)) != E(0):
                raise ValueError('ROW_GROUP_MISMATCH:' + label)
            rows.append(row)
        qq = rank(baseline+rows, QQ)
        qrank = rank(baseline+rows, GF(109))
        if (qq, qrank) != (result['arms'][label]['rank_qq'], result['arms'][label]['rank_mod_q']):
            raise ValueError('ARM_RANK_MISMATCH:' + label)
        new_rows[label] = rows
        out['arms'][label] = {'status': 'PASS', 'patterns': trials,
                              'candidates': len(found), 'rank_qq': qq,
                              'rank_mod_q': qrank, 'wall_ns': wall_ns}
        path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
        print(json.dumps({'arm': label, 'status': 'PASS', 'patterns': trials,
                          'candidates': len(found)}), flush=True)
    both = baseline+new_rows['direct']+new_rows['hecke']
    if (rank(both, QQ), rank(both, GF(109))) != (
            result['combined_rank_qq'], result['combined_rank_mod_q']):
        raise ValueError('COMBINED_RANK_MISMATCH')
    out['combined_rank_qq'], out['combined_rank_mod_q'] = rank(both, QQ), rank(both, GF(109))
    out['peak_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    out['status'] = 'PASS'
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': 'PASS', 'combined_rank_qq': out['combined_rank_qq'],
                      'combined_rank_mod_q': out['combined_rank_mod_q']}))


if __name__ == '__main__':
    main()
