"""Independent checked-Sage replay of width-16 quadratic lift."""
import hashlib
import json
from pathlib import Path
from sage.all import EllipticCurve, GF, PolynomialRing

HERE=Path(__file__).resolve().parent
protocol=json.loads((HERE/'audit_protocol.json').read_text())
for name,digest in protocol['sources'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,name
native=json.loads((HERE/'result.json').read_text())
ring=PolynomialRing(GF(2),'X'); X=ring.gen()
field=GF(2**41,name='X',modulus=X**41+X**3+1)
curve=EllipticCurve(field,[1,0,0,0,1])
def decode(word): return field(ring([(word>>i)&1 for i in range(41)]))
def encode(value): return sum(int(bit)<<i for i,bit in enumerate(value.polynomial().list()))
witness=(17678,155,6169,16990); width=16
starts=[(i//width)*width for i in witness]
need={(slot,sid) for slot in range(4) for sid in range(starts[slot],starts[slot]+width)}
states={}; target=None
for line in Path(protocol['source_table']).open():
    p=line.split()
    if p[0]=='T' and int(p[1])==1:
        target=curve(decode(int(p[2])),decode(int(p[3])))
    if p[0]=='S':
        key=(int(p[1]),int(p[2]))
        if key in need:
            states[key]=(curve(decode(int(p[9])),decode(int(p[10]))),
                         frozenset((int(p[5]),int(p[6]))))
assert len(states)==len(need) and target is not None

def partial(slot):
    out=[]
    for i in range(starts[slot],starts[slot]+width):
        for j in range(starts[slot+1],starts[slot+1]+width):
            a,ca=states[(slot,i)];b,cb=states[(slot+1,j)]
            if ca & cb: continue
            z=a+b
            if z==curve(0) or z[0]==0: continue
            out.append((z,encode(1/z[0]),ca|cb))
    return out
left,right=partial(0),partial(2)
C={x[1] for x in left};D={x[1] for x in right}
assert (len(C),len(D))==(native['left_unique'],native['right_unique'])==(120,128)
def lift(value):
    out=1;index=1
    for i in range(41):
        if value>>i&1:out|=1<<index
        index+=1
    for i in range(41):
        for j in range(i+1,41):
            if (value>>i&1) and (value>>j&1):out|=1<<index
            index+=1
    assert index==862
    return out
def basis(values):
    pivots={}
    for value in values:
        x=lift(value)
        while x:
            bit=x.bit_length()-1
            if bit in pivots:x^=pivots[bit]
            else:pivots[bit]=x;break
    return pivots
def contained(value,pivots):
    x=lift(value)
    while x:
        bit=x.bit_length()-1
        if bit not in pivots:return False
        x^=pivots[bit]
    return True
pivots=basis(D)
assert len(pivots)==native['right_lift_rank']==128
t=1/target[0]
proposals=passes=members=0
for c_word in C:
    c=decode(c_word);ct=c*t
    P=PolynomialRing(field,'z');z=P.gen()
    poly=(1+ct*ct)*z*z+ct*z+c*c+t*t
    for root,_ in poly.roots():
        proposals+=1
        d=encode(root)
        in_span=contained(d,pivots);in_set=d in D
        passes+=in_span;members+=in_set
        assert not in_set or in_span
assert (proposals,passes,members)==(native['root_proposals'],native['lift_passes'],native['set_hits'])==(240,1,1)
result={'status':'PASS_INDEPENDENT_QUADRATIC_LIFT_REPLAY','right_lift_rank':len(pivots),
        'root_proposals':proposals,'lift_passes':passes,'set_hits':members}
with (HERE/'audit_result.json').open('x') as out:
    json.dump(result,out,sort_keys=True,indent=2);out.write('\n')
print(result['status'])
