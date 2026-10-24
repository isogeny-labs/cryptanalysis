"""Two generic seed logs complete the sign-constrained degree-23 relation table."""
from hashlib import sha256
from math import isqrt
import json
from pathlib import Path
from sage.all import EllipticCurve, GF, matrix, vector

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PRIOR=ROOT/'hecke-torsion-frontiers-20261024'
SIGN=ROOT/'hecke-sign-closure-20261024'
def sha(path):return sha256(path.read_bytes()).hexdigest()
def key(P):return (-1,-1) if P.is_zero() else (int(P[0]),int(P[1]))

def main():
    raw=(HERE/'completion_protocol.v2.json').read_bytes();protocol=json.loads(raw)
    assert protocol['status']=='FROZEN_BEFORE_L23_TWO_SEED_COMPLETION'
    sources={'completion':HERE/'complete_v2.py','l23_result':HERE/'result.v2.json',
             'frontier':PRIOR/'p20023.result.json','seed':PRIOR/'p20023.seed.result.json',
             'sign':SIGN/'result.json'}
    assert protocol['source_sha256']=={name:sha(path) for name,path in sources.items()}
    data=json.loads(sources['l23_result'].read_text());frontier=json.loads(sources['frontier'].read_text())
    seed=json.loads(sources['seed'].read_text());sign=json.loads(sources['sign'].read_text())
    keys=[tuple(x) for x in data['all_column_representatives']];idx={a:i for i,a in enumerate(keys)}
    old=[tuple(x) for x in frontier['column_representatives']]
    def remap(row):return {str(idx[old[int(j)]]):v for j,v in row.items()}
    rows=([remap(r['coefficients']) for r in seed['accepted_rows']]+[remap(r) for r in frontier['rows']]
          +[remap(r['coefficients']) for r in sign['sign_rows']]
          +[r['coefficients'] for r in data['accepted_rows']])
    assert len(rows)==7546 and len(keys)==3953
    E=EllipticCurve(GF(20023),[0,-1,1,-10,-20]);O=E(0);T=E([5,5,1])
    def point(a):return O if a==(-1,-1) else E([a[0],a[1],1])
    def orbit(P):return min(key(P+k*T) for k in range(5))
    anchor=idx[orbit(point((1,8630)))];G=5*point((1,8630))
    assert 4021*G==O
    entries={(i,int(j)):v for i,row in enumerate(rows) for j,v in row.items()}
    entries[(len(rows),anchor)]=1
    A=matrix(GF(4021),len(rows)+1,len(keys),entries,sparse=False)
    basis=A.right_kernel().basis();assert len(basis)==2
    support=sorted(set().union(*(set(v.support()) for v in basis)))
    assert sorted(old.index(keys[i]) for i in support if keys[i] in set(old))==protocol['expected_ambiguous_old_indices']
    chosen=[];evaluations=[]
    for i in support:
        candidate=[basis[j][i] for j in range(2)]
        if matrix(GF(4021),evaluations+[candidate]).rank()>len(evaluations):
            chosen.append(i);evaluations.append(candidate)
        if len(chosen)==2:break
    assert len(chosen)==2
    m=isqrt(4021)+1;baby={};Q=O
    for j in range(m):
        assert key(Q) not in baby
        baby[key(Q)]=j;Q+=G
    step=-(m*G)
    def bsgs(target):
        R=target
        for giant in range(m+1):
            small=baby.get(key(R))
            if small is not None:
                k=(giant*m+small)%4021
                assert k*G==target
                return k,giant
            R+=step
        raise AssertionError('BSGS exhausted')
    seeds=[]
    for i in chosen:
        target=5*point(keys[i]);k,giants=bsgs(target)
        seeds.append({'column_index':i,'orbit_representative':keys[i],
                      'projected_point':key(target),'scalar':k,'giant_steps':giants})
    augmented=dict(entries)
    for j,s in enumerate(seeds):augmented[(len(rows)+1+j,s['column_index'])]=1
    M=matrix(GF(4021),len(rows)+1+len(seeds),len(keys),augmented,sparse=False)
    rhs=vector(GF(4021),[0]*len(rows)+[1]+[s['scalar'] for s in seeds])
    assert M.rank()==len(keys)
    logs=M.solve_right(rhs);assert M*logs==rhs
    table={}
    for i,rep in enumerate(keys):
        P=5*point(rep);k=int(logs[i]);assert k*G==P
        assert key(P) not in table
        table[key(P)]=k
    offsets={'0':0,'1':0,'2':0,'uncovered':0}
    for k in range(4021):
        target=k*G
        for j in range(3):
            hit=table.get(key(target+j*G))
            if hit is not None:
                assert (hit-j)%4021==k
                offsets[str(j)]+=1;break
        else:offsets['uncovered']+=1
    assert offsets['uncovered']==0
    out={'status':'PASS_L23_TWO_GENERIC_SEEDS_COMPLETE_REACHABLE_TABLE',
         'protocol_sha256':sha256(raw).hexdigest(),
         'source_sha256':{name:sha(path) for name,path in sources.items()},
         'baseline_nullity':len(basis),'selected_seed_indices':chosen,
         'generic_seed_log_method':'shared-baby-table BSGS',
         'baby_table_entries':len(baby),'seed_logs':seeds,
         'augmented_rank':int(M.rank()),'column_count':len(keys),
         'logs_by_column':[int(v) for v in logs],
         'prepared_table_count':len(table),'offset_histogram':offsets,
         'candidate_id':None,'timing_claim':None}
    (HERE/'completion.v2.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('selected_seed_indices','seed_logs','augmented_rank',
                  'prepared_table_count','offset_histogram')},sort_keys=True))

if __name__=='__main__':main()
