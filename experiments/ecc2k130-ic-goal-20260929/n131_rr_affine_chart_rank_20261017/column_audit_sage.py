"""Recompute selected and fixed W23 folded-column orbit keys in Sage."""
import hashlib
import json
import signal
from functools import lru_cache
from pathlib import Path
from sage.all import EllipticCurve, GF, PolynomialRing

D=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
p=json.loads((D/'column_protocol.json').read_text())
assert sha(D/'column_audit_sage.py')==p['source_sha256']
assert sha(D/'panel.json')==p['panel_sha256']
signal.alarm(p['wall_cap_s'])
panel=json.loads((D/'panel.json').read_text())
R=PolynomialRing(GF(2),'z');z=R.gen()
F=GF(2**131,name='z',modulus=z**131+z**13+z**2+z+1)
E=EllipticCurve(F,[1,0,0,0,1])
def dec(value):return F(R([(int(value)>>i)&1 for i in range(131)]))
def enc(value):return sum(int(bit)<<i for i,bit in enumerate(value.polynomial().list()))
def halftrace(value):
    acc=F.zero();power=value
    for _ in range(66):acc+=power;power=power**4
    assert acc**2+acc==value
    return acc
@lru_cache(None)
def key(mask):
    w=dec(mask<<1)
    assert w and w.trace()==0 and (1/w).trace()==0
    P=E.lift_x(1+1/halftrace(w),all=True)[0]
    Q=4*P
    assert Q!=E(0)
    x=Q[0]
    words=[]
    for _ in range(131):
        words.append(enc(x));x=x**2
    assert x==Q[0]
    return min(words)
seed=898618
selected=[mask for a in panel['selection']['masks'] for mask in (a,a^seed)]
fixed=[mask for pair in panel['fixed_edges'] for mask in pair]
selected_keys=[key(mask) for mask in selected]
fixed_keys=[key(mask) for mask in fixed]
assert selected_keys==panel['selection']['columns']
assert len(set(selected_keys+fixed_keys))==18
record={'status':'PASS_INDEPENDENT_W23_FOLDED_COLUMNS',
        'selected_masks':selected,'selected_columns':selected_keys,
        'fixed_masks':fixed,'all_distinct_columns':True,
        'panel_sha256':sha(D/'panel.json'),
        'protocol_sha256':sha(D/'column_protocol.json')}
with (D/'column_audit_result.json').open('x') as out:
    json.dump(record,out,sort_keys=True,indent=2);out.write('\n')
print(record['status'])
