"""Reconstruct degree-23 Hecke neighbors at all six fully split source points."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

from sage.all import GF, classical_modular_polynomial, matrix

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PRIOR=ROOT/'hecke-torsion-frontiers-20261024'
SCREEN=ROOT/'hecke-higher-degree-screen-20261024'
SIGN=ROOT/'hecke-sign-closure-20261024'
MODULE=ROOT/'hecke-two-sheet-small-order-20261023/tools/hecke11.py'
BUILDER=ROOT/'hecke-l13-closure-20261024/modular_hecke.py'
sys.path.insert(0,str(MODULE.parent));sys.path.insert(0,str(BUILDER.parent))
import hecke11 as H
from modular_hecke import build_mod

def sha(path):return sha256(path.read_bytes()).hexdigest()
def key(P):return (-1,-1) if P.is_zero() else (int(P[0]),int(P[1]))

def main():
    raw=(HERE/'protocol.json').read_bytes();protocol=json.loads(raw)
    assert protocol['status']=='FROZEN_BEFORE_L23_PRODUCER'
    sources={'producer':HERE/'produce.py','builder':BUILDER,'hecke11':MODULE,
             'screen':SCREEN/'result.json','frontier':PRIOR/'p20023.result.json',
             'seed':PRIOR/'p20023.seed.result.json','sign':SIGN/'result.json'}
    assert protocol['source_sha256']=={name:sha(path) for name,path in sources.items()}
    screen=json.loads(sources['screen'].read_text());prior=json.loads(sources['frontier'].read_text())
    seed=json.loads(sources['seed'].read_text());sign=json.loads(sources['sign'].read_text())
    src=[tuple(x) for x in screen['summary']['23']['fully_split_sources']]
    assert src==[tuple(x) for x in protocol['source_points']] and len(src)==6
    funcs,meta=build_mod(23,20023,H)
    encoded={f'{l}:{part}:{k}':{f'{a},{b}':int(c) for (a,b),c in coeff.items()}
             for (l,part,k),coeff in funcs.items()}
    (HERE/'functions.json').write_text(json.dumps({'functions':encoded,'metadata':meta},sort_keys=True,indent=2)+'\n')
    _,jfun=H.build([2,3]);rd=H.Reduced(20023,funcs,jfun,[23]);phi=classical_modular_polynomial(23)
    assert rd.a_l[23]==-1
    T=rd.E([5,5,1]);assert 5*T==rd.E(0)
    def point(a):return rd.E(0) if a==(-1,-1) else rd.E([a[0],a[1],1])
    def orbit(P):return min(key(P+k*T) for k in range(5))
    old_keys=[tuple(x) for x in prior['column_representatives']];old_set=set(old_keys)
    statuses=Counter();attempts=[];accepted=[];new=set()
    for rep in src:
        P=point(rep);j=rd.j(P);assert j is not None
        roots=rd.neighbour_x(23,P).roots()
        multiplicity=sum(int(m) for _,m in roots)
        record={'source':rep,'j':int(j),'rational_x_root_multiplicity':multiplicity}
        if multiplicity!=24:
            record['status']='NOT_ALL_RATIONAL_X';statuses[record['status']]+=1
            attempts.append(record);continue
        nb=rd.neighbours_all(23,P)
        if nb is None or len(nb)!=24:
            record['status']='UNRESOLVED_NEIGHBOURS';statuses[record['status']]+=1
            attempts.append(record);continue
        if any(rd.j(Q) is None for Q in nb):
            record['status']='CUSP_NEIGHBOUR';statuses[record['status']]+=1
            attempts.append(record);continue
        assert sum(nb,rd.E(0))==-P
        assert all(phi(j,rd.j(Q))==0 for Q in nb)
        coeff=Counter(orbit(Q) for Q in nb);coeff[orbit(P)]+=1
        coeff={a:v for a,v in coeff.items() if v}
        new.update(set(coeff)-old_set)
        record['status']='ACCEPTED';record['row_index']=len(accepted)
        statuses['ACCEPTED']+=1;attempts.append(record)
        accepted.append({'source':rep,'j':int(j),'neighbors':[key(Q) for Q in nb],
                         'coefficients':coeff})
    keys=sorted(old_set|new);idx={a:i for i,a in enumerate(keys)}
    def encode(row):return {str(idx[a]):v for a,v in row.items() if v}
    base=[r['coefficients'] for r in seed['accepted_rows']]+prior['rows']
    old_rows=[encode({old_keys[int(j)]:v for j,v in row.items()}) for row in base]
    sign_rows=[encode({old_keys[int(j)]:v for j,v in row['coefficients'].items()})
               for row in sign['sign_rows']]
    new_rows=[encode(row['coefficients']) for row in accepted]
    accepted_out=[{**{k:v for k,v in row.items() if k!='coefficients'},'coefficients':enc}
                  for row,enc in zip(accepted,new_rows)]
    anchor=idx[orbit(point((1,8630)))]
    def mat(rows):
        entries={(i,int(j)):v for i,row in enumerate(rows) for j,v in row.items()}
        entries[(len(rows),anchor)]=1
        return matrix(GF(4021),len(rows)+1,len(keys),entries,sparse=False)
    old_cols={idx[a] for a in old_keys};discard=sorted(set(range(len(keys)))-old_cols)
    diagnostics={}
    for name,rows in [('hecke',old_rows),('hecke_sign',old_rows+sign_rows)]:
        before=mat(rows);after=mat(rows+new_rows)
        K=after.right_kernel();support=set().union(*(set(v.support()) for v in K.basis()))
        proj=int(after.matrix_from_columns(discard).rank()) if discard else 0
        diagnostics[name]={'baseline_rank':int(before.rank()),'combined_rank':int(after.rank()),
                           'new_column_projection_rank':proj,
                           'combined_induced_old_rank':int(after.rank())-proj,
                           'combined_nullity':int(K.dimension()),
                           'ambiguous_old_indices':sorted(old_keys.index(keys[i]) for i in support&old_cols)}
    out={'status':'L23_TARGETED_PRODUCED','protocol_sha256':sha256(raw).hexdigest(),
         'source_sha256':{name:sha(path) for name,path in sources.items()},
         'functions_sha256':sha(HERE/'functions.json'),'function_metadata':meta,
         'source_points':src,'status_counts':dict(statuses),'attempts':attempts,
         'accepted_rows':accepted_out,'new_representatives':sorted(new),
         'all_column_representatives':keys,'rank_diagnostics':diagnostics,
         'candidate_id':None,'timing_claim':None}
    (HERE/'result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status_counts':dict(statuses),'new_columns':len(new),
                      'rank_diagnostics':diagnostics},sort_keys=True))

if __name__=='__main__':main()
