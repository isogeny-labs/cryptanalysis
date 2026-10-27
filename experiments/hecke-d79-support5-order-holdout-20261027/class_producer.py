"""Construct selected D79 classes and freeze prelift source orders."""
import hashlib
import importlib.util
import json
import resource
import time
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve_from_j, GF, QQ, hilbert_class_polynomial, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())
SCREEN = json.loads((HERE / 'prescreen.json').read_text())


def rank(rows, width):
    return int(matrix(QQ, len(rows), width,
                      lambda i, j: rows[i].get(j, 0)).rank())


def main():
    if SCREEN['status'] != 'COMPLETE' or len(SCREEN['selected']) != 1:
        raise ValueError('PRESCREEN_INCOMPLETE')
    source = ROOT / PLAN['source_path']
    if hashlib.sha256(source.read_bytes()).hexdigest() != PLAN['source_sha256']:
        raise ValueError('SOURCE_MISMATCH')
    spec = importlib.util.spec_from_file_location('hecke_d79_priority_class', source)
    H = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(H)
    t0 = time.perf_counter_ns()
    funcs, jfun = H.build([2, 5])
    build_ns = time.perf_counter_ns() - t0
    H79 = hilbert_class_polynomial(-79)
    out = {'schema': 'hecke-d79-priority-class-v1', 'status': 'RUNNING',
           'degree25_build_wall_ns': build_ns, 'cases': [],
           'candidate_id': None, 'target_online_ms': None}
    path = HERE / 'class-result.json'
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    for selected in SCREEN['selected']:
        t0 = time.perf_counter_ns()
        p, v = selected['p'], selected['v']
        R = H.Reduced(p, funcs, jfun, [2, 5])
        E, Fp = R.E, R.Fp
        if int(E.cardinality()) != selected['curve_order']:
            raise ValueError('CURVE_ORDER_MISMATCH')
        starts = []
        for j in H79.change_ring(Fp).roots(multiplicities=False):
            tr = abs(int(EllipticCurve_from_j(j).trace_of_frobenius()))
            if tr == 2*v:
                starts.extend(R.points_with_j(j))
        seen, frontier = set(starts), list(starts)
        trace_cache = {}
        def in_class(P):
            j = R.j(P)
            if j is None or j == 0 or j == 1728:
                return False
            if j not in trace_cache:
                trace_cache[j] = abs(int(EllipticCurve_from_j(j).trace_of_frobenius()))
            return trace_cache[j] == 2*v
        while frontier:
            nxt = []
            for P in frontier:
                for ell in (2, 5):
                    for Q in R.neighbour_candidates(ell, P):
                        if Q not in seen and in_class(Q):
                            seen.add(Q)
                            nxt.append(Q)
            frontier = nxt
        points = sorted(seen, key=lambda P: (int(P[0]), int(P[1])))
        if len(points) != 40:
            out['cases'].append({'p': p, 'v': v, 'status': 'CLASS_SIZE_MISMATCH',
                                 'class_size': len(points), 'start_count': len(starts)})
            path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
            continue
        class_ns = time.perf_counter_ns() - t0
        index = {P: i for i, P in enumerate(points)}
        t0 = time.perf_counter_ns()
        rows = []
        for i, P in enumerate(points):
            for ell in (2, 5):
                nb = R.neighbours_all(ell, P)
                if nb is None or not all(Q in index for Q in nb):
                    continue
                if sum(nb, E(0)) != R.a_l[ell]*P:
                    raise ValueError('BASE_HECKE_EQUATION_FAIL')
                row = Counter(index[Q] for Q in nb)
                row[i] -= int(R.a_l[ell])
                sparse = {k: x for k, x in row.items() if x}
                if sum((x*points[k] for k, x in sparse.items()), E(0)) != E(0):
                    raise ValueError('BASE_ROW_GROUP_FAIL')
                rows.append({'source': i, 'degree': ell,
                             'row': {str(k): x for k, x in sorted(sparse.items())}})
        projected = [(selected['curve_order']//5)*P for P in points]
        T = next((Q for Q in projected if Q != E(0)), None)
        if T is None:
            residues = [0]*40
        else:
            lookup = {k*T: k for k in range(5)}
            if len(lookup) != 5 or any(Q not in lookup for Q in projected):
                raise ValueError('PROJECTION_FAIL')
            residues = [lookup[Q] for Q in projected]
        buckets = {r: [i for i, x in enumerate(residues) if x == r]
                   for r in sorted(set(residues))}
        priority = []
        for offset in range(max(len(bucket) for bucket in buckets.values())):
            for r in sorted(buckets):
                if offset < len(buckets[r]):
                    priority.append(buckets[r][offset])
        if sorted(priority) != list(range(40)):
            raise ValueError('PRIORITY_PERMUTATION_FAIL')
        row_rank = rank([{int(k): x for k, x in item['row'].items()} for item in rows], 40)
        cell = {'p': p, 'v': v, 'curve_order': selected['curve_order'],
                'largest_prime_factor': selected['largest_prime_factor'],
                'status': 'CLASS_READY', 'start_count': len(starts),
                'class_size': 40, 'class_points': [[int(P[0]), int(P[1])] for P in points],
                'base_rows': rows, 'base_rank_qq': row_rank,
                'projection_residues': residues,
                'projection_counts': {str(k): residues.count(k) for k in range(5)},
                'priority_order': priority, 'ascending_order': list(range(40)),
                'class_walk_wall_ns': class_ns,
                'base_and_order_wall_ns': time.perf_counter_ns() - t0}
        out['cases'].append(cell)
        path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
        print(json.dumps({'p': p, 'status': cell['status'],
                          'class_size': 40, 'projection_counts': cell['projection_counts']}),
              flush=True)
    out['status'] = 'COMPLETE'
    out['peak_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
