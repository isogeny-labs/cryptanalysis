"""Trace-screened degree-13 Hecke experiment on the p=20023 quotient component."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
import time

from sage.all import EllipticCurve_from_j, GF, classical_modular_polynomial, matrix

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'hecke-torsion-frontiers-20261024'
MODULE=HERE.parent/'hecke-two-sheet-small-order-20261023/tools/hecke11.py'
sys.path.insert(0,str(MODULE.parent));sys.path.insert(0,str(HERE))
import hecke11 as H
from modular_hecke import build_mod

def sha(path):return sha256(path.read_bytes()).hexdigest()
def key(P):return (-1,-1) if P.is_zero() else (int(P[0]),int(P[1]))

def main():
    raw=(HERE/'protocol.json').read_bytes();protocol=json.loads(raw)
    assert protocol['status']=='FROZEN_BEFORE_L13_PRODUCER'
    sources={'producer':HERE/'produce.py','modular_hecke':HERE/'modular_hecke.py',
             'hecke11':MODULE,'frontier':PRIOR/'p20023.result.json',
             'seed':PRIOR/'p20023.seed.result.json'}
    assert protocol['source_sha256']=={name:sha(path) for name,path in sources.items()}
    prior=json.loads(sources['frontier'].read_text());seed=json.loads(sources['seed'].read_text())
    assert len(prior['column_representatives'])==3949 and seed['combined_row_count']==5565
    start=time.monotonic();funcs,build_meta=build_mod(13,20023,H)
    _,jfun=H.build([2,3]);rd=H.Reduced(20023,funcs,jfun,[13]);phi=classical_modular_polynomial(13)
    assert rd.a_l[13]==4
    encoded_funcs={f'{l}:{part}:{k}':{f'{a},{b}':int(c) for (a,b),c in f.items()}
                   for (l,part,k),f in funcs.items()}
    (HERE/'functions.json').write_text(json.dumps({'metadata':build_meta,'functions':encoded_funcs},
                                                  indent=2,sort_keys=True)+'\n')
    T=rd.E([5,5,1]);assert 5*T==rd.E(0) and int(rd.E.cardinality())==20105
    def point(pair):return rd.E(0) if tuple(pair)==(-1,-1) else rd.E([pair[0],pair[1],1])
    def orbit(P):return min(key(P+k*T) for k in range(5))
    old_keys=[tuple(x) for x in prior['column_representatives']]
    assert all(orbit(point(rep))==rep for rep in old_keys)
    old_set=set(old_keys);base_rows=[r['coefficients'] for r in seed['accepted_rows']]+prior['rows']
    trace_cache={};statuses=Counter();attempts=[];accepted=[];new=set();eligible=0
    for rep in old_keys:
        P0=point(rep)
        for k in range(5):
            P=P0+k*T;j=rd.j(P)
            if j is None:
                statuses['SOURCE_UNDEFINED_J']+=1
                attempts.append({'source':key(P),'status':'SOURCE_UNDEFINED_J'})
                continue
            jj=int(j)
            if jj not in trace_cache:
                trace_cache[jj]=abs(int(EllipticCurve_from_j(j).trace_of_frobenius()))
            t=trace_cache[jj]
            if jj not in (0,1728%20023) and t%13 not in (5,8):
                statuses['TRACE_OBSTRUCTION']+=1
                attempts.append({'source':key(P),'status':'TRACE_OBSTRUCTION','abs_trace':t})
                continue
            eligible+=1
            roots=rd.neighbour_x(13,P).roots()
            if sum(int(m) for _,m in roots)!=14:
                statuses['NOT_ALL_RATIONAL']+=1
                attempts.append({'source':key(P),'status':'NOT_ALL_RATIONAL','abs_trace':t,
                                 'rational_root_multiplicity':sum(int(m) for _,m in roots)})
                continue
            nb=rd.neighbours_all(13,P)
            if nb is None or len(nb)!=14:
                statuses['UNRESOLVED_NEIGHBOURS']+=1
                attempts.append({'source':key(P),'status':'UNRESOLVED_NEIGHBOURS','abs_trace':t})
                continue
            if any(rd.j(Q) is None for Q in nb):
                statuses['CUSP_NEIGHBOUR']+=1
                attempts.append({'source':key(P),'status':'CUSP_NEIGHBOUR','abs_trace':t})
                continue
            assert sum(nb,rd.E(0))==4*P
            assert all(phi(j,rd.j(Q))==0 for Q in nb)
            coeff=Counter(orbit(Q) for Q in nb);coeff[orbit(P)]-=4
            coeff={a:v for a,v in coeff.items() if v}
            new.update(set(coeff)-old_set)
            accepted.append({'source':key(P),'neighbors':[key(Q) for Q in nb],
                             'abs_trace':t,'coefficients':coeff})
            statuses['ACCEPTED']+=1
            attempts.append({'source':key(P),'status':'ACCEPTED','row_index':len(accepted)-1,
                             'abs_trace':t})
        if len(attempts)%2500==0:
            print(json.dumps({'scanned':len(attempts),'eligible':eligible,'accepted':len(accepted)}),flush=True)
    all_keys=sorted(old_set|new);index={a:i for i,a in enumerate(all_keys)}
    def encode(row):return {str(index[a]):v for a,v in row.items() if v}
    old_rows=[encode({old_keys[int(j)]:v for j,v in row.items()}) for row in base_rows]
    new_rows=[encode(row['coefficients']) for row in accepted]
    accepted_out=[{**{k:v for k,v in row.items() if k!='coefficients'},'coefficients':encoded}
                  for row,encoded in zip(accepted,new_rows)]
    anchor=index[orbit(point((1,8630)))]
    def make_matrix(rows):
        entries={(i,int(j)):v for i,row in enumerate(rows) for j,v in row.items()}
        entries[(len(rows),anchor)]=1
        return matrix(GF(4021),len(rows)+1,len(all_keys),entries,sparse=False)
    before=make_matrix(old_rows);after=make_matrix(old_rows+new_rows)
    def support(M):
        K=M.right_kernel();return sorted(set().union(*(set(v.support()) for v in K.basis()))),int(K.dimension())
    old_indices={index[a] for a in old_keys}
    before_support,before_nullity=support(before);after_support,after_nullity=support(after)
    before_old=sorted(old_keys.index(all_keys[i]) for i in set(before_support)&old_indices)
    after_old=sorted(old_keys.index(all_keys[i]) for i in set(after_support)&old_indices)
    assert before_old==protocol['baseline_ambiguous_indices']
    discard=sorted(set(range(len(all_keys)))-old_indices)
    out={'status':'L13_TRACE_SCREENED_PRODUCED','p':20023,'degree':13,'a13':4,
         'protocol_sha256':sha256(raw).hexdigest(),'source_sha256':{name:sha(path) for name,path in sources.items()},
         'functions_sha256':sha(HERE/'functions.json'),'function_metadata':build_meta,
         'source_orbit_count':len(old_keys),'source_point_count':5*len(old_keys),
         'eligible_source_count':eligible,'status_counts':dict(statuses),'attempts':attempts,
         'accepted_rows':accepted_out,'new_representatives':sorted(new),
         'all_column_representatives':all_keys,
         'baseline_anchor_rank':int(before.rank()),'combined_anchor_rank':int(after.rank()),
         'discard_new_projection_rank':int(after.matrix_from_columns(discard).rank()) if discard else 0,
         'baseline_ambiguous_old_indices':before_old,'combined_ambiguous_old_indices':after_old,
         'baseline_nullity':before_nullity,'combined_nullity':after_nullity,
         'baseline_ambiguous_all_count':len(before_support),'combined_ambiguous_all_count':len(after_support),
         'producer_wall_diagnostic_s':time.monotonic()-start,
         'candidate_id':None,'timing_claim':None}
    (HERE/'result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:out[k] for k in ('source_point_count','eligible_source_count','status_counts',
                 'baseline_anchor_rank','combined_anchor_rank','discard_new_projection_rank',
                 'combined_ambiguous_old_indices','combined_nullity')},sort_keys=True))

if __name__=='__main__':main()
