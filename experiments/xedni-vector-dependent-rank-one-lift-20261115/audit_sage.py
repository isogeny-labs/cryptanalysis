"""Independent exhaustive public-event census and rank-one Sage replay."""
import hashlib
import json
from pathlib import Path
from sage.all import EllipticCurve, GF, QQ

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PARENT=ROOT/'xedni-optimized-family-lift-replay-20261115'
OPT=ROOT/'xedni-coefficient-optimization-20261115'
BAND=ROOT/'xedni-crt-band-panel-20261115'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def center(n,p):
    n=int(n)%p
    return n if n<=p//2 else n-p

def red(z,p):
    num,den=int(z.numerator()),int(z.denominator())
    assert den%p
    return num*pow(den,-1,p)%p

protocol=json.loads((HERE/'protocol.json').read_text())
result=json.loads((HERE/'result.json').read_text())
assert result['protocol_sha256']==sha(HERE/'protocol.json')
assert result['source_sha256']==sha(HERE/'run_sage.py')
assert result['sage_runtime_sha256']==sha(HERE/'sage-runtime-info.json')
assert protocol['parent_public_relation_result_sha256']==sha(PARENT/'result.json')
assert protocol['selected_family_sha256']==sha(OPT/'family-selection.json')
vectors=[tuple(v) for v in json.loads((OPT/'family-selection.json').read_text())['selected']]
reference=json.loads((BAND/'result.json').read_text())['fields']
assert len(vectors)==13 and len(result['fields'])==len(reference)==8
fields=[]
for row,old in zip(result['fields'],reference):
    p,q=old['field_prime'],old['subgroup_order']
    assert (p,q)==(row['field_prime'],row['subgroup_order'])
    Ebase=EllipticCurve(GF(p),[0,0,0,-1,-2]);G=Ebase(old['generator']);Q=Ebase(old['public_target'])
    d=old['fixture_scalar']
    assert d*G==Q and int(G.order())==q
    path=HERE/row['events_path'];assert sha(path)==row['events_sha256']
    saved=[json.loads(line) for line in path.read_text().splitlines()]
    cursor=0;tests=0
    for t1 in range(q):
        U=Q-t1*G
        for t2 in range(q):
            V=Q-t2*G
            if U.is_zero() or V.is_zero() or U==V:continue
            for a,b in vectors:
                tests+=1
                relation=((a+b)*d-a*t1-b*t2)%q==0
                assert relation==bool((a*U+b*V).is_zero())
                if not relation:continue
                assert cursor<len(saved)
                item=saved[cursor];cursor+=1
                assert item['t']==[t1,t2] and item['vector']==[a,b]
                assert item['query_index_one_based']==t1*q+t2+1
                assert item['status']=='verified'
                inv_b=pow(b%q,-1,q);T=inv_b*U
                assert item['inverse_b']==inv_b
                assert b*T==U and (-a)*T==V
                x,y=center(T[0],p),center(T[1],p)
                assert item['lift_T']==[x,y]
                B=y*y-x*x*x+x
                assert item['curve_B']==B and (B+2)%p==0
                E=EllipticCurve(QQ,[0,0,0,-1,B])
                assert E.discriminant()!=0
                P=E([x,y]);A=b*P;C=(-a)*P
                assert (a*A+b*C).is_zero()
                assert Ebase([red(A[0],p),red(A[1],p)])==U
                assert Ebase([red(C[0],p),red(C[1],p)])==V
                coords=[str(A[0]),str(A[1]),str(C[0]),str(C[1])]
                digest=hashlib.sha256(json.dumps(coords,separators=(',',':')).encode()).hexdigest()
                assert item['rational_points_sha256']==digest
                recovered=((a*t1+b*t2)*pow((a+b)%q,-1,q))%q
                assert item['recovered_scalar']==recovered and recovered*G==Q
    assert cursor==len(saved)==row['counts']['verified']
    assert tests==row['counts']['public_vector_tests']==13*(q-1)*(q-2)
    assert row['counts'].get('failed',0)==0
    fields.append({'field_prime':p,'subgroup_order':q,'public_vector_tests':tests,
                   'verified_rational_lifts':cursor})
assert sum(x['verified_rational_lifts'] for x in fields)==protocol['event_cap']==6136
print(json.dumps({'schema':'xedni-vector-dependent-rank-one-audit-v1','status':'PASS',
                  'protocol_sha256':sha(HERE/'protocol.json'),
                  'source_sha256':sha(Path(__file__)),
                  'sage_runtime_sha256':sha(HERE/'sage-runtime-info.json'),
                  'fields':fields},sort_keys=True,indent=2))
