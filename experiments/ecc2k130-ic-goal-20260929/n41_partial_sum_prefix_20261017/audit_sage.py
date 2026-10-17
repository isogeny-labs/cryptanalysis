"""Independent checked-Sage exact join and x-prefix census for half codes."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'n41_sixpair_shared_target_20261017/join_input.tsv'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
p=json.loads((HERE/'audit_protocol.json').read_text())
assert p['sources']=={'source':sha(SOURCE),'native_result':sha(HERE/'half_result.json'),
                     'runner':sha(Path(__file__)),'runtime':sha(HERE/'sage_runtime_info.json')}
R=PolynomialRing(GF(2),'t');t=R.gen()
F=GF(2**41,name='t',modulus=t**41+t**3+1)
E=EllipticCurve(F,[1,0,0,0,1])
def dec(v):return F(R([(int(v)>>i)&1 for i in range(41)]))
rows={}
header=SOURCE.open().readline().split()
assert header[:3]==['ECC2K41','6','160']
target=E(dec(header[3]),dec(header[4]))
for line in SOURCE.read_text().splitlines()[1:]:
    a=line.split();slot,id=int(a[1]),int(a[2]);point=E(dec(a[9]),dec(a[10]))
    assert int(point[0].to_integer())==int(a[9]) and int(point[1].to_integer())==int(a[10])
    rows[slot,id]=(point,(1<<int(a[7]))|(1<<int(a[8])))
assert len(rows)==960
deadline=time.monotonic()+p['wall_cap_seconds']
started=time.monotonic()
left={};left_x=set();right_x=set()
triples=[0,0];coordinates=0;relations=[]
status='COMPLETE'
for side in (0,1):
    if status!='COMPLETE':break
    off=3*side
    for a in range(80):
        if status!='COMPLETE':break
        A,ca=rows[off,a]
        for b in range(80):
            if ca & rows[off+1,b][1]:continue
            B,cb=rows[off+1,b]
            ab=A+B;used=ca|cb
            for c in range(80):
                if used & rows[off+2,c][1]:continue
                C,cc=rows[off+2,c]
                point=ab+C
                need=target-point if side else point
                triples[side]+=1
                if side:
                    for lk,lcols in left.get(need,()):
                        coordinates+=1
                        if not (lcols&(used|cc)):
                            relations.append(list(lk+(a,b,c)))
                    if need!=E(0):right_x.add(int(need[0].to_integer()))
                else:
                    left.setdefault(need,[]).append(((a,b,c),used|cc))
                    if need!=E(0):left_x.add(int(need[0].to_integer()))
                if triples[side]%10000==0 and time.monotonic()>deadline:
                    status='BOUNDED_UNKNOWN';break
                if triples[side]%10000==0 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>p['rss_cap_bytes']:
                    status='RSS_CAP';break
            if status!='COMPLETE':break
native=json.loads((HERE/'half_result.json').read_text())['worker']
prefixes=[]
if status=='COMPLETE':
    for bits in p['prefix_bits']:
        shift=41-bits
        L={x>>shift for x in left_x};U={x>>shift for x in right_x}
        prefixes.append({'bits':bits,'left_distinct':len(L),'right_distinct':len(U),
                         'intersection':len(L&U)})
    assert triples==[native['left_triples'],native['right_triples']]
    assert coordinates==native['coordinate_hits']==0
    assert relations==[] and native['relations']==0
    assert prefixes==native['prefixes']
record={'status':status,'triples':triples,'coordinate_hits':coordinates,
        'relations':relations,'prefixes':prefixes,'elapsed_seconds':time.monotonic()-started,
        'peak_self_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'protocol_sha256':sha(HERE/'audit_protocol.json'),
        'native_result_sha256':sha(HERE/'half_result.json')}
with (HERE/'audit_result.json').open('x') as f:
    json.dump(record,f,sort_keys=True,indent=2);f.write('\n')
print(status,triples,coordinates,len(relations),record['elapsed_seconds'],flush=True)
