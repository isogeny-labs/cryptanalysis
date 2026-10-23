"""Locate rational Hecke neighbors omitted by the frozen D1407 walk."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import sys

from sage.all import EllipticCurve_from_j

P = Path(__file__).resolve().parent
sys.path.insert(0, str(P / 'tools'))
import hecke11 as H

def point(E, encoded):
    x, y = encoded[1:-1].split(' : ')[:2]
    return E([int(x), int(y), 1])

def main():
    source = P / 'data/exp11_class_walk_D1407_f6.json'
    data = json.loads(source.read_text())
    funcs, jfun = H.build([2, 3])
    reduced = H.Reduced(data['p'], funcs, jfun, [2, 3])
    points = [point(reduced.E, s) for s in data['column_points']]
    seen = set(points)
    omitted = defaultdict(list)
    for i, q in enumerate(points):
        for ell in (2, 3):
            neighbors = reduced.neighbours_all(ell, q)
            if neighbors is None:
                continue
            for neighbor in neighbors:
                if neighbor not in seen:
                    omitted[str(neighbor)].append({'source_column': i, 'degree': ell})
    records = []
    for encoded, sources in sorted(omitted.items()):
        q = point(reduced.E, encoded)
        j = reduced.j(q)
        curve = EllipticCurve_from_j(j) if j is not None else None
        roots = {str(ell): sum(int(m) for _, m in reduced.neighbour_x(ell, q).roots())
                 for ell in (2, 3)}
        records.append({'point': encoded, 'j': None if j is None else int(j),
                        'trace_abs': None if curve is None else abs(int(curve.trace_of_frobenius())),
                        'endomorphism_conductor': None if curve is None else int(curve.endomorphism_order().conductor()),
                        'sources': sources, 'rational_neighbor_root_counts': roots})
    result = {'status': 'DIAGNOSED_MISSING_NEIGHBORS',
              'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'script_sha256': hashlib.sha256((P/'diagnose_missing.py').read_bytes()).hexdigest(),
              'missing_point_count': len(records), 'records': records}
    (P/'missing_neighbors.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(result, sort_keys=True))

if __name__ == '__main__': main()
