"""Add the frozen trace-64 seed relations to the p=20023 frontier matrix."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
from sage.all import EllipticCurve_from_j, GF, ZZ, classical_modular_polynomial, matrix

HERE=Path(__file__).resolve().parent
MODULE=HERE.parent/'hecke-two-sheet-small-order-20261023/tools/hecke11.py'
sys.path.insert(0,str(MODULE.parent))
import hecke11 as H

def sha(p):return sha256(p.read_bytes()).hexdigest()
def key(P):return (-1,-1) if P.is_zero() else (int(P[0]),int(P[1]))

def main():
    raw=(HERE/'p20023.seed.protocol.json').read_bytes();protocol=json.loads(raw)
    frontier=json.loads((HERE/'p20023.result.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_SEED_COMPLETION'
    assert protocol['source_sha256']=={'seed_producer':sha(HERE/'complete_seed.py'),
                                       'frontier':sha(HERE/'p20023.result.json'),
                                       'hecke11':sha(MODULE)}
    funcs,jfun=H.build([2,3]);rd=H.Reduced(20023,funcs,jfun,[2,3]);T=rd.E([5,5,1])
    assert 5*T==rd.E(0)
    def orbit(P):return min(key(P+k*T) for k in range(5))
    keys=[tuple(x) for x in frontier['column_representatives']];idx={a:i for i,a in enumerate(keys)}
    seed={tuple(x) for x in frontier['boundary_representatives']['seed']}
    traces={};sources=[]
    for P in rd.E:
        j=rd.j(P)
        if j is None:continue
        jj=int(j)
        if jj not in traces:traces[jj]=abs(int(EllipticCurve_from_j(j).trace_of_frobenius()))
        if traces[jj]==64:sources.append(P)
    assert len(sources)==588 and {orbit(P) for P in sources}==seed
    phi={l:classical_modular_polynomial(l) for l in (2,3)}
    status=Counter();accepted=[]
    for P in sorted(sources,key=key):
        j=rd.j(P)
        for l in (2,3):
            if sum(int(m) for _,m in rd.neighbour_x(l,P).roots())!=l+1:
                status[f'L{l}_NOT_ALL_RATIONAL']+=1;continue
            nb=rd.neighbours_all(l,P)
            if nb is None or len(nb)!=l+1:
                status[f'L{l}_UNRESOLVED_NEIGHBOURS']+=1;continue
            if any(rd.j(Q) is None for Q in nb):
                status[f'L{l}_CUSP_NEIGHBOUR']+=1;continue
            assert sum(nb,rd.E(0))==rd.a_l[l]*P
            assert all(phi[l](j,rd.j(Q))==0 for Q in nb)
            coeff=Counter(orbit(Q) for Q in nb);coeff[orbit(P)]-=int(rd.a_l[l])
            assert set(coeff)<=set(keys)
            accepted.append({'source':key(P),'degree':l,'neighbours':[key(Q) for Q in nb],
                             'coefficients':{str(idx[a]):v for a,v in coeff.items() if v}})
            status[f'L{l}_ACCEPTED']+=1
    assert len(accepted)==490
    rows=[r['coefficients'] for r in accepted]+frontier['rows']
    def rank(cols,modulus):
        F=ZZ if modulus is None else GF(modulus)
        cidx={j:k for k,j in enumerate(cols)}
        entries={(i,cidx[int(j)]):v for i,row in enumerate(rows) for j,v in row.items() if int(j) in cidx}
        return int(matrix(F,len(rows),len(cols),entries,sparse=True).rank())
    seed_indices={idx[a] for a in seed}
    discarded=[j for j in range(len(keys)) if j not in seed_indices]
    ranks={}
    for mod in (None,4021):
        full=rank(list(range(len(keys))),mod);projection=rank(discarded,mod)
        ranks['exact' if mod is None else str(mod)]={'full_rank':full,
                 'discard_seed_projection_rank':projection,'induced_seed_rank':full-projection}
    out={'status':'SEED_COMPLETED','protocol_sha256':sha256(raw).hexdigest(),
         'frontier_sha256':sha(HERE/'p20023.result.json'),
         'seed_producer_sha256':sha(HERE/'complete_seed.py'),
         'source_count':len(sources),'status_counts':dict(status),'accepted_rows':accepted,
         'combined_row_count':len(rows),'column_count':len(keys),'ranks':ranks,
         'candidate_id':None,'timing_claim':None}
    (HERE/'p20023.seed.result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'seed_accepted':len(accepted),'rows':len(rows),'ranks':ranks},sort_keys=True))

if __name__=='__main__':main()
