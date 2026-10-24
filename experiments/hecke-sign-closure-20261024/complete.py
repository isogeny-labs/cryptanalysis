"""Determine the three residual orbit logs and solve the reachable table."""
from hashlib import sha256
from math import isqrt
import json
from pathlib import Path
from sage.all import EllipticCurve, GF, matrix, vector

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'hecke-torsion-frontiers-20261024'
def sha(path):return sha256(path.read_bytes()).hexdigest()
def key(P):return (-1,-1) if P.is_zero() else (int(P[0]),int(P[1]))

def main():
    raw=(HERE/'completion_protocol.json').read_bytes();protocol=json.loads(raw)
    assert protocol['status']=='FROZEN_BEFORE_THREE_SEED_COMPLETION'
    sources={'completion':HERE/'complete.py','sign_result':HERE/'result.json',
             'frontier':PRIOR/'p20023.result.json','seed':PRIOR/'p20023.seed.result.json'}
    assert protocol['source_sha256']=={name:sha(path) for name,path in sources.items()}
    sign=json.loads(sources['sign_result'].read_text());frontier=json.loads(sources['frontier'].read_text())
    seed=json.loads(sources['seed'].read_text())
    keys=[tuple(x) for x in frontier['column_representatives']];index={a:i for i,a in enumerate(keys)}
    rows=([r['coefficients'] for r in seed['accepted_rows']]+frontier['rows']+
          [r['coefficients'] for r in sign['sign_rows']])
    assert len(rows)==7540 and len(keys)==3949
    E=EllipticCurve(GF(20023),[0,-1,1,-10,-20]);O=E(0);T=E([5,5,1])
    def point(a):return O if a==(-1,-1) else E([a[0],a[1],1])
    def orbit(P):return min(key(P+k*T) for k in range(5))
    anchor=index[orbit(point((1,8630)))];G=5*point((1,8630))
    assert 4021*G==O
    entries={(i,int(j)):v for i,row in enumerate(rows) for j,v in row.items()}
    entries[(len(rows),anchor)]=1
    A=matrix(GF(4021),len(rows)+1,len(keys),entries,sparse=False)
    basis=A.right_kernel().basis();assert len(basis)==3
    support=sorted(set().union(*(set(v.support()) for v in basis)))
    assert support==sign['combined_ambiguous_indices']
    chosen=[];vectors=[]
    for i in support:
        candidate=[basis[j][i] for j in range(len(basis))]
        trial=matrix(GF(4021),vectors+[candidate])
        if trial.rank()>len(vectors):
            chosen.append(i);vectors.append(candidate)
        if len(chosen)==len(basis):break
    assert len(chosen)==3 and matrix(GF(4021),vectors).rank()==3
    m=isqrt(4021)+1
    baby={};Q=O
    for j in range(m):
        assert key(Q) not in baby
        baby[key(Q)]=j;Q+=G
    giant_step=-(m*G)
    def bsgs(target):
        R=target
        for giant in range(m+1):
            small=baby.get(key(R))
            if small is not None:
                answer=(giant*m+small)%4021
                assert answer*G==target
                return answer,giant
            R+=giant_step
        raise AssertionError('BSGS exhausted')
    seeds=[]
    for i in chosen:
        P=point(keys[i]);target=5*P;answer,giants=bsgs(target)
        seeds.append({'column_index':i,'orbit_representative':keys[i],
                      'projected_point':key(target),'scalar':answer,'giant_steps':giants})
    all_entries=dict(entries)
    for k,s in enumerate(seeds):all_entries[(len(rows)+1+k,s['column_index'])]=1
    M=matrix(GF(4021),len(rows)+1+len(seeds),len(keys),all_entries,sparse=False)
    rhs=vector(GF(4021),[0]*len(rows)+[1]+[s['scalar'] for s in seeds])
    assert M.rank()==len(keys)
    logs=M.solve_right(rhs);assert M*logs==rhs
    prepared={}
    for i,rep in enumerate(keys):
        x=key(5*point(rep));v=int(logs[i]);assert v*G==5*point(rep)
        assert x not in prepared
        prepared[x]=v
    assert len(prepared)==3949
    offset_hist={'0':0,'1':0,'2':0,'uncovered':0}
    for k in range(4021):
        target=k*G
        for offset in range(3):
            shifted=key(target+offset*G)
            if shifted in prepared:
                assert (prepared[shifted]-offset)%4021==k
                offset_hist[str(offset)]+=1
                break
        else:offset_hist['uncovered']+=1
    assert offset_hist['uncovered']==0
    out={'status':'PASS_THREE_GENERIC_SEEDS_COMPLETE_REACHABLE_TABLE',
         'protocol_sha256':sha256(raw).hexdigest(),
         'source_sha256':{name:sha(path) for name,path in sources.items()},
         'baseline_nullity':len(basis),'selected_seed_indices':chosen,
         'generic_seed_log_method':'shared-baby-table BSGS',
         'baby_table_entries':len(baby),'seed_logs':seeds,
         'augmented_rank':int(M.rank()),'column_count':len(keys),
         'logs_by_column':[int(v) for v in logs],
         'prepared_table_count':len(prepared),'offset_histogram':offset_hist,
         'candidate_id':None,'timing_claim':None}
    (HERE/'completion.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:out[k] for k in ('selected_seed_indices','baby_table_entries','seed_logs',
                 'augmented_rank','prepared_table_count','offset_histogram')},sort_keys=True))

if __name__=='__main__':main()
