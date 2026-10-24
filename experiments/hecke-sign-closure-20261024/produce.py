"""Add exact inversion identities to the p=20023 torsion-orbit relation matrix."""
from hashlib import sha256
import json
from pathlib import Path
from sage.all import EllipticCurve, GF, ZZ, matrix, vector

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'hecke-torsion-frontiers-20261024'
def sha(path):return sha256(path.read_bytes()).hexdigest()
def key(P):return (-1,-1) if P.is_zero() else (int(P[0]),int(P[1]))

def main():
    raw=(HERE/'protocol.json').read_bytes();protocol=json.loads(raw)
    assert protocol['status']=='FROZEN_BEFORE_SIGN_PRODUCER'
    sources={'producer':HERE/'produce.py','frontier':PRIOR/'p20023.result.json',
             'seed':PRIOR/'p20023.seed.result.json'}
    assert protocol['source_sha256']=={name:sha(path) for name,path in sources.items()}
    frontier=json.loads(sources['frontier'].read_text());seed=json.loads(sources['seed'].read_text())
    keys=[tuple(x) for x in frontier['column_representatives']];index={a:i for i,a in enumerate(keys)}
    base_rows=[r['coefficients'] for r in seed['accepted_rows']]+frontier['rows']
    assert len(keys)==3949 and len(base_rows)==5565
    E=EllipticCurve(GF(20023),[0,-1,1,-10,-20]);O=E(0);T=E([5,5,1]);assert 5*T==O
    def point(a):return O if a==(-1,-1) else E([a[0],a[1],1])
    def orbit(P):return min(key(P+k*T) for k in range(5))
    signs=[];seen=set()
    for i,rep in enumerate(keys):
        P=point(rep);j=index[orbit(-P)]
        assert index[orbit(-point(keys[j]))]==i
        pair=tuple(sorted((i,j)))
        if pair in seen:continue
        seen.add(pair)
        row={str(i):2} if i==j else {str(i):1,str(j):1}
        assert 5*P+5*point(keys[j])==O
        signs.append({'indices':list(pair),'points':[rep,keys[j]],'coefficients':row})
    assert len(signs)==1975
    sign_rows=[x['coefficients'] for x in signs]
    anchor=index[orbit(point((1,8630)))]
    def mat(rows,ring):
        entries={(i,int(j)):v for i,row in enumerate(rows) for j,v in row.items()}
        entries[(len(rows),anchor)]=1
        return matrix(ring,len(rows)+1,len(keys),entries,sparse=False)
    before=mat(base_rows,GF(4021));after=mat(base_rows+sign_rows,GF(4021))
    def support(M):
        K=M.right_kernel();return sorted(set().union(*(set(v.support()) for v in K.basis()))),int(K.dimension())
    b_support,b_null=support(before);a_support,a_null=support(after)
    assert b_support==protocol['baseline_ambiguous_indices']
    rhs=vector(GF(4021),[0]*(len(base_rows)+len(sign_rows))+[1])
    solution=after.solve_right(rhs);assert after*solution==rhs
    G=5*point((1,8630));assert 4021*G==O
    scalars={};Q=O
    for k in range(4021):
        assert key(Q) not in scalars
        scalars[key(Q)]=k;Q+=G
    assert Q==O and len(scalars)==4021
    table={}
    for i,rep in enumerate(keys):
        if i in a_support:continue
        x=key(5*point(rep));log=int(solution[i])
        assert scalars[x]==log
        table[x]=log
    exact_before=int(mat(base_rows,ZZ).rank())
    exact_after=int(mat(base_rows+sign_rows,ZZ).rank())
    out={'status':'SIGN_CLOSURE_PRODUCED','protocol_sha256':sha256(raw).hexdigest(),
         'source_sha256':{name:sha(path) for name,path in sources.items()},
         'p':20023,'subgroup_order':4021,'orbit_count':len(keys),'base_row_count':len(base_rows),
         'sign_row_count':len(sign_rows),'sign_rows':signs,
         'baseline_anchor_rank':int(before.rank()),'combined_anchor_rank':int(after.rank()),
         'baseline_exact_anchor_rank':exact_before,'combined_exact_anchor_rank':exact_after,
         'baseline_nullity':b_null,'combined_nullity':a_null,
         'baseline_ambiguous_indices':b_support,'combined_ambiguous_indices':a_support,
         'determined_orbit_count':len(keys)-len(a_support),'prepared_table_count':len(table),
         'candidate_id':None,'timing_claim':None}
    (HERE/'result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:out[k] for k in ('sign_row_count','baseline_anchor_rank','combined_anchor_rank',
                                        'baseline_nullity','combined_nullity','combined_ambiguous_indices',
                                        'prepared_table_count')},sort_keys=True))

if __name__=='__main__':main()
