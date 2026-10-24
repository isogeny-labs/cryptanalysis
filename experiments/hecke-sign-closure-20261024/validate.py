"""Independent integer-curve replay of sign relations and three-seed completion."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from sage.all import GF, matrix

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'hecke-torsion-frontiers-20261024'
def sha(path):return sha256(path.read_bytes()).hexdigest()

def main():
    protocol=json.loads((HERE/'validation_protocol.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_SIGN_VALIDATOR'
    sources={'validator':HERE/'validate.py','sign_result':HERE/'result.json',
             'completion':HERE/'completion.json','frontier':PRIOR/'p20023.result.json',
             'seed':PRIOR/'p20023.seed.result.json'}
    assert protocol['source_sha256']=={name:sha(path) for name,path in sources.items()}
    sign=json.loads(sources['sign_result'].read_text())
    completion=json.loads(sources['completion'].read_text())
    frontier=json.loads(sources['frontier'].read_text());seed=json.loads(sources['seed'].read_text())
    p=20023
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
    T=(5,5);assert on(T) and mul(5,T) is None
    def orbit(Q):return min(key(add(Q,mul(k,T))) for k in range(5))
    keys=[tuple(x) for x in frontier['column_representatives']];idx={x:i for i,x in enumerate(keys)}
    assert len(keys)==3949
    signs=sign['sign_rows'];pairs=set()
    for rec in signs:
        i,j=rec['indices'];assert 0<=i<=j<len(keys)
        pair=(i,j);assert pair not in pairs;pairs.add(pair)
        P,Q=pt(keys[i]),pt(keys[j]);assert on(P) and on(Q)
        assert orbit(neg(P))==keys[j] and orbit(neg(Q))==keys[i]
        assert add(mul(5,P),mul(5,Q)) is None
        expected={str(i):2} if i==j else {str(i):1,str(j):1}
        assert rec['coefficients']==expected
    assert len(pairs)==sign['sign_row_count']==1975
    G=mul(5,(1,8630));assert on(G) and mul(4021,G) is None
    scalars={};Q=None
    for k in range(4021):
        assert Q not in scalars
        scalars[Q]=k;Q=add(Q,G)
    assert Q is None and len(scalars)==4021
    logs=completion['logs_by_column'];assert len(logs)==len(keys)
    projected={}
    for i,rep in enumerate(keys):
        Q=mul(5,pt(rep));assert scalars[Q]==logs[i]
        assert Q not in projected
        projected[Q]=logs[i]
    assert len(projected)==3949
    rows=[r['coefficients'] for r in seed['accepted_rows']]+frontier['rows']
    assert all(sum(int(v)*logs[int(j)] for j,v in row.items())%4021==0 for row in rows)
    assert all(sum(int(v)*logs[int(j)] for j,v in row['coefficients'].items())%4021==0 for row in signs)
    for rec in completion['seed_logs']:
        i=rec['column_index'];assert keys[i]==tuple(rec['orbit_representative'])
        assert logs[i]==rec['scalar'] and mul(rec['scalar'],G)==mul(5,pt(keys[i]))
    assert completion['selected_seed_indices']==[r['column_index'] for r in completion['seed_logs']]
    # Independently reconstruct the augmented finite-field rank.
    all_rows=rows+[r['coefficients'] for r in signs]
    entries={(i,int(j)):v for i,row in enumerate(all_rows) for j,v in row.items()}
    anchor=idx[orbit((1,8630))];entries[(len(all_rows),anchor)]=1
    for k,i in enumerate(completion['selected_seed_indices']):entries[(len(all_rows)+1+k,i)]=1
    M=matrix(GF(4021),len(all_rows)+1+len(completion['seed_logs']),len(keys),entries,sparse=False)
    assert int(M.rank())==len(keys)==completion['augmented_rank']
    histogram=Counter();missing=[]
    for k in range(4021):
        target=mul(k,G)
        for off in range(3):
            shifted=add(target,mul(off,G))
            if shifted in projected:
                assert (projected[shifted]-off)%4021==k
                histogram[str(off)]+=1;break
        else:missing.append(k)
    assert not missing and {str(j):histogram[str(j)] for j in range(3)}|{'uncovered':0}==completion['offset_histogram']
    out={'status':'PASS_SIGN_AND_THREE_SEED_INTEGER_REPLAY',
         'protocol_sha256':sha(HERE/'validation_protocol.json'),
         'sign_result_sha256':sha(HERE/'result.json'),
         'completion_sha256':sha(HERE/'completion.json'),
         'validator_sha256':sha(HERE/'validate.py'),
         'sign_rows_checked':len(signs),'hecke_rows_checked':len(rows),
         'seed_logs_checked':len(completion['seed_logs']),
         'projected_logs_replayed':len(projected),'augmented_rank':int(M.rank()),
         'offset_histogram':completion['offset_histogram']}
    (HERE/'validation.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))

if __name__=='__main__':main()
