"""Complete degree-5 Hecke incidence from the saved p=20023 quotient component."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
import time

from sage.all import GF, EllipticCurve, classical_modular_polynomial, matrix

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'hecke-torsion-frontiers-20261024'
MODULE=HERE.parent/'hecke-two-sheet-small-order-20261023/tools/hecke11.py'
sys.path.insert(0,str(MODULE.parent))
import hecke11 as H

def sha(path):return sha256(path.read_bytes()).hexdigest()
def key(P):return (-1,-1) if P.is_zero() else (int(P[0]),int(P[1]))

def main():
    protocol_file=HERE/'protocol.json';raw=protocol_file.read_bytes();protocol=json.loads(raw)
    assert protocol['status']=='FROZEN_BEFORE_L5_PRODUCER'
    sources={'producer':HERE/'produce.py','hecke11':MODULE,
             'frontier':PRIOR/'p20023.result.json','seed':PRIOR/'p20023.seed.result.json'}
    assert protocol['source_sha256']=={name:sha(path) for name,path in sources.items()}
    prior=json.loads(sources['frontier'].read_text());seed=json.loads(sources['seed'].read_text())
    assert prior['p']==20023 and len(prior['column_representatives'])==3949
    assert seed['combined_row_count']==5565
    funcs,jfun=H.build([5]);rd=H.Reduced(20023,funcs,jfun,[5]);phi=classical_modular_polynomial(5)
    T=rd.E([5,5,1]);assert 5*T==rd.E(0) and int(rd.E.cardinality())==20105
    assert rd.a_l[5]==1
    def point(pair):return rd.E(0) if tuple(pair)==(-1,-1) else rd.E([pair[0],pair[1],1])
    def orbit(P):return min(key(P+k*T) for k in range(5))
    old_keys=[tuple(x) for x in prior['column_representatives']]
    assert all(orbit(point(rep))==rep for rep in old_keys)
    base_rows=[r['coefficients'] for r in seed['accepted_rows']]+prior['rows']
    assert len(base_rows)==5565
    statuses=Counter();attempts=[];accepted=[];new=set();start=time.monotonic()
    for rep in old_keys:
        Q=point(rep)
        for k in range(5):
            P=Q+k*T;jP=rd.j(P)
            if jP is None:
                statuses['SOURCE_UNDEFINED_J']+=1
                attempts.append({'source':key(P),'status':'SOURCE_UNDEFINED_J'})
                continue
            roots=rd.neighbour_x(5,P).roots()
            if sum(int(m) for _,m in roots)!=6:
                status='NOT_ALL_RATIONAL';statuses[status]+=1
                attempts.append({'source':key(P),'status':status})
                continue
            neighbors=rd.neighbours_all(5,P)
            if neighbors is None or len(neighbors)!=6:
                status='UNRESOLVED_NEIGHBOURS';statuses[status]+=1
                attempts.append({'source':key(P),'status':status})
                continue
            if any(rd.j(R) is None for R in neighbors):
                status='CUSP_NEIGHBOUR';statuses[status]+=1
                attempts.append({'source':key(P),'status':status})
                continue
            assert sum(neighbors,rd.E(0))==P
            assert all(phi(jP,rd.j(R))==0 for R in neighbors)
            coeff=Counter(orbit(R) for R in neighbors);coeff[orbit(P)]-=1
            coeff={a:v for a,v in coeff.items() if v}
            new.update(set(coeff)-set(old_keys))
            accepted.append({'source':key(P),'neighbors':[key(R) for R in neighbors],
                             'coefficients':coeff})
            statuses['ACCEPTED']+=1
            attempts.append({'source':key(P),'status':'ACCEPTED','row_index':len(accepted)-1})
    all_keys=sorted(set(old_keys)|new);index={a:i for i,a in enumerate(all_keys)}
    def encode_keyed(row):return {str(index[a]):v for a,v in row.items() if v}
    old_index={a:i for i,a in enumerate(old_keys)}
    def encode_old(row):return encode_keyed({old_keys[int(j)]:v for j,v in row.items()})
    old_rows=[encode_old(row) for row in base_rows]
    l5_rows=[encode_keyed(row['coefficients']) for row in accepted]
    accepted_out=[{'source':row['source'],'neighbors':row['neighbors'],'coefficients':encoded}
                  for row,encoded in zip(accepted,l5_rows)]
    # Dense matrices use the installed finite-field backend; sparse echelon is
    # much slower for this near-full-rank incidence shape.
    def mat(rows,anchor=False):
        entries={(i,int(j)):v for i,row in enumerate(rows) for j,v in row.items()}
        if anchor:
            anchor_rep=orbit(point((1,8630)))
            entries[(len(rows),index[anchor_rep])]=1
        return matrix(GF(4021),len(rows)+int(anchor),len(all_keys),entries,sparse=False)
    old_set={index[a] for a in old_keys};discard=sorted(set(range(len(all_keys)))-old_set)
    before=mat(old_rows,True)
    after=mat(old_rows+l5_rows,True)
    def kernel_support(M):
        K=M.right_kernel();return sorted(set().union(*(set(v.support()) for v in K.basis()))),int(K.dimension())
    before_support,before_nullity=kernel_support(before)
    after_support,after_nullity=kernel_support(after)
    before_old=sorted(set(before_support)&old_set)
    after_old=sorted(set(after_support)&old_set)
    assert [old_keys.index(all_keys[i]) for i in before_old]==protocol['baseline_ambiguous_indices']
    out={'status':'L5_COMPLETE_COMPONENT_PRODUCED','p':20023,'degree':5,'a5':1,
         'protocol_sha256':sha256(raw).hexdigest(),
         'source_sha256':{name:sha(path) for name,path in sources.items()},
         'source_orbit_count':len(old_keys),'source_point_count':5*len(old_keys),
         'attempts':attempts,'status_counts':dict(statuses),
         'accepted_rows':accepted_out,'new_representatives':sorted(new),
         'all_column_representatives':all_keys,'old_rows':old_rows,
         'baseline_anchor_rank':int(before.rank()),'combined_anchor_rank':int(after.rank()),
         'discard_new_projection_rank':int(after.matrix_from_columns(discard).rank()) if discard else 0,
         'baseline_ambiguous_old_indices':[old_keys.index(all_keys[i]) for i in before_old],
         'combined_ambiguous_old_indices':[old_keys.index(all_keys[i]) for i in after_old],
         'baseline_nullity':before_nullity,'combined_nullity':after_nullity,
         'baseline_ambiguous_all_count':len(before_support),
         'combined_ambiguous_all_count':len(after_support),
         'producer_wall_diagnostic_s':time.monotonic()-start,
         'candidate_id':None,'timing_claim':None}
    (HERE/'result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:out[k] for k in ('source_point_count','status_counts','baseline_anchor_rank',
                 'combined_anchor_rank','discard_new_projection_rank','baseline_ambiguous_old_indices',
                 'combined_ambiguous_old_indices','combined_nullity')},sort_keys=True))

if __name__=='__main__':main()
