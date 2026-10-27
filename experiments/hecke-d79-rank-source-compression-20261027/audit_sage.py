"""Independent checked-Sage matrix and group replay of rank compression."""
import hashlib
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, matrix, vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())
POST = json.loads((HERE / 'post-run.json').read_text())


def pinned(name):
    item = PLAN['frozen'][name]
    raw = (ROOT / item['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == item['sha256']
    return json.loads(raw)


def row(item):
    return [int(item['row'].get(str(j), 0)) for j in range(40)]


def main():
    raw = (HERE / 'result.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == POST['result_sha256']
    result = json.loads(raw)
    assert pinned('parent-audit.json')['status'] == 'PASS'
    cls = pinned('class-result.json')
    analysis = pinned('analysis.json')
    source = pinned('source-result.json')
    logs = pinned('class-logs.json')
    audited = []
    for item in result['cases']:
        p, q = item['p'], item['q']
        c = next(x for x in cls['cases'] if x['p'] == p)
        a = next(x for x in analysis['cases'] if x['p'] == p)
        s = next(x for x in source['cases'] if x['p'] == p)
        F = GF(q)
        baseline_rows = [row(x) for x in c['base_rows'] + a['direct_candidates']]
        hecke_rows = [row(x) for x in a['hecke_candidates']]
        B = matrix(F, baseline_rows)
        H = matrix(F, hecke_rows)
        selected = [a['hecke_candidates'][i] for i in item['selected_candidate_indices']]
        S = matrix(F, [row(x) for x in selected])
        assert int(B.rank()) == item['baseline_rank']
        assert int(B.stack(H).rank()) == item['full_pool_rank']
        assert int(B.stack(S).rank()) == item['full_pool_rank']
        assert selected == item['selected_rows']
        union = sorted(set().union(*(x['sources'] for x in selected)))
        assert union == item['selected_sources']
        assert sum(s['degree13_sources'][i]['lift_wall_ns'] for i in union) == item['selected_source_lift_ns']
        E = EllipticCurve(GF(p), [0, -1, 1, -10, -20])
        assert int(E.cardinality()) == c['curve_order']
        points = [E(x, y) for x, y in c['class_points']]
        assert all(sum((v * points[i] for i, v in enumerate(row(x))), E(0)) == E(0)
                   for x in selected)
        if p == 63317:
            # Every four-source set is unique in the frozen pool; no pair can use four sources.
            supports = [frozenset(x['sources']) for x in a['hecke_candidates']]
            assert all(len(v) == 4 for v in supports)
            assert len(set(supports)) == len(supports)
            assert not any(len(x | y) == 4 for x, y in itertools.combinations(supports, 2))
            assert item['selected_source_count'] == 5
            anchor = logs['anchor_index']
            M = B.stack(S)
            anchor_row = matrix(F, 1, 40, lambda _, j: int(j == anchor))
            assert int(M.rank()) == 39 and int(M.stack(anchor_row).rank()) == 40
            rhs = vector(F, [0]*M.nrows() + [1])
            solved = [int(x) for x in M.stack(anchor_row).solve_right(rhs)]
            assert solved == logs['q_logs']
            assert H * vector(F, solved) == vector(F, [0]*H.nrows())
            recovered = True
        else:
            assert int(B.stack(H).rank()) == 34 and item['remaining_rank_deficit'] == 6
            assert item['selected_source_count'] == 4
            recovered = False
        audited.append({'p': p, 'q': q, 'baseline_rank': int(B.rank()),
                        'full_pool_rank': int(B.stack(H).rank()),
                        'selected_rank': int(B.stack(S).rank()),
                        'selected_sources': union, 'selected_rows_group_verified': len(selected),
                        'anchored_logs_recovered': recovered})
    out = {'schema': 'hecke-d79-rank-source-compression-audit-v1',
           'status': 'PASS', 'cases': audited}
    (HERE / 'audit.json').write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': 'PASS', 'cases': audited}))


if __name__ == '__main__':
    main()
