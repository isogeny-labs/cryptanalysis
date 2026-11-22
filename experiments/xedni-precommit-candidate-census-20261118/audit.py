"""Independent repeated-addition replay of every recorded candidate outcome."""
from collections import Counter
from fractions import Fraction
from pathlib import Path
import gzip
import hashlib
import json

H = Path(__file__).resolve().parent
P = json.loads((H/'protocol.json').read_text())
R = json.loads((H/'result.json').read_text())
S = (H/P['source_dir']).resolve()
assert hashlib.sha256((S/'run-result.json').read_bytes()).hexdigest() == P['source_result_sha256']
M = json.loads((S/'run-result.json').read_text())

def rows(info):
    blob = (S/info['path']).read_bytes()
    assert hashlib.sha256(blob).hexdigest() == info['gzip_sha256']
    raw = gzip.decompress(blob)
    assert hashlib.sha256(raw).hexdigest() == info['raw_sha256']
    data = [json.loads(line) for line in raw.splitlines()]
    assert len(data) == info['rows']
    return data

queries = rows(M['queries'])
vectors = rows(M['vectors'])
recorded = [json.loads(line) for line in (H/'outcomes.jsonl').read_text().splitlines()]
assert len(recorded) == R['candidate_vector_tests']
assert hashlib.sha256((H/'outcomes.jsonl').read_bytes()).hexdigest() == R['outcomes_sha256']

def plus(P,Q,A):
    if P is None: return Q
    if Q is None: return P
    x,y=P; u,v=Q
    if x==u and y==-v: return None
    k=(Fraction(3*x*x+A,2*y) if P==Q else Fraction(v-y,u-x))
    z=k*k-x-u
    return (z,k*(x-z)-y)

def repeated(n,P,A):
    if n<0: P=(P[0],-P[1]); n=-n
    R=None
    for _ in range(n): R=plus(R,P,A)
    return R

c=Counter()
for row in recorded:
    q=queries[row['event_index']]
    h=vectors[row['event_index']*13+row['vector_index']]
    assert h['public_relation'] and (h['a'],h['b'])==(row['a'],row['b'])
    p=q['p']
    def cent(z): return z-p if z>p//2 else z
    x1,y1=map(cent,q['U']); x2,y2=map(cent,q['V'])
    shift=row['shift']
    assert shift is not None and len(shift)==4
    x1+=shift[0]*p; y1+=shift[1]*p; x2+=shift[2]*p; y2+=shift[3]*p
    f1=y1*y1-x1*x1*x1; f2=y2*y2-x2*x2*x2
    A=Fraction(f1-f2,x1-x2); B=Fraction(f1)-A*x1
    assert 4*A**3+27*B**2!=0
    assert y1*y1==x1*x1*x1+A*x1+B and y2*y2==x2*x2*x2+A*x2+B
    status='relation' if plus(repeated(row['a'],(Fraction(x1),Fraction(y1)),A),repeated(row['b'],(Fraction(x2),Fraction(y2)),A),A) is None else 'nonidentity'
    assert status==row['status']
    c[status]+=1
assert len(recorded)==22*81 and c==Counter({'nonidentity':1782})
assert R['public_hit_rows']==22 and R['public_hit_rows_with_any_rational_relation']==0
print('PASS: 22 public-hit rows, 81 frozen candidate lifts each, 1782 independent repeated-addition checks, zero exact rational relations')
