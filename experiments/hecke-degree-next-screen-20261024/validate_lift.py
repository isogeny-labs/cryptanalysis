"""Direct point enumeration replay of the degree-29 rational lift counts."""
import json
from collections import Counter
from pathlib import Path
import sys
from sage.all import GF, PolynomialRing, classical_modular_polynomial

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'hecke-two-sheet-small-order-20261023/tools'))
import hecke11 as H

def main():
    saved=json.loads((HERE/'l29_lift_result.json').read_text())
    funcs,jfun=H.build([2,3]);rd=H.Reduced(20023,funcs,jfun,[2,3])
    counts=Counter()
    for P in rd.E.points():
        j=rd.j(P)
        if j is not None:counts[int(j)]+=1
    F=GF(20023);R=PolynomialRing(F,'Y');Y=R.gen()
    phi=classical_modular_polynomial(29)
    summary=[]
    for row in saved['outcomes']:
        roots=R(phi(F(row['source_j']),Y)).roots()
        assert sum(int(m) for _,m in roots)==30
        expected={int(j):(int(m),counts[int(j)]) for j,m in roots}
        actual={r['j']:(r['multiplicity'],r['rational_point_lifts']) for r in row['roots']}
        assert actual==expected
        summary.append({'source_j':row['source_j'],'distinct_roots':len(roots),
                        'all_roots_have_rational_lift':all(n>0 for _,n in expected.values())})
    result={'status':'PASS_DIRECT_POINT_ENUMERATION_LIFT_REPLAY','curve_points':len(rd.E.points()),
            'sources':summary}
    (HERE/'l29_lift_validation.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
