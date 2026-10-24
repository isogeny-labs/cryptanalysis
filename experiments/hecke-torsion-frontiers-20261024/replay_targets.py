"""Independent integer-group relation replay and fixed one-target controls."""
from hashlib import sha256
import json
from math import gcd
from pathlib import Path

HERE=Path(__file__).resolve().parent
def sha(p):return sha256(p.read_bytes()).hexdigest()

def run(case,p,h,order,anchor,seed,boundary):
    protocol=json.loads((HERE/'replay.protocol.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_TARGET_REPLAY'
    assert protocol['source_sha256']['script']==sha(HERE/'replay_targets.py')
    assert protocol['source_sha256'][case]==sha(HERE/(case+'.result.json'))
    if case=='p20023':assert protocol['source_sha256']['p20023_seed']==sha(HERE/'p20023.seed.result.json')
    data=json.loads((HERE/(case+'.result.json')).read_text())
    seed_data=json.loads((HERE/'p20023.seed.result.json').read_text()) if case=='p20023' else None
    def pt(a):return None if tuple(a)==(-1,-1) else tuple(a)
    def key(Q):return (-1,-1) if Q is None else Q
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
        R=(x,y);assert on(R);return R
    def mul(k,Q):
        if k<0:return mul(-k,neg(Q))
        R=None
        while k:
            if k&1:R=add(R,Q)
            Q=add(Q,Q);k>>=1
        return R
    G=mul(h,anchor);assert on(anchor) and G is not None and mul(order,G) is None
    scalars={};Q=None
    for k in range(order):
        assert Q not in scalars
        scalars[Q]=k;Q=add(Q,G)
    assert Q is None and len(scalars)==order
    keys=[pt(x) for x in data['column_representatives']]
    logs=[scalars[mul(h,P)] for P in keys]
    rows=([r['coefficients'] for r in seed_data['accepted_rows']] if seed_data else [])+data['rows']
    assert all(sum(int(v)*logs[int(j)] for j,v in row.items())%order==0 for row in rows)
    retained={tuple(x) for x in data['boundary_representatives'][boundary]}
    projected={mul(h,pt(x)) for x in retained}
    k=int.from_bytes(sha256(seed.encode()).digest(),'big')%order
    target=mul(k,G);assert target in scalars and scalars[target]==k
    def rho():
        def step(state):
            X,a,b=state
            lane=0 if X is None else X[0]%3
            if lane==0:return add(X,G),(a+1)%order,b
            if lane==1:return add(X,target),a,(b+1)%order
            return add(X,X),(2*a)%order,(2*b)%order
        slow=(None,0,0);fast=slow;steps=0
        for _ in range(10*order):
            slow=step(slow);fast=step(step(fast));steps+=3
            if slow[0]==fast[0]:
                denominator=(fast[2]-slow[2])%order
                if gcd(denominator,order)==1:
                    answer=((slow[1]-fast[1])*pow(denominator,-1,order))%order
                    if mul(answer,G)==target:return answer,steps
        return None,steps
    answer,walk_steps=rho();assert answer==k
    out={'status':'PASS_INTEGER_RELATION_AND_SAME_TARGET_RHO_REPLAY','case':case,
         'source_sha256':sha(HERE/(case+'.result.json')),'p':p,'projection_multiplier':h,
         'subgroup_order':order,'generator':key(G),'anchor':anchor,
         'rows_replayed':len(rows),'column_count':len(keys),
         'retained_boundary':boundary,'retained_projected_target_count':len(projected),
         'target_seed':seed,'target_scalar_fixture':k,'target_point':key(target),
         'target_replay':mul(k,G)==target,'rho_recovered_scalar':answer,
         'rho_walk_steps':walk_steps,'candidate_id':None,'timing_claim':None}
    (HERE/(case+'.target_replay.json')).write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True))

if __name__=='__main__':
    run('p12043',12043,40,299,(10,3005),'hecke-layer5-prospective-one-target-20261023','original')
    run('p20023',20023,5,4021,(1,8630),'hecke-p20023-prospective-one-target-v1','seed')
