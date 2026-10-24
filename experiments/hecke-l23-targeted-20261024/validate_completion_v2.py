"""Independent integer-curve replay of the two-seed degree-23 completion."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from sage.all import GF, matrix

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PRIOR=ROOT/'hecke-torsion-frontiers-20261024'
SIGN=ROOT/'hecke-sign-closure-20261024'
def sha(path):return sha256(path.read_bytes()).hexdigest()

def main():
    protocol=json.loads((HERE/'completion_validation_protocol.v2.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_L23_COMPLETION_VALIDATOR'
    sources={'validator':HERE/'validate_completion_v2.py','completion':HERE/'completion.v2.json',
             'l23_result':HERE/'result.v2.json','frontier':PRIOR/'p20023.result.json',
             'seed':PRIOR/'p20023.seed.result.json','sign':SIGN/'result.json'}
    assert protocol['source_sha256']=={name:sha(path) for name,path in sources.items()}
    done=json.loads(sources['completion'].read_text());l23=json.loads(sources['l23_result'].read_text())
    frontier=json.loads(sources['frontier'].read_text());seed=json.loads(sources['seed'].read_text())
    sign=json.loads(sources['sign'].read_text())
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
        Q=(x,y);assert on(Q);return Q
    def mul(k,Q):
        if k<0:return mul(-k,neg(Q))
        R=None
        while k:
            if k&1:R=add(R,Q)
            Q=add(Q,Q);k>>=1
        return R
    T=(5,5);assert mul(5,T) is None
    def orbit(Q):return min(key(add(Q,mul(k,T))) for k in range(5))
    G=mul(5,(1,8630));assert mul(4021,G) is None
    true_logs={};Q=None
    for k in range(4021):
        assert Q not in true_logs
        true_logs[Q]=k;Q=add(Q,G)
    assert Q is None and len(true_logs)==4021
    keys=[tuple(x) for x in l23['all_column_representatives']];idx={a:i for i,a in enumerate(keys)}
    logs=done['logs_by_column'];assert len(logs)==len(keys)==3953
    table={}
    for i,rep in enumerate(keys):
        Q=mul(5,pt(rep));assert on(Q) and true_logs[Q]==logs[i]
        assert Q not in table
        table[Q]=logs[i]
    assert len(table)==done['prepared_table_count']==3953
    old=[tuple(x) for x in frontier['column_representatives']]
    def remap(row):return {str(idx[old[int(j)]]):v for j,v in row.items()}
    rows=([remap(r['coefficients']) for r in seed['accepted_rows']]
          +[remap(r) for r in frontier['rows']]
          +[remap(r['coefficients']) for r in sign['sign_rows']]
          +[r['coefficients'] for r in l23['accepted_rows']])
    assert len(rows)==7546
    assert all(sum(int(v)*logs[int(j)] for j,v in row.items())%4021==0 for row in rows)
    for record in done['seed_logs']:
        i=record['column_index'];assert keys[i]==tuple(record['orbit_representative'])
        assert logs[i]==record['scalar'] and mul(logs[i],G)==mul(5,pt(keys[i]))
    entries={(i,int(j)):v for i,row in enumerate(rows) for j,v in row.items()}
    entries[(len(rows),idx[orbit((1,8630))])]=1
    for k,i in enumerate(done['selected_seed_indices']):entries[(len(rows)+1+k,i)]=1
    M=matrix(GF(4021),len(rows)+1+len(done['seed_logs']),len(keys),entries,sparse=False)
    assert int(M.rank())==done['augmented_rank']==len(keys)
    hist=Counter()
    for k in range(4021):
        target=mul(k,G)
        for off in range(3):
            shifted=add(target,mul(off,G))
            if shifted in table:
                assert (table[shifted]-off)%4021==k
                hist[str(off)]+=1;break
        else:hist['uncovered']+=1
    assert {str(i):hist[str(i)] for i in range(3)}|{'uncovered':hist['uncovered']}==done['offset_histogram']
    out={'status':'PASS_L23_TWO_SEED_INTEGER_REPLAY',
         'protocol_sha256':sha(HERE/'completion_validation_protocol.v2.json'),
         'completion_sha256':sha(HERE/'completion.v2.json'),
         'validator_sha256':sha(HERE/'validate_completion_v2.py'),
         'relation_rows_checked':len(rows),'projected_logs_replayed':len(table),
         'seed_logs_checked':len(done['seed_logs']),'augmented_rank':int(M.rank()),
         'offset_histogram':done['offset_histogram']}
    (HERE/'completion_validation.v2.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))

if __name__=='__main__':main()
