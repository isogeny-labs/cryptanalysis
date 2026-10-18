"""Audit exceptional first-two-pair sums before a staged S3 encoding."""
import hashlib
import json
import resource
import signal
import time
from collections import defaultdict
from pathlib import Path

from sage.all import EllipticCurve,GF,PolynomialRing

here=Path(__file__).resolve().parent
p=json.loads((here/'audit_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path,digest in p['sources'].items():
    assert sha(path)==digest,path
assert not (here/'audit_result.json').exists()
signal.signal(signal.SIGALRM,lambda _s,_f: (_ for _ in ()).throw(TimeoutError('audit wall cap')))
signal.alarm(p['wall_cap_seconds'])
started=time.monotonic()


def field(n):
    K=PolynomialRing(GF(2),'u')
    u=K.gen()
    modulus=u**41+u**3+1 if n==41 else u**131+u**13+u**2+u+1
    F=GF(2**n,name='u',modulus=modulus)
    def dec(value):
        return F(K([(int(value)>>i)&1 for i in range(n)]))
    return F,dec


source=json.loads(Path(p['n41_states']).read_text())
F,dec=field(41)
E=EllipticCurve(F,[1,0,0,0,1])
states=[]
for slot in (0,1):
    states.append([(E(dec(row['point'][0]),dec(row['point'][1])),
                    frozenset(row['columns'])) for row in source['states'][slot]])
assert all(point[0] for slot in states for point,_ in slot)
valid=identity=zero_x=equal_x=reciprocal_pair=0
for point,cols in states[0]:
    a=1/point[0]
    for other,other_cols in states[1]:
        if cols & other_cols:
            continue
        valid+=1
        b=1/other[0]
        equal_x+=int(a==b)
        reciprocal_pair+=int(a*b==1)
        total=point+other
        if total==E(0):
            identity+=1
            assert a==b
        elif not total[0]:
            zero_x+=1
            assert a*b==1
assert valid>0

n131=json.loads(Path(p['n131_roots']).read_text())['queries'][0]['sources']
n131=[row for row in n131 if isinstance(row['code'],int)]
assert len(n131)==512
G,dec131=field(131)
roots=[dec131(word) for row in n131 for word in row['pair_roots']]
assert len(roots)==1024 and all(roots)
seen=defaultdict(list)
for i,root in enumerate(roots):
    seen[root].append(i)
distinct=len(seen)
same_x_cross=0
inverse_x_cross=0
for i,root in enumerate(roots):
    # Count ordered cross-code root-coordinate matches; source signs are
    # deliberately left free in this necessary-condition audit.
    same_x_cross+=sum(i//2!=j//2 for j in seen[root])
    inverse_x_cross+=sum(i//2!=j//2 for j in seen.get(1/root,[]))

signal.alarm(0)
out={'status':'PASS_FIRST_TWO_PAIR_EXCEPTION_AUDIT',
     'candidate_id':None,
     'n41':{'curve_id':source['curve_id'],'disjoint_ordered_pairs':valid,
            'identity_sums':identity,'zero_x_sums':zero_x,
            'equal_reciprocal_candidates':equal_x,
            'reciprocal_product_one_candidates':reciprocal_pair},
     'n131_sample':{'curve_id':p['n131_curve_id'],
                    'source_codes':len(n131),'root_coordinates':len(roots),
                    'distinct_root_coordinates':distinct,
                    'cross_code_equal_x_candidates':same_x_cross,
                    'cross_code_product_one_candidates':inverse_x_cross},
     'wall_seconds':time.monotonic()-started,
     'self_maxrss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
     'protocol_sha256':sha(here/'audit_protocol.json')}
(here/'audit_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(json.dumps(out,sort_keys=True))
