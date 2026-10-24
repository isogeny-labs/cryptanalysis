"""Pure-integer replay of the two pre-degree-23 translation controls."""
from hashlib import sha256
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
def sha(path):return sha256(path.read_bytes()).hexdigest()
p=20023;r=4021
def decode(a):return None if tuple(a)==(-1,-1) else tuple(a)
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
    protocol=json.loads((HERE/'control_validation_protocol.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_EARLIER_TABLE_INTEGER_REPLAY'
    paths={'control':HERE/'control_result.json',
           'frontier':ROOT/'hecke-torsion-frontiers-20261024/p20023.result.json',
           'seed':ROOT/'hecke-torsion-frontiers-20261024/p20023.seed.result.json',
           'sign':ROOT/'hecke-sign-closure-20261024/result.json'}
    data={k:json.loads(v.read_text()) for k,v in paths.items()}
    keys=[tuple(a) for a in data['control']['column_representatives']]
    assert keys==[tuple(a) for a in data['frontier']['column_representatives']]
    assert len(keys)==3949
    T=(5,5);assert mul(5,T) is None
    def orbit(P):return min((-1,-1) if add(P,mul(k,T)) is None else add(P,mul(k,T))
                            for k in range(5))
    G=mul(5,(1,8630));assert mul(r,G) is None
    idx={a:i for i,a in enumerate(keys)};anchor=idx[orbit((1,8630))]
    projected={}
    for i,rep in enumerate(keys):
        Q=mul(5,decode(rep));assert Q not in projected
        projected[Q]=i
    base=[z['coefficients'] for z in data['seed']['accepted_rows']]+data['frontier']['rows']
    sign=[z['coefficients'] for z in data['sign']['sign_rows']]
    outcomes={}
    for stage,rows in [('seed_plus_degree2_3_hecke',base),
                       ('seed_plus_degree2_3_hecke_plus_inversion',base+sign)]:
        saved=data['control']['results'][stage]
        logs=saved['logs_by_column'];assert len(logs)==len(keys)
        assert logs[anchor]==1 and saved['generic_seed_logs']==0
        support=set(saved['kernel_support_columns'])
        assert len(saved['selected_rows'])==saved['baseline_nullity']
        for record in saved['selected_rows']:
            i=record['source_column'];j=record['offset'];hit=record['hit_column']
            assert i in support and hit not in support and j in (1,2)
            source=mul(5,decode(keys[i]));shifted=add(source,mul(j,G))
            assert shifted==mul(5,decode(keys[hit]))
            assert record['source_projected']==([-1,-1] if source is None else list(source))
            assert record['shifted_point']==([-1,-1] if shifted is None else list(shifted))
            coeff={int(k):int(v) for k,v in record['coefficients'].items()}
            assert coeff.get(i)==1 and coeff.get(hit)==-1
            assert sum(v*logs[k] for k,v in coeff.items())%r==0
        for row in rows:
            assert sum(int(v)*logs[int(k)] for k,v in row.items())%r==0
        table={}
        for rep,scalar in zip(keys,logs):
            Q=mul(5,decode(rep));assert mul(scalar,G)==Q
            table[Q]=scalar
        offsets={'0':0,'1':0,'2':0,'uncovered':0}
        for scalar in range(r):
            target=mul(scalar,G)
            for j in range(3):
                hit=table.get(add(target,mul(j,G)))
                if hit is not None:
                    assert (hit-j)%r==scalar
                    offsets[str(j)]+=1;break
            else:offsets['uncovered']+=1
        assert offsets['uncovered']==0
        outcomes[stage]={'selected_shifts':len(saved['selected_rows']),
                         'orbit_logs_replayed':len(logs),
                         'relation_rows_replayed':len(rows),
                         'subgroup_targets_replayed':r,'offset_histogram':offsets}
    out={'status':'PASS_INTEGER_EARLIER_TABLE_TRANSLATION_REPLAY',
         'stages':outcomes,'source_sha256':{k:sha(v) for k,v in paths.items()}}
    (HERE/'control_validation.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v['selected_shifts'] for k,v in outcomes.items()},sort_keys=True))

if __name__=='__main__':main()
