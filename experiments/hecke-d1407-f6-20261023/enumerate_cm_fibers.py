"""Independently enumerate X0(11) rational points above four CM strata."""
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys

from sage.all import hilbert_class_polynomial, pari

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
    rd = H.Reduced(data['p'], funcs, jfun, [2, 3])
    saved = {point(rd.E, s) for s in data['column_points']}
    complete = set()
    strata = {}
    for conductor in (1, 2, 3, 6):
        D = -1407*conductor*conductor
        js = hilbert_class_polynomial(D).change_ring(rd.Fp).roots(multiplicities=False)
        point_counts = Counter()
        points = set()
        exceptional = []
        for j in js:
            fiber = rd.points_with_j(j)
            point_counts[len(fiber)] += 1
            points.update(fiber)
            if len(fiber) != 2:
                exceptional.append({'j': int(j), 'rational_points': [str(q) for q in fiber]})
        complete.update(points)
        strata[str(conductor)] = {'class_number': int(pari.qfbclassno(D)),
                                  'rational_j_count': len(js), 'rational_point_count': len(points),
                                  'points_per_j': dict(point_counts), 'exceptional_fibers': exceptional}
    result = {'status': 'INDEPENDENT_CM_FIBER_ENUMERATION',
              'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'script_sha256': hashlib.sha256((P/'enumerate_cm_fibers.py').read_bytes()).hexdigest(),
              'strata': strata, 'complete_count': len(complete), 'saved_count': len(saved),
              'missing_from_walk': sorted(map(str, complete-saved)),
              'outside_four_strata': sorted(map(str, saved-complete))}
    (P/'cm_fibers.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(result, sort_keys=True))

if __name__ == '__main__': main()
