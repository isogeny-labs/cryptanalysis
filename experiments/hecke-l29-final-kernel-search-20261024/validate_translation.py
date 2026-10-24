"""Pure-integer replay of zero-seed generator-shift closure."""
from hashlib import sha256
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
def sha(path):return sha256(path.read_bytes()).hexdigest()
p=20023;r=4021
def decode(a):return None if tuple(a)==(-1,-1) else tuple(a)
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
    protocol=json.loads((HERE/'translation_validation_protocol.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_INTEGER_TRANSLATION_VALIDATION'
    paths={'result':HERE/'translation_result.json','kernel':HERE/'kernel_result.json',
           'rank':ROOT/'hecke-l29-trace-orbits-20261024/all_rank_result.json',
           'frontier':ROOT/'hecke-torsion-frontiers-20261024/p20023.result.json',
           'seed':ROOT/'hecke-torsion-frontiers-20261024/p20023.seed.result.json',
           'sign':ROOT/'hecke-sign-closure-20261024/result.json',
           'l23':ROOT/'hecke-l23-targeted-20261024/result.v2.json',
           'l29':ROOT/'hecke-degree-next-screen-20261024/l29_result.json'}
    data={k:json.loads(v.read_text()) for k,v in paths.items()}
    result=data['result'];kernel=data['kernel']
    keys=[tuple(a) for a in result['column_representatives']]
    assert keys==[tuple(a) for a in kernel['column_representatives']]
    logs=result['logs_by_column'];assert len(keys)==len(logs)==3959
    idx={a:i for i,a in enumerate(keys)}
    old=[tuple(a) for a in data['frontier']['column_representatives']]
    l23=[tuple(a) for a in data['l23']['all_column_representatives']]
    l29=[tuple(a) for a in data['l29']['all_column_representatives']]
    T=(5,5);assert mul(5,T) is None
    def orbit(Q):return min((-1,-1) if add(Q,mul(k,T)) is None else add(Q,mul(k,T))
                            for k in range(5))
    A=(1,8630);G=mul(5,A);assert mul(r,G) is None
    anchor=idx[orbit(A)];assert logs[anchor]==1
    projected={}
    for i,rep in enumerate(keys):
        Q=mul(5,decode(rep));assert Q not in projected
        projected[Q]=i
    support={int(i):v for i,v in kernel['kernel_support'].items()}
    assert len(support)==4 and kernel['old_support_indices']==[1391,1392,2593,2594]
    assert support[kernel['normalization_column']]==1

    def remap(row,reps):return {idx[reps[int(j)]]:int(v) for j,v in row.items()}
    rows=[remap(z['coefficients'],old) for z in data['seed']['accepted_rows']]
    rows += [remap(z,old) for z in data['frontier']['rows']]
    rows += [remap(z['coefficients'],old) for z in data['sign']['sign_rows']]
    rows += [remap(z['coefficients'],l23) for z in data['l23']['accepted_rows']]
    rows += [remap(z['coefficients'],l29) for z in data['l29']['accepted_rows']]
    rows += [{int(j):int(v) for j,v in z['coefficients'].items()}
             for z in data['rank']['trace_rows']]
    assert len(rows)==7602
    for row in rows:
        assert sum(v*support.get(i,0) for i,v in row.items())%r==0
        assert sum(v*logs[i] for i,v in row.items())%r==0
    assert support.get(anchor,0)==0

    chosen=[]
    for old_i in kernel['old_support_indices']:
        source_i=idx[old[old_i]];Q=mul(5,decode(old[old_i]))
        for offset in (1,2):
            shifted=add(Q,mul(offset,G));hit=projected.get(shifted)
            if hit is not None and hit not in support:
                chosen.append((old_i,source_i,offset,hit,Q,shifted));break
        else:raise AssertionError(f'no known shift for {old_i}')
    assert len(chosen)==len(result['selected_rows'])==4
    for expected,saved in zip(chosen,result['selected_rows']):
        old_i,source_i,offset,hit,Q,shifted=expected
        assert (saved['old_orbit_index'],saved['source_column'],saved['offset'],saved['hit_column']) == (old_i,source_i,offset,hit)
        assert saved['source_projected_point']==encode(Q)
        assert saved['shifted_point']==encode(shifted)
        assert add(Q,mul(offset,G))==mul(5,decode(keys[hit]))
        coeff={int(i):int(v) for i,v in saved['coefficients'].items()}
        assert coeff.get(source_i)==1 and coeff.get(hit)==-1
        assert sum(v*logs[i] for i,v in coeff.items())%r==0
        assert sum(v*support.get(i,0) for i,v in coeff.items())%r!=0

    table={}
    for rep,scalar in zip(keys,logs):
        Q=mul(5,decode(rep));assert mul(scalar,G)==Q
        table[Q]=scalar
    assert len(table)==3959
    offsets={'0':0,'1':0,'2':0,'uncovered':0}
    for scalar in range(r):
        target=mul(scalar,G)
        for j in range(3):
            hit=table.get(add(target,mul(j,G)))
            if hit is not None:
                assert (hit-j)%r==scalar
                offsets[str(j)]+=1;break
        else:offsets['uncovered']+=1
    assert offsets==result['offset_histogram']
    out={'status':'PASS_INTEGER_ZERO_SEED_TRANSLATION_REPLAY',
         'shift_identities_replayed':len(chosen),'baseline_relations_replayed':len(rows),
         'orbit_logs_replayed':len(logs),'subgroup_targets_replayed':r,
         'offset_histogram':offsets,'source_sha256':{k:sha(v) for k,v in paths.items()}}
    (HERE/'translation_validation.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:out[k] for k in ('status','shift_identities_replayed','orbit_logs_replayed','subgroup_targets_replayed')},sort_keys=True))

if __name__=='__main__':main()
