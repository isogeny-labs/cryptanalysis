"""Rebuild three W23 first-slot root families with five RR slots fixed."""
import hashlib
import json
from pathlib import Path
from sage.all import EllipticCurve, GF, PolynomialRing

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=json.loads((HERE/'prepare_protocol_n131.json').read_text())
for path,digest in protocol['sources'].items():assert sha(path)==digest,path
prior=json.loads((ROOT/'n41_n131_sixpair_rr_root_span_20261016/frozen_panels.json').read_text())['n131']
worker=json.loads((ROOT/'n131_w23_sixpair_density_20261016/run_result.json').read_text())['worker_result']
samples=worker['sample_edges']
assert worker['seed_mask']==898618 and len(samples)==8
R=PolynomialRing(GF(2),'t');t=R.gen()
F=GF(2**131,name='t',modulus=t**131+t**13+t**2+t+1)
E=EllipticCurve(F,[1,0,0,0,1])
def dec(value):return F(R([(int(value)>>i)&1 for i in range(131)]))
def enc(value):return sum(int(bit)<<i for i,bit in enumerate(value.polynomial().list()))
def xy(point):return [enc(point[0]),enc(point[1])]
def halftrace(value):
    out=F.zero();term=value
    for _ in range(66):out+=term;term=term**4
    assert out**2+out==value
    return out
def source(mask):
    w=dec(mask<<1)
    assert w and w.trace()==0 and (1/w).trace()==0
    x=1+1/halftrace(w)
    points=E.lift_x(x,all=True)
    assert len(points)==2
    return points[0]
def roots(a,b):
    left,right=source(a),source(b)
    groups={}
    for p in (left,-left):
        for q in (right,-right):
            z=p+q
            assert z!=E(0)
            point=xy(z);groups.setdefault(point[0],set()).add(tuple(point))
    assert len(groups)==2 and all(len(values)==2 for values in groups.values())
    return [[list(row) for row in sorted(groups[x])] for x in sorted(groups)]

fixed=[edge['roots'][0][0] for edge in prior['edges'][1:]]
fixed_cols={col for edge in prior['edges'][1:] for col in edge['columns']}
variants=[]
for index in (0,1,7):
    a,b,ca,cb=samples[index]
    assert not ({ca,cb}&fixed_cols)
    pair_roots=roots(a,b)
    if index==0:assert pair_roots==prior['edges'][0]['roots']
    variants.append({'sample_index':index,'masks':[a,b],'columns':[ca,cb],
                     'roots':pair_roots})
result={'status':'FROZEN_N131_FIRST_CODE_VARIANTS','field_degree':131,
        'field_modulus':(1<<131)|(1<<13)|7,'target':prior['target'],
        'fixed_points':fixed,'fixed_columns':sorted(fixed_cols),'variants':variants,
        'prepare_protocol_sha256':sha(HERE/'prepare_protocol_n131.json')}
with (HERE/'panel_n131.json').open('x') as out:json.dump(result,out,sort_keys=True,indent=2);out.write('\n')
print(result['status'])
