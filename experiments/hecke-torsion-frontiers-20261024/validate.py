"""Independent affine-curve replay of saved Hecke rows and frontier membership."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
MODULE=ROOT/'hecke-two-sheet-small-order-20261023/tools/hecke11.py'
PARENT=ROOT/'hecke-torsion-bridge-layer3-20261023/result.json'

def sha(p):return sha256(p.read_bytes()).hexdigest()
def main(case):
    protocol_file=HERE/('p12043.protocol.v3.json' if case=='p12043' else case+'.protocol.json')
    producer_file=HERE/('produce_p12043_v3.py' if case=='p12043' else 'produce.py')
    protocol=json.loads(protocol_file.read_text())
    data=json.loads((HERE/(case+'.result.json')).read_text())
    p=protocol['p']; assert data['p']==p and data['protocol_sha256']==sha(protocol_file)
    assert protocol['source_sha256']['producer']==data['producer_sha256']==sha(producer_file)
    assert protocol['source_sha256']['hecke11']==data['hecke11_sha256']==sha(MODULE)
    if case=='p12043':assert protocol['source_sha256']['parent']==data['parent_sha256']==sha(PARENT)
    def pt(x):return None if tuple(x)==(-1,-1) else tuple(x)
    def key(x):return (-1,-1) if x is None else x
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
    keys=[tuple(x) for x in data['column_representatives']]
    assert keys==sorted(set(keys)) and all(on(pt(x)) and orbit(pt(x))==x for x in keys)
    idx={x:i for i,x in enumerate(keys)}
    if case=='p12043':
        parent=json.loads(PARENT.read_text())
        old=[tuple(parent['column_representatives'][i]) for i in parent['discard_previous_indices']]
        assert data['stages'][0]['frontier_representatives']==[list(x) for x in old]
    else:
        assert data['seed_trace_abs']==64 and len(data['stages'][0]['frontier_representatives'])==564
    prior=set(tuple(x) for x in data['boundary_representatives']['third' if case=='p12043' else 'seed'])
    counts=[];all_saved_rows=[];novel_counts=[]
    for stage in data['stages']:
        frontier=[tuple(x) for x in stage['frontier_representatives']]
        assert len(frontier)==len(set(frontier)) and all(x in prior for x in frontier)
        sources={add(pt(rep),mul(k,T)) for rep in frontier for k in range(5)}
        assert len(sources)==stage['source_count']
        statuses=Counter();new=set()
        for rec in stage['accepted_rows']:
            P=pt(rec['source']);assert P in sources and on(P)
            l=rec['degree'];assert l in (2,3)
            neighbors=[pt(Q) for Q in rec['neighbours']]
            assert len(neighbors)==l+1 and all(on(Q) for Q in neighbors)
            S=None
            for Q in neighbors:S=add(S,Q)
            assert S==mul(-2 if l==2 else -1,P)
            coeff=Counter(idx[orbit(Q)] for Q in neighbors)
            coeff[idx[orbit(P)]]-=(-2 if l==2 else -1)
            assert {str(j):v for j,v in coeff.items() if v}==rec['coefficients']
            new.update({keys[j] for j,v in coeff.items() if v}-prior)
            all_saved_rows.append(rec['coefficients']);statuses[f'L{l}_ACCEPTED']+=1
        assert sorted(new)==[tuple(x) for x in stage['new_representatives']]
        assert dict(statuses)=={k:v for k,v in stage['status_counts'].items() if k.endswith('_ACCEPTED')}
        assert sum(stage['status_counts'].values())+stage['status_counts'].get('SOURCE_UNDEFINED_J',0)==2*stage['source_count']
        counts.append(dict(stage['status_counts']));novel_counts.append(len(new));prior.update(new)
    if case=='p12043':
        parent=json.loads(PARENT.read_text())
        parent_keys=[tuple(x) for x in parent['column_representatives']]
        earlier=parent['base_rows']+parent['layer1_rows']+parent['layer2_rows']+[x['coefficients'] for x in parent['accepted_rows']]
        def remap(row):return {str(idx[parent_keys[int(j)]]):v for j,v in row.items()}
        assert data['rows']==[remap(r) for r in earlier]+all_saved_rows
    else:assert data['rows']==all_saved_rows
    seed_replayed=0
    if case=='p20023':
        seed_data=json.loads((HERE/'p20023.seed.result.json').read_text())
        assert seed_data['frontier_sha256']==sha(HERE/'p20023.result.json')
        assert seed_data['combined_row_count']==len(data['rows'])+len(seed_data['accepted_rows'])==5565
        seed={tuple(x) for x in data['boundary_representatives']['seed']}
        for rec in seed_data['accepted_rows']:
            P=pt(rec['source']);assert on(P) and orbit(P) in seed
            l=rec['degree'];assert l in (2,3)
            neighbors=[pt(x) for x in rec['neighbours']]
            assert len(neighbors)==l+1 and all(on(Q) for Q in neighbors)
            S=None
            for Q in neighbors:S=add(S,Q)
            assert S==mul(-2 if l==2 else -1,P)
            coeff=Counter(idx[orbit(Q)] for Q in neighbors)
            coeff[idx[orbit(P)]]-=(-2 if l==2 else -1)
            assert {str(j):v for j,v in coeff.items() if v}==rec['coefficients']
            seed_replayed+=1
        assert seed_replayed==490
    receipt={'status':'PASS_AFFINE_POINT_AND_ROW_REPLAY','case':case,
             'protocol_sha256':sha(protocol_file),
             'result_sha256':sha(HERE/(case+'.result.json')),
             'validator_sha256':sha(HERE/'validate.py'),
             'accepted_rows_replayed':len(all_saved_rows),
             'new_columns_by_layer':novel_counts,'status_counts_by_layer':counts,
             'matrix_rows_checked':len(data['rows'])+seed_replayed,
             'seed_rows_replayed':seed_replayed,'column_count':len(keys)}
    (HERE/(case+'.validation.json')).write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k in ('status','case','accepted_rows_replayed','new_columns_by_layer')},sort_keys=True))

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ('p12043','p20023')
    main(sys.argv[1])
