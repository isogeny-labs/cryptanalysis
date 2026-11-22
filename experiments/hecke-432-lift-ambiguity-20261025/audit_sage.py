"""Resolve every two-lift j-pair row at the level-27 group difference."""
import json
import sys
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import EllipticCurve, GF, sage_eval

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT/'hecke-27-coordinate-bridge-20261025'))
from evaluate_sage import roots_for_pair  # noqa: E402


def main():
    result = json.loads((ROOT/'hecke-432-kernel-transport-20261025'/'full_result.json').read_text())
    maps = json.loads((ROOT/'hecke-27-coordinate-bridge-20261025'/'coordinate_map.json').read_text())
    K = GF(883**2, 'u')
    u = K.gen()
    C = EllipticCurve(K, maps['curve_ainvs'])
    checked = []
    for index, row in enumerate(result['rows']):
        if row['coordinate_counts'] != [2,2]:
            continue
        points=[]
        for jpair in row['j_pairs']:
            js,jt = [sage_eval(v,locals={'u':u}) for v in jpair]
            roots = roots_for_pair(C,maps,js,jt)[1]
            assert len(roots)==2
            points.append(roots)
        matched=[]
        for P in points[0]:
            for Q in points[1]:
                if P[0]**883==Q[0] and P[1]**883==Q[1]:
                    matched.append((P,Q))
        differences=[P-Q for P,Q in matched]
        assert len(differences)==2 and not differences[0].is_zero()
        assert differences[0]==differences[1]
        translation=matched[1][0]-matched[0][0]
        assert translation==matched[1][1]-matched[0][1]
        translation_order=int(translation.order())
        checked.append({'row_index':index,'source_j':row['source_j'],
                        'pair':row['pair'],'difference':[str(differences[0][0]),
                                                           str(differences[0][1])],
                        'common_translation':[str(translation[0]),str(translation[1])],
                        'common_translation_order':translation_order,
                        'B_point':row['B_points'][0]})
    assert len(checked)==48
    out={'status':'PASS_ALL_MULTILIFT_DIFFERENCES','prime':883,
         'multi_lift_rows':len(checked),'compatible_pairs_per_row':2,
         'distinct_nonzero_differences_per_row':1,
         'common_translation_orders':sorted(set(r['common_translation_order'] for r in checked)),
         'rows':checked}
    (HERE/'result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','prime','multi_lift_rows',
                                       'compatible_pairs_per_row',
                                       'distinct_nonzero_differences_per_row')},sort_keys=True))


if __name__=='__main__':
    main()
