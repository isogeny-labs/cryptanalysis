"""Independent checked-Sage replay of the seven-pair N41 public control."""
import hashlib,json
from pathlib import Path
from sage.all import EllipticCurve,GF,PolynomialRing
HERE=Path(__file__).resolve().parent
p=json.loads((HERE/'audit_protocol_v2.json').read_text())
for path,digest in p['sources'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
geo=json.loads(Path(p['geometry']).read_text())
source=json.loads(Path(p['source_geometry']).read_text())
ring=PolynomialRing(GF(2),'t');t=ring.gen()
field=GF(2**41,name='t',modulus=t**41+t**3+1)
curve=EllipticCurve(field,[1,0,0,0,1])
def dec(word):return field(ring([(int(word)>>i)&1 for i in range(41)]))
def enc(value):return sum(int(bit)<<i for i,bit in enumerate(value.polynomial().list()))
def xy(point):return [enc(point[0]),enc(point[1])]
rows={row['mask']:row for row in source['rows']}
positive=geo['positive_control'];total=curve(0);columns=[];pair_rows=[]
for i,state in enumerate(positive['states']):
    a,b=state['a'],state['b']
    points=[]
    for mask,sign in ((a,state['sign_a']),(b,state['sign_b'])):
        raw=curve(*map(dec,rows[mask]['raw_point']))
        point=-raw if sign else raw
        rotation=geo['rotations'][i]
        points.append(curve(point[0]**(1<<rotation),point[1]**(1<<rotation)))
        columns.append(rows[mask]['column'])
    joined=points[0]+points[1]
    assert joined!=curve(0) and xy(joined)==state['raw_sum']
    assert enc(1/(joined[0]+1))==state['z']
    total+=joined
    pair_rows.append({'slot':i,'masks':[a,b],'raw_sum':xy(joined),'z':state['z']})
assert len(columns)==len(set(columns))==14
assert xy(total)==positive['raw_target']
assert xy(4*total)==positive['subgroup_target']
result={'status':'PASS_INDEPENDENT_N41_SEVENPAIR_PUBLIC_REPLAY',
        'pairs':pair_rows,'raw_target':xy(total),'public_target':xy(4*total),
        'distinct_columns':len(set(columns))}
with (HERE/'audit_result_v2.json').open('x') as out:
    json.dump(result,out,sort_keys=True,indent=2);out.write('\n')
print(result['status'])
