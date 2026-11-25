"""Export an exact XOR representation of the first N131 constant coefficient."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=json.loads((HERE/'span_protocol.json').read_text())
for path,digest in protocol['sources'].items():assert sha(path)==digest,path
source=ROOT/'n41_n131_sixpair_rr_root_span_20261016/run.py'
spec=importlib.util.spec_from_file_location('rr',source)
rr=importlib.util.module_from_spec(spec);spec.loader.exec_module(rr)
panel=json.loads((HERE/'panel_n131_v2.json').read_text())
F=rr.Field(131,panel['field_modulus'])
items=[];constants=[]
for chart,variant in enumerate(panel['variants']):
    points=[variant['roots'][0][0]]+panel['fixed_points']
    c=rr.coefficients([p[0] for p in points],[p[1] for p in points],panel['target'],F)
    assert c is not None
    constants.append(c[0])
    for mask in range(1,64):
        if rr.popcount(mask)<=3:items.append((chart,mask,c[mask]))
basis={}
for i,(_,_,value) in enumerate(items):
    combo=1<<i
    while value:
        p=value.bit_length()-1
        if p in basis:
            b,m=basis[p];value^=b;combo^=m
        else:basis[p]=(value,combo);break
assert len(basis)==131
value=constants[0];combo=0
while value:
    p=value.bit_length()-1
    b,m=basis[p];value^=b;combo^=m
assert value==0
selected=[{'chart':chart,'monomial_mask':mask,'field_value':word}
          for i,(chart,mask,word) in enumerate(items) if combo>>i&1]
check=0
for row in selected:check^=row['field_value']
assert check==constants[0]
result={'status':'EXACT_N131_CONSTANT_IN_SIGN_SPAN','field_degree':131,
        'coefficient_count':len(items),'span_rank':len(basis),
        'selected_count':len(selected),'constant':constants[0],
        'selected':selected,'protocol_sha256':sha(HERE/'span_protocol.json')}
with (HERE/'span_certificate.json').open('x') as out:
    json.dump(result,out,sort_keys=True,indent=2);out.write('\n')
print(result['status'],result['selected_count'])
