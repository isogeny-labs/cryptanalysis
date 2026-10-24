"""Record exact conductor behavior after the frozen first-prime producer gate failed."""
from collections import Counter,defaultdict
from hashlib import sha256
import json
from pathlib import Path

from sage.all import EllipticCurve_from_j, GF, hilbert_class_polynomial

HERE=Path(__file__).resolve().parent


def main():
    protocol=json.loads((HERE/'producer_protocol.json').read_text())
    p=protocol['p']; d=protocol['d']; field=GF(p)
    strata={}; appearances=defaultdict(list)
    for c in (1,2,3,6):
        js=hilbert_class_polynomial(-d*c*c).change_ring(field).roots(multiplicities=False)
        rows=[]
        for j in js:
            curve=EllipticCurve_from_j(j)
            actual=int(curve.endomorphism_order().conductor())
            trace=abs(int(curve.trace_of_frobenius()))
            isogenies=curve.isogenies_prime_degree(3)
            rows.append({'j':int(j),'expected_conductor':c,
                         'actual_conductor':actual,'trace_abs':trace,
                         'rational_degree3_isogeny_count':len(isogenies),
                         'degree3_codomain_j':[int(phi.codomain().j_invariant()) for phi in isogenies]})
            appearances[int(j)].append(c)
        strata[str(c)]={'root_count':len(rows),
                        'actual_conductor_counts':dict(Counter(str(r['actual_conductor']) for r in rows)),
                        'rows':sorted(rows,key=lambda r:r['j'])}
    overlaps={str(j):cs for j,cs in appearances.items() if len(cs)>1}
    out={'status':'FIRST_PRIME_EXACT_CONDUCTOR_GATE_FAILED',
         'producer_protocol_sha256':sha256((HERE/'producer_protocol.json').read_bytes()).hexdigest(),
         'script_sha256':sha256((HERE/'diagnose.py').read_bytes()).hexdigest(),
         'p':p,'d':d,'strata':strata,'overlapping_j':overlaps,
         'candidate_id':None,'timing_claim':None}
    (HERE/'conductor_diagnostic.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':out['status'],
                      'actual_conductor_counts':{k:v['actual_conductor_counts'] for k,v in strata.items()},
                      'overlap_count':len(overlaps)},sort_keys=True))


if __name__=='__main__':main()
