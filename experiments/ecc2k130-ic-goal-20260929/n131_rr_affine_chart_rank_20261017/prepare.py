"""Select the first source-valid W23 affine square around the frozen anchor."""
import hashlib
import json
import resource
import signal
import time
from functools import lru_cache
from pathlib import Path
from sage.all import EllipticCurve, GF, PolynomialRing

D=Path(__file__).resolve().parent
ROOT=D.parent
PARENT=ROOT/'n41_n131_sixpair_rr_root_span_20261016/frozen_panels.json'
COUNT=ROOT/'n131_w23_sixpair_density_20261016/run_result.json'
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
p=json.loads((D/'protocol.json').read_text())
assert sha(D/'prepare.py')==p['source_sha256']['preparer']
assert sha(PARENT)==p['source_sha256']['parent_panel']
assert sha(COUNT)==p['source_sha256']['w23_count']
signal.alarm(p['wall_cap_s'])
start=time.monotonic()
parent=json.loads(PARENT.read_text())['n131']
R=PolynomialRing(GF(2),'t');t=R.gen()
F=GF(2**131,name='t',modulus=t**131+t**13+t**2+t+1)
E=EllipticCurve(F,[1,0,0,0,1])
def dec(value):return F(R([(int(value)>>i)&1 for i in range(131)]))
def enc(value):return sum(int(bit)<<i for i,bit in enumerate(value.polynomial().list()))
def xy(point):return [enc(point[0]),enc(point[1])]
def halftrace(value):
    result=F.zero();term=value
    for _ in range(66):result+=term;term=term**4
    assert result**2+result==value
    return result
@lru_cache(None)
def eligible(mask):
    if mask<=0 or mask>=(1<<23):return False
    w=dec(mask<<1)
    return bool(w and w.trace()==0 and (1/w).trace()==0)
@lru_cache(None)
def source(mask):
    assert eligible(mask)
    w=dec(mask<<1)
    point=E.lift_x(1+1/halftrace(w),all=True)[0]
    assert point!=E(0)
    return point
@lru_cache(None)
def orbit_key(mask):
    point=4*source(mask)
    assert point!=E(0)
    x=point[0];small=None
    for _ in range(131):
        value=enc(x)
        small=value if small is None or value<small else small
        x=x**2
    return small
def roots(a,b):
    groups={}
    for x in (source(a),-source(a)):
        for y in (source(b),-source(b)):
            z=x+y
            assert z!=E(0)
            row=xy(z)
            groups.setdefault(row[0],set()).add(tuple(row))
    assert len(groups)==2 and all(len(values)==2 for values in groups.values())
    return [[list(row) for row in sorted(groups[x])] for x in sorted(groups)]
fixed_points=[edge['roots'][0][0] for edge in parent['edges'][1:]]
fixed_keys={orbit_key(mask) for edge in parent['edges'][1:] for mask in edge['masks']}
anchor=p['anchor_mask'];seed=p['seed_mask'];pivot=seed.bit_length()-1
bits=[i for i in range(23) if i!=pivot]
directions=[1<<i for i in bits]
directions+=sorted((1<<i)|(1<<j) for i in bits for j in bits if i<j)
tested=source_valid=column_valid=0
selected=None
for ix,d1 in enumerate(directions):
    if selected:break
    for d2 in directions[ix+1:]:
        tested+=1
        masks=[anchor,anchor^d1,anchor^d2,anchor^d1^d2]
        if not all(eligible(a) and eligible(a^seed) for a in masks):continue
        source_valid+=1
        columns=[orbit_key(x) for a in masks for x in (a,a^seed)]
        if len(set(columns))!=8 or set(columns)&fixed_keys:continue
        column_valid+=1
        root_groups=[roots(a,a^seed) for a in masks]
        if any(len({r[0] for r in [group[root][0]]+fixed_points+[parent['target']]})!=7
               for group in root_groups for root in (0,1)):
            continue
        selected={'directions':[d1,d2],'masks':masks,
                  'columns':columns,'roots':root_groups}
        break
assert selected is not None
assert selected['masks'][0]==parent['edges'][0]['masks'][0]
assert selected['roots'][0]==parent['edges'][0]['roots']
result={'status':'FROZEN_N131_AFFINE_FOUR_CODE_PANEL',
        'target':parent['target'],'fixed_points':fixed_points,
        'fixed_edges':[edge['masks'] for edge in parent['edges'][1:]],
        'selection':selected,'candidates_tested':tested,
        'source_valid_candidates':source_valid,
        'column_valid_candidates':column_valid,
        'wall_s':time.monotonic()-start,
        'self_peak_rss_bytes_darwin':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'protocol_sha256':sha(D/'protocol.json')}
with (D/'panel.json').open('x') as out:
    json.dump(result,out,sort_keys=True,indent=2);out.write('\n')
print(json.dumps({'status':result['status'],'directions':selected['directions'],
                  'masks':selected['masks'],'candidates_tested':tested},sort_keys=True))
