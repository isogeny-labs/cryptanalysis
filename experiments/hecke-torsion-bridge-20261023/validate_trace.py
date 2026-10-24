"""Checked-Sage replay of translated-source traces and modular neighbors."""
from hashlib import sha256
import json
from pathlib import Path
import sys

from sage.all import EllipticCurve_from_j, classical_modular_polynomial

HERE=Path(__file__).resolve().parent
MODULE=HERE.parent/'hecke-two-sheet-small-order-20261023'/'tools'/'hecke11.py'
sys.path.insert(0,str(MODULE.parent))
import hecke11 as H

def sha(path):return sha256(path.read_bytes()).hexdigest()

def main():
    result=json.loads((HERE/'result.json').read_text())
    funcs,jfun=H.build([2,3]);rd=H.Reduced(12043,funcs,jfun,[2,3])
    def point(pair):return rd.E(0) if pair==[-1,-1] else rd.E([pair[0],pair[1],1])
    phi={l:classical_modular_polynomial(l) for l in (2,3)}
    statuses={}
    for record in result['source_records']:
        Q=point(record['point']);j=rd.j(Q)
        if j is None:
            assert record['status']=='CUSP_OR_UNDEFINED_J'
        else:
            assert record['status']=='CLASSIFIED' and int(j)==record['j']
            trace=abs(int(EllipticCurve_from_j(j).trace_of_frobenius()))
            assert trace==record['trace_abs']
            statuses[trace]=statuses.get(trace,0)+1
    cross=0
    for row in result['accepted_rows']:
        Q=point(row['source']);l=row['degree'];j=rd.j(Q)
        assert j is not None
        trace=abs(int(EllipticCurve_from_j(j).trace_of_frobenius()))
        assert trace==row['source_trace_abs']
        neighbours=[point(z) for z in row['neighbours']]
        assert len(neighbours)==l+1
        assert sum(neighbours,rd.E(0))==rd.a_l[l]*Q
        for N in neighbours:
            jn=rd.j(N)
            assert jn is not None and phi[l](j,jn)==0
        cross+=trace!=200
    assert cross==result['cross_class_accepted_rows']==40
    out={'status':'PASS_TORSION_BRIDGE_TRACE_AND_MODULAR_REPLAY',
         'result_sha256':sha(HERE/'result.json'),'script_sha256':sha(HERE/'validate_trace.py'),
         'hecke11_sha256':sha(MODULE),
         'classified_trace_abs_counts':{str(k):v for k,v in sorted(statuses.items())},
         'accepted_rows_checked':len(result['accepted_rows']),
         'accepted_cross_class_rows':cross,'candidate_id':None,'timing_claim':None}
    (HERE/'trace_validation.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'accepted_cross_class_rows':cross},sort_keys=True))

if __name__=='__main__':main()
