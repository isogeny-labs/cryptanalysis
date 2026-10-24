"""Complete the combined 54-source trace table from one generic seed log."""
from hashlib import sha256
from math import isqrt
import json
from pathlib import Path
from sage.all import EllipticCurve, GF, matrix, vector

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
def sha(path):return sha256(path.read_bytes()).hexdigest()
def key(P):return (-1,-1) if P.is_zero() else (int(P[0]),int(P[1]))

def main():
    path=HERE/'all_completion_protocol.json';raw=path.read_bytes()
    protocol=json.loads(raw);assert protocol['status']=='FROZEN_BEFORE_COMBINED_ONE_SEED_COMPLETION'
    paths={'rank':HERE/'all_rank_result.json',
           'frontier':ROOT/'hecke-torsion-frontiers-20261024/p20023.result.json',
           'seed':ROOT/'hecke-torsion-frontiers-20261024/p20023.seed.result.json',
           'sign':ROOT/'hecke-sign-closure-20261024/result.json',
           'l23':ROOT/'hecke-l23-targeted-20261024/result.v2.json',
           'l29':ROOT/'hecke-degree-next-screen-20261024/l29_result.json'}
    data={k:json.loads(v.read_text()) for k,v in paths.items()}
    old=[tuple(x) for x in data['frontier']['column_representatives']]
    l23=[tuple(x) for x in data['l23']['all_column_representatives']]
    l29=[tuple(x) for x in data['l29']['all_column_representatives']]
    keys=sorted(set(l29)|{tuple(x) for x in data['rank']['additional_representatives']})
    assert len(keys)==3959
    idx={a:i for i,a in enumerate(keys)}
    def remap(row,reps):return {str(idx[reps[int(j)]]):v for j,v in row.items()}
    rows=[remap(r['coefficients'],old) for r in data['seed']['accepted_rows']]
    rows += [remap(r,old) for r in data['frontier']['rows']]
    rows += [remap(r['coefficients'],old) for r in data['sign']['sign_rows']]
    rows += [remap(r['coefficients'],l23) for r in data['l23']['accepted_rows']]
    rows += [remap(r['coefficients'],l29) for r in data['l29']['accepted_rows']]
    rows += [r['coefficients'] for r in data['rank']['trace_rows']]
    E=EllipticCurve(GF(20023),[0,-1,1,-10,-20]);O=E(0);T=E([5,5,1])
    def point(a):return O if a==(-1,-1) else E([*a,1])
    def orbit(P):return min(key(P+k*T) for k in range(5))
    anchor=idx[orbit(point(tuple(protocol['anchor_point'])))]
    G=5*point(tuple(protocol['anchor_point']));assert 4021*G==O
    entries={(i,int(j)):v for i,row in enumerate(rows) for j,v in row.items()}
    entries[(len(rows),anchor)]=1
    A=matrix(GF(4021),len(rows)+1,len(keys),entries,sparse=False)
    basis=A.right_kernel().basis();assert len(basis)==1
    support=sorted(basis[0].support())
    old_set=set(old)
    ambiguous=sorted(old.index(keys[i]) for i in support if keys[i] in old_set)
    assert ambiguous==protocol['expected_ambiguous_old_indices']
    selected=next(i for i in support if keys[i] in old_set)
    m=isqrt(4021)+1;baby={};Q=O
    for j in range(m):
        assert key(Q) not in baby
        baby[key(Q)]=j;Q+=G
    target=5*point(keys[selected]);seed_projected=key(target);R=target;step=-(m*G)
    for giant in range(m+1):
        small=baby.get(key(R))
        if small is not None:
            scalar=(giant*m+small)%4021
            assert scalar*G==target
            break
        R+=step
    else:raise AssertionError('BSGS exhausted')
    augmented=dict(entries);augmented[(len(rows)+1,selected)]=1
    M=matrix(GF(4021),len(rows)+2,len(keys),augmented,sparse=False)
    rhs=vector(GF(4021),[0]*len(rows)+[1,scalar])
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
    out={'status':'PASS_ONE_GENERIC_SEED_COMBINED_TRACE_TABLE',
         'protocol_sha256':sha(path),'source_sha256':{k:sha(v) for k,v in paths.items()},
         'baseline_rank':int(A.rank()),'baseline_nullity':1,
         'ambiguous_old_indices':ambiguous,
         'seed_log_method':'generic BSGS','baby_table_entries':len(baby),
         'seed_log':{'column_index':selected,'orbit_representative':keys[selected],
                     'projected_point':seed_projected,'scalar':scalar,'giant_steps':giant},
         'augmented_rank':int(M.rank()),'column_count':len(keys),
         'all_column_representatives':keys,'logs_by_column':[int(v) for v in logs],
         'prepared_table_count':len(table),'offset_histogram':offsets,
         'candidate_id':None,'timing_claim':None}
    (HERE/'all_completion_result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'seed_log':out['seed_log'],'augmented_rank':out['augmented_rank'],
                      'offset_histogram':offsets},sort_keys=True),flush=True)

if __name__=='__main__':main()
