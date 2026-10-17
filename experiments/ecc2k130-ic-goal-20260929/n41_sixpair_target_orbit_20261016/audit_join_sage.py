"""Independent Sage relation and rank replay for 41 target-orbit hits."""
import hashlib
import json
from pathlib import Path
from sage.all import EllipticCurve, GF, Matrix, PolynomialRing

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=json.loads((HERE/'audit_protocol.json').read_text())
for path,digest in protocol['sources'].items():assert sha(path)==digest,path
join=json.loads((HERE/'join_result.json').read_text())
assert join['status']=='COMPLETE' and join['orbits_completed']==41 and len(join['hits'])==41
g=json.loads((ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json').read_text())
s=json.loads((ROOT/'n41_w7_entropy_cubic_20261011/w8/geometry.json').read_text())
rows={row['mask']:row for row in s['rows']}
R=PolynomialRing(GF(2),'t');t=R.gen()
F=GF(2**41,'t',modulus=t**41+t**3+1)
E=EllipticCurve(F,[1,0,0,0,1])
r=g['subgroup_order'];LAMBDA=256851699273
assert LAMBDA>1 and pow(LAMBDA,41,r)==1
def dec(word):return F(R([(int(word)>>i)&1 for i in range(41)]))
def enc(v):return sum(int(b)<<i for i,b in enumerate(v.polynomial().list()))
def xy(P):return [enc(P[0]),enc(P[1])]
def point(pair):return E(dec(pair[0]),dec(pair[1]))
def phi(P):return E(P[0]**2,P[1]**2)
public=point(protocol['public_subgroup_point']);raw=point(protocol['public_raw_point'])
assert 4*raw==public
allowed={mask for a in g['permitted_canonical_a'] for mask in (a,a^g['fixed_seed_sum_code'])}
columns=sorted({rows[mask]['column'] for mask in allowed})
assert len(columns)==77
base={}
for item in s['rows']:
    c=item['column']
    if item['mask'] in allowed and c not in base:base[c]=point(item['projected_point'])
assert all(LAMBDA*P==phi(P) for P in base.values())
orbit_lookup={}
for c,B in base.items():
    P=B
    for k in range(41):
        orbit_lookup[(c,tuple(xy(P)))]=(k,1)
        orbit_lookup[(c,tuple(xy(-P)))]=(k,-1)
        P=phi(P)
    assert P==B
mask_data={}
for mask in allowed:
    item=rows[mask]
    P=point(item['raw_point'])
    assert 4*P==point(item['projected_point'])
    mask_data[mask]=(item['column'],*orbit_lookup[(item['column'],tuple(item['projected_point']))])
rank_prefix=[];relations=[];vectors=[];target_orbit=raw
for j,line in enumerate(join['hits']):
    parts=line.split();assert len(parts)==11 and parts[0]=='ORBIT_HIT' and int(parts[1])==j
    ids=list(map(int,parts[2:8]));assert all(0<=v<160 for v in ids)
    pair_sum=E(0);cols=[];coeff={}
    for slot,sid in enumerate(ids):
        state=g['blocks'][slot]['states'][sid]
        leaves=[]
        for mask,sign in ((state['a'],state['sign_a']),(state['b'],state['sign_b'])):
            item=rows[mask]
            P=point(item['raw_point'])
            if sign:P=-P
            for _ in range(g['rotations'][slot]):P=phi(P)
            leaves.append(P);cols.append(item['column'])
            c,k,eps=mask_data[mask]
            value=(eps*(-1 if sign else 1)*pow(LAMBDA,(k+g['rotations'][slot]-j)%41,r))%r
            coeff[c]=(coeff.get(c,0)+value)%r
        assert xy(leaves[0]+leaves[1])==state['raw_sum']
        pair_sum+=sum(leaves,E(0))
    assert len(set(cols))==12
    assert pair_sum==target_orbit
    assert 4*pair_sum==4*target_orbit
    replay=sum((int(value)*base[c] for c,value in coeff.items()),E(0))
    assert replay==public
    vector=[coeff.get(c,0) for c in columns]+[r-1]
    vectors.append(vector)
    rank_prefix.append(int(Matrix(GF(r),vectors).rank()))
    relations.append({'orbit_index':j,'state_ids':ids,'distinct_columns':12,
                      'raw_sum':xy(pair_sum),'nonzero_columns':len(coeff),
                      'row_sha256':hashlib.sha256(json.dumps(vector).encode()).hexdigest()})
    target_orbit=phi(target_orbit)
assert target_orbit==raw
out={'status':'PASS_N41_41_ORBIT_GROUP_AND_ROW_AUDIT','relation_count':41,
     'rank_prefix':rank_prefix,'final_rank':rank_prefix[-1],
     'column_count':len(columns),'relations':relations,
     'join_sha256':sha(HERE/'join_result.json'),
     'source_geometry_sha256':sha(ROOT/'n41_w7_entropy_cubic_20261011/w8/geometry.json')}
(HERE/'join_audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(out['status'],out['final_rank'])
