"""Checked-Sage replay of third-frontier traces and modular neighbors."""
from collections import Counter
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
    data=json.loads((HERE/'result.json').read_text())
    funcs,jfun=H.build([2,3]);rd=H.Reduced(12043,funcs,jfun,[2,3])
    def point(pair):return rd.E(0) if pair==[-1,-1] else rd.E([pair[0],pair[1],1])
    phi={l:classical_modular_polynomial(l) for l in (2,3)}
    traces=Counter();cusp=0
    for rec in data['source_records']:
        Q=point(rec['point']);j=rd.j(Q)
        if j is None:
            assert rec['status']=='CUSP_OR_UNDEFINED_J';cusp+=1
        else:
            assert rec['status']=='CLASSIFIED' and rec['j']==int(j)
            trace=abs(int(EllipticCurve_from_j(j).trace_of_frobenius()))
            assert trace==rec['trace_abs'];traces[trace]+=1
    cross=0
    for row in data['accepted_rows']:
        Q=point(row['source']);l=row['degree'];j=rd.j(Q)
        assert j is not None
        trace=abs(int(EllipticCurve_from_j(j).trace_of_frobenius()))
        assert trace==row['source_trace_abs']
        nb=[point(z) for z in row['neighbours']]
        assert len(nb)==l+1 and sum(nb,rd.E(0))==rd.a_l[l]*Q
        for N in nb:
            jn=rd.j(N)
            assert jn is not None and phi[l](j,jn)==0
        cross+=trace!=200
    out={'status':'PASS_TORSION_LAYER3_TRACE_AND_MODULAR_REPLAY',
         'result_sha256':sha(HERE/'result.json'),'script_sha256':sha(HERE/'validate_trace.py'),
         'hecke11_sha256':sha(MODULE),'classified_trace_abs_counts':{str(k):v for k,v in sorted(traces.items())},
         'undefined_j_source_count':cusp,'accepted_rows_checked':len(data['accepted_rows']),
         'accepted_different_abs_trace_rows':cross,'candidate_id':None,'timing_claim':None}
    (HERE/'trace_validation.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'accepted_rows':out['accepted_rows_checked'],
                      'different_abs_trace_rows':cross},sort_keys=True))

if __name__=='__main__':main()
