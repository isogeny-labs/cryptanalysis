"""Independent checked-Sage replay of the public-point six-pair join hit."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
result=json.loads((HERE/'join_result.json').read_text())
protocol=json.loads((HERE/'join_protocol.json').read_text())
assert result['status']=='HIT_PENDING_SAGE_REPLAY' and len(result['hit_lines'])==1
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert sha(HERE/'join_protocol.json')==result['protocol_sha256']
for path,digest in protocol['sources'].items():assert sha(path)==digest,path
assert sha(HERE/'join.stdout.txt')==result['stdout_sha256']
assert sha(HERE/'join.stderr.txt')==result['stderr_sha256']
geometry=json.loads((ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json').read_text())
source_path=ROOT/'n41_w7_entropy_cubic_20261011/w8/geometry.json'
baseline=json.loads((ROOT/'n41_w8_selector_elimination_control_20261013/audit_protocol_v2.json').read_text())
assert sha(source_path)==baseline['sources'][str(source_path)]
source=json.loads(source_path.read_text())
rows={row['mask']:row for row in source['rows']}
R=PolynomialRing(GF(2),'t');t=R.gen()
F=GF(2**41,name='t',modulus=t**41+t**3+1)
E=EllipticCurve(F,[1,0,0,0,1])
def dec(word):return F(R([(int(word)>>i)&1 for i in range(41)]))
def enc(value):return sum(int(bit)<<i for i,bit in enumerate(value.polynomial().list()))
def xy(point):return [enc(point[0]),enc(point[1])]
parts=result['hit_lines'][0].split()
assert len(parts)==10 and parts[0]=='HIT'
ids=list(map(int,parts[1:7]))
assert all(0<=sid<160 for sid in ids)
pair_rows=[]
columns=[]
total=E(0)
for slot,sid in enumerate(ids):
    state=geometry['blocks'][slot]['states'][sid]
    raw=[]
    for mask,sign in ((state['a'],state['sign_a']),(state['b'],state['sign_b'])):
        point=E(*map(dec,rows[mask]['raw_point']))
        if sign:point=-point
        k=geometry['rotations'][slot]
        point=E(point[0]**(1<<k),point[1]**(1<<k))
        raw.append(point)
        columns.append(rows[mask]['column'])
    pair=raw[0]+raw[1]
    assert pair!=E(0) and xy(pair)==state['raw_sum']
    assert state['columns']==columns[-2:]
    total+=pair
    pair_rows.append({'slot':slot,'state_id':sid,'masks':[state['a'],state['b']],
                      'signs':[state['sign_a'],state['sign_b']],
                      'columns':state['columns'],'raw_sum':xy(pair)})
assert len(columns)==len(set(columns))==12
assert xy(total)==protocol['public_raw_point']==geometry['positive_control']['raw_target']
assert xy(4*total)==geometry['positive_control']['subgroup_target']
audit={'status':'PASS_INDEPENDENT_N41_SIXPAIR_PUBLIC_RELATION',
       'pair_rows':pair_rows,'distinct_columns':len(set(columns)),
       'raw_target':xy(total),'subgroup_target':xy(4*total),
       'join_protocol_sha256':sha(HERE/'join_protocol.json'),
       'join_result_sha256':sha(HERE/'join_result.json'),
       'source_geometry_sha256':sha(source_path)}
with (HERE/'join_audit_result.json').open('x') as out:
    json.dump(audit,out,sort_keys=True,indent=2);out.write('\n')
print(audit['status'],flush=True)
