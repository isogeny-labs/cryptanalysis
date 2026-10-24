"""Necessary X_0(11)(Fp) point-lift control for the two selected fibers."""
import json
from pathlib import Path
import sys
from sage.all import GF, PolynomialRing, classical_modular_polynomial

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'hecke-two-sheet-small-order-20261023/tools'))
import hecke11 as H

def main():
    screen=json.loads((HERE/'result.json').read_text())
    funcs,jfun=H.build([2,3]);rd=H.Reduced(20023,funcs,jfun,[2,3])
    F=GF(20023);R=PolynomialRing(F,'Y');Y=R.gen()
    phi=classical_modular_polynomial(29)
    outcomes=[]
    for record in screen['outcomes']['29']['fully_split_adjacencies']:
        sj=record['source_j']
        roots=R(phi(F(sj),Y)).roots()
        values=[]
        for j,m in roots:
            pts=rd.points_with_j(j)
            values.append({'j':int(j),'multiplicity':int(m),'rational_point_lifts':len(pts)})
        outcomes.append({'source_j':sj,'root_count':sum(v['multiplicity'] for v in values),
                         'distinct_root_count':len(values),
                         'unliftable_j':sorted(v['j'] for v in values if not v['rational_point_lifts']),
                         'roots':values})
    result={'status':'L29_NECESSARY_POINT_LIFT_SCREEN','outcomes':outcomes,
            'candidate_id':None,'timing_claim':None}
    (HERE/'l29_lift_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps([{'source_j':r['source_j'],'unliftable_j':r['unliftable_j']}
                      for r in outcomes],sort_keys=True))

if __name__=='__main__':main()
