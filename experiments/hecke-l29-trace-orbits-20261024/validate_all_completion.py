"""Pure-integer replay of the combined 54-source trace completion."""
from hashlib import sha256
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
def sha(p):return sha256(p.read_bytes()).hexdigest()
p=20023;r=4021

def decode(a):return None if a==[-1,-1] else tuple(a)
def encode(a):return [-1,-1] if a is None else list(a)
def on(Q):
    if Q is None:return True
    x,y=Q;return (y*y+y-x*x*x+x*x+10*x+20)%p==0
def neg(Q):return None if Q is None else (Q[0],(-Q[1]-1)%p)
def add(A,B):
    if A is None:return B
    if B is None:return A
    x1,y1=A;x2,y2=B
    if x1==x2 and (y1+y2+1)%p==0:return None
    if A==B:s=((3*x1*x1-2*x1-10)*pow((2*y1+1)%p,-1,p))%p
    else:s=((y2-y1)*pow((x2-x1)%p,-1,p))%p
    c=(y1-s*x1)%p;x=(s*s+1-x1-x2)%p;y=(-s*x-c-1)%p
    Q=(x,y);assert on(Q);return Q
def mul(k,Q):
    if k<0:return mul(-k,neg(Q))
    R=None
    while k:
        if k&1:R=add(R,Q)
        Q=add(Q,Q);k>>=1
    return R

def main():
    protocol=json.loads((HERE/'all_completion_validation_protocol.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_COMBINED_INTEGER_COMPLETION_VALIDATION'
    paths={'validator':HERE/'validate_all_completion.py','completion':HERE/'all_completion_result.json',
           'rank':HERE/'all_rank_result.json',
           'frontier':ROOT/'hecke-torsion-frontiers-20261024/p20023.result.json',
           'seed':ROOT/'hecke-torsion-frontiers-20261024/p20023.seed.result.json',
           'sign':ROOT/'hecke-sign-closure-20261024/result.json',
           'l23':ROOT/'hecke-l23-targeted-20261024/result.v2.json',
           'l29':ROOT/'hecke-degree-next-screen-20261024/l29_result.json'}
    assert protocol['source_sha256']=={k:sha(v) for k,v in paths.items()}
    data={k:json.loads(v.read_text()) for k,v in paths.items() if k!='validator'}
    comp=data['completion'];keys=[tuple(a) for a in comp['all_column_representatives']]
    logs=comp['logs_by_column'];assert len(keys)==len(logs)==3959
    idx={a:i for i,a in enumerate(keys)}
    T=(5,5);assert mul(5,T) is None
    def orbit(P):return min((-1,-1) if add(P,mul(k,T)) is None else add(P,mul(k,T))
                            for k in range(5))
    A=(1,8630);G=mul(5,A);assert G is not None and mul(r,G) is None
    assert logs[idx[orbit(A)]]==1
    seed=comp['seed_log'];sidx=seed['column_index']
    assert keys[sidx]==tuple(seed['orbit_representative'])
    assert encode(mul(5,decode(list(keys[sidx]))))==seed['projected_point']
    assert mul(seed['scalar'],G)==decode(seed['projected_point'])
    assert logs[sidx]==seed['scalar']==3006
    table={}
    for rep,scalar in zip(keys,logs):
        P=mul(5,decode(list(rep)))
        assert mul(scalar,G)==P
        assert P not in table
        table[P]=scalar
    assert len(table)==3959

    old=[tuple(a) for a in data['frontier']['column_representatives']]
    l23=[tuple(a) for a in data['l23']['all_column_representatives']]
    l29=[tuple(a) for a in data['l29']['all_column_representatives']]
    def check(row,reps):
        return sum(int(v)*logs[idx[reps[int(j)]]] for j,v in row.items())%r==0
    for row in data['seed']['accepted_rows']:assert check(row['coefficients'],old)
    for row in data['frontier']['rows']:assert check(row,old)
    for row in data['sign']['sign_rows']:assert check(row['coefficients'],old)
    for row in data['l23']['accepted_rows']:assert check(row['coefficients'],l23)
    for row in data['l29']['accepted_rows']:assert check(row['coefficients'],l29)
    for row in data['rank']['trace_rows']:assert check(row['coefficients'],keys)

    offsets={'0':0,'1':0,'2':0,'uncovered':0}
    for scalar in range(r):
        target=mul(scalar,G)
        for j in range(3):
            hit=table.get(add(target,mul(j,G)))
            if hit is not None:
                assert (hit-j)%r==scalar
                offsets[str(j)]+=1;break
        else:offsets['uncovered']+=1
    assert offsets==comp['offset_histogram']
    result={'status':'PASS_INTEGER_COMBINED_ONE_SEED_COMPLETION_REPLAY',
            'orbit_logs_replayed':len(keys),'subgroup_targets_replayed':r,
            'seed_scalar':seed['scalar'],'offset_histogram':offsets,
            'relation_rows_replayed':sum([len(data['seed']['accepted_rows']),len(data['frontier']['rows']),
                                          len(data['sign']['sign_rows']),len(data['l23']['accepted_rows']),
                                          len(data['l29']['accepted_rows']),len(data['rank']['trace_rows'])]),
            'source_sha256':{k:sha(v) for k,v in paths.items()}}
    (HERE/'all_completion_validation.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ('status','orbit_logs_replayed','subgroup_targets_replayed','relation_rows_replayed')},sort_keys=True))

if __name__=='__main__':main()
