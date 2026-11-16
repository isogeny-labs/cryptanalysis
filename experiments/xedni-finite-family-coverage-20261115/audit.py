"""Independent brute-force modular census and checked-Sage group replay."""
import hashlib
import json
import math
from pathlib import Path
from sage.all import EllipticCurve, GF

HERE=Path(__file__).resolve().parent
FAMILY=HERE.parent/'xedni-coefficient-holdout-20261115'
HOLD=HERE.parent/'xedni-nonisomorphic-holdout-20261115'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

protocol=json.loads((HERE/'protocol.json').read_text())
result=json.loads((HERE/'result.json').read_text())
assert result['protocol_sha256']==sha(HERE/'protocol.json')
assert result['source_sha256']==sha(HERE/'run.py')
assert protocol['family_protocol_sha256']==sha(FAMILY/'protocol.json')
assert protocol['family_source_sha256']==sha(FAMILY/'run.py')
assert protocol['field_selection_sha256']==sha(HOLD/'selection.json')
vectors=[(a,b) for a in range(1,4) for b in range(-3,4) if b and math.gcd(a,abs(b))==1]
assert [list(v) for v in vectors]==json.loads((FAMILY/'protocol.json').read_text())['coefficient_family']
fields=[]
for row,(p,q) in zip(result['fields'],json.loads((HOLD/'selection.json').read_text())['selected']):
    assert (p,q)==(row['field_prime'],row['subgroup_order'])
    E=EllipticCurve(GF(p),[-1,-2]);G=E(2,2)
    assert int(E.cardinality())==q and int(G.order())==q
    raw=HERE/row['first_path']
    assert sha(raw)==row['first_sha256']
    saved=[json.loads(line) for line in raw.read_text().splitlines()]
    assert len(saved)==q-1 and all(x['scalar']==i+1 for i,x in enumerate(saved))
    counts=[0]*len(protocol['query_caps'])
    for d,item in enumerate(saved,start=1):
        found=None
        for t in range(1,q):
            if t==d:continue
            for j,(a,b) in enumerate(vectors):
                if (a+b)%q==0:continue
                if ((a+b)*d-b*t)%q==0:
                    found={'scalar':d,'first_query':t+1,'offset':t,
                           'vector_index':j,'vector':[a,b]}
                    break
            if found:break
        assert found==item
        Q=d*G;R=Q-item['offset']*G
        assert not Q.is_zero() and not R.is_zero() and Q!=R
        a,b=item['vector']
        assert (a*Q+b*R).is_zero()
        recovered=(b*item['offset']*pow((a+b)%q,-1,q))%q
        assert recovered==d and recovered*G==Q
        for i,L in enumerate(protocol['query_caps']):
            counts[i]+=item['first_query']<=L
    assert counts==[x['covered_nonzero_targets'] for x in row['caps']]
    for entry in row['caps']:
        assert entry['covered_nonzero_targets']<=entry['union_bound']
        assert entry['union_bound']==min(q-1,13*(entry['query_cap']-1))
    fields.append({'field_prime':p,'subgroup_order':q,'counts':counts,
                   'full_row_covered':q-1})
print(json.dumps({'schema':'xedni-finite-family-coverage-audit-v1','status':'PASS',
                  'fields':fields},sort_keys=True,indent=2))
