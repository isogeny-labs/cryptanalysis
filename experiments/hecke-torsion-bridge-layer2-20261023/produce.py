"""Second torsion-orbit frontier and exact induced-rank gate."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
import time

from sage.all import EllipticCurve_from_j, GF, classical_modular_polynomial, matrix

HERE=Path(__file__).resolve().parent
FIRST=HERE.parent/'hecke-torsion-bridge-20261023'/'result.json'
MATRIX=HERE.parent/'hecke-inert2-non3-cycle-20261023'/'full_matrix.json'
MODULE=HERE.parent/'hecke-two-sheet-small-order-20261023'/'tools'/'hecke11.py'
sys.path.insert(0,str(MODULE.parent))
import hecke11 as H

def sha(path):return sha256(path.read_bytes()).hexdigest()
def key(P):return (-1,-1) if P.is_zero() else (int(P[0]),int(P[1]))

def main():
    raw=(HERE/'protocol.json').read_bytes();protocol=json.loads(raw)
    assert protocol['status']=='FROZEN_BEFORE_TORSION_LAYER2_PRODUCER'
    for name,path in [('first',FIRST),('matrix',MATRIX),('hecke11',MODULE),('producer',HERE/'produce.py')]:
        assert protocol['source_sha256'][name]==sha(path)
    first=json.loads(FIRST.read_text());original=json.loads(MATRIX.read_text())
    assert first['status']=='TORSION_BRIDGE_ONE_LAYER_PRODUCED'
    assert first['rank_results']['101']['induced_increment']==0
    funcs,jfun=H.build([2,3]);rd=H.Reduced(12043,funcs,jfun,[2,3])
    T=rd.E([5,5,1]);assert 5*T==rd.E(0)
    def point(pair):return rd.E(0) if pair==[-1,-1] else rd.E([pair[0],pair[1],1])
    def orbit(P):return min(key(P+k*T) for k in range(5))
    prior_keys=[tuple(x) for x in first['column_representatives']]
    old_keys={prior_keys[i] for i in first['old_column_indices']}
    frontier_keys=[prior_keys[i] for i in first['new_column_indices']]
    assert len(frontier_keys)==128
    sources={}
    for index,representative in enumerate(frontier_keys):
        P=point(list(representative))
        assert orbit(P)==representative
        for k in range(5):
            Q=P+k*T
            assert Q not in sources
            sources[Q]=(first['new_column_indices'][index],k)
    assert len(sources)==640
    phi={l:classical_modular_polynomial(l) for l in (2,3)}
    statuses=Counter();source_records=[];accepted=[]
    for P in sorted(sources,key=key):
        j=rd.j(P)
        if j is None:
            source_records.append({'point':key(P),'frontier_origin':sources[P],
                                   'status':'CUSP_OR_UNDEFINED_J'})
            statuses['SOURCE_UNDEFINED_J']+=1;continue
        trace_abs=abs(int(EllipticCurve_from_j(j).trace_of_frobenius()))
        source_records.append({'point':key(P),'frontier_origin':sources[P],
                               'status':'CLASSIFIED','j':int(j),'trace_abs':trace_abs})
        for l in (2,3):
            roots=rd.neighbour_x(l,P).roots()
            if sum(int(m) for _,m in roots)!=l+1:
                statuses[f'L{l}_NOT_ALL_RATIONAL']+=1;continue
            nb=rd.neighbours_all(l,P)
            if nb is None or len(nb)!=l+1:
                statuses[f'L{l}_UNRESOLVED_NEIGHBOURS']+=1;continue
            if any(rd.j(Q) is None for Q in nb):
                statuses[f'L{l}_CUSP_NEIGHBOUR']+=1;continue
            assert sum(nb,rd.E(0))==rd.a_l[l]*P
            assert all(phi[l](j,rd.j(Q))==0 for Q in nb)
            coeff=Counter(orbit(Q) for Q in nb)
            coeff[orbit(P)]-=rd.a_l[l]
            accepted.append({'source':key(P),'frontier_origin':sources[P],
                             'source_trace_abs':trace_abs,'degree':l,
                             'neighbours':[key(Q) for Q in nb],
                             'coefficients':{a:v for a,v in coeff.items() if v}})
            statuses[f'L{l}_ACCEPTED']+=1
    added_keys={a for row in accepted for a in row['coefficients']}-set(prior_keys)
    all_keys=sorted(set(prior_keys)|added_keys)
    index={a:i for i,a in enumerate(all_keys)}
    def lift(row,keys):return {str(index[keys[int(j)]]):int(v) for j,v in row.items()}
    base_rows=[lift(row,prior_keys) for row in first['base_rows']]
    layer1_rows=[lift(row['coefficients'],prior_keys) for row in first['accepted_rows']]
    layer2_rows=[{str(index[a]):int(v) for a,v in row['coefficients'].items()} for row in accepted]
    prior_rows=base_rows+layer1_rows
    full_rows=prior_rows+layer2_rows
    old_cols=sorted(index[a] for a in old_keys)
    prior_cols=sorted(index[a] for a in prior_keys)
    new_from_old=sorted(set(range(len(all_keys)))-set(old_cols))
    new_from_prior=sorted(set(range(len(all_keys)))-set(prior_cols))
    rank_results={}
    for modulus in (101,1000000007):
        F=GF(modulus)
        def rank(rows,cols):
            return int(matrix(F,[[row.get(str(j),0) for j in cols] for row in rows],sparse=True).rank()) if cols else 0
        start=time.monotonic()
        rbase=rank(base_rows,old_cols)
        rprior=rank(prior_rows,prior_cols)
        rfull=rank(full_rows,list(range(len(all_keys))))
        rnewold=rank(full_rows,new_from_old)
        rnewprior=rank(full_rows,new_from_prior)
        rank_results[str(modulus)]={'base_old_rank':rbase,'prior_full_rank':rprior,
            'full_rank':rfull,'new_from_old_projection_rank':rnewold,
            'induced_old_rank':rfull-rnewold,'induced_old_increment':rfull-rnewold-rbase,
            'new_from_prior_projection_rank':rnewprior,
            'induced_prior_rank':rfull-rnewprior,'induced_prior_increment':rfull-rnewprior-rprior,
            'rank_wall_s':time.monotonic()-start}
    out={'status':'TORSION_BRIDGE_LAYER2_PRODUCED',
         'protocol_sha256':sha256(raw).hexdigest(),'script_sha256':sha(HERE/'produce.py'),
         'first_sha256':sha(FIRST),'source_matrix_sha256':sha(MATRIX),'hecke11_sha256':sha(MODULE),
         'p':12043,'torsion_point':[5,5],'frontier_orbit_count':len(frontier_keys),
         'candidate_source_count':len(sources),'source_records':source_records,
         'status_counts':dict(statuses),
         'accepted_rows':[{**{k:v for k,v in row.items() if k!='coefficients'},
                           'coefficients':{str(index[a]):v for a,v in row['coefficients'].items()}}
                          for row in accepted],
         'column_representatives':all_keys,
         'old_column_indices':old_cols,'prior_column_indices':prior_cols,
         'new_from_old_indices':new_from_old,'new_from_prior_indices':new_from_prior,
         'base_rows':base_rows,'layer1_rows':layer1_rows,
         'rank_results':rank_results,'candidate_id':None,'timing_claim':None}
    (HERE/'result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'candidates':len(sources),
                      'accepted_rows':len(accepted),'new_columns':len(new_from_prior),
                      'rank_results':rank_results},sort_keys=True))

if __name__=='__main__':main()
