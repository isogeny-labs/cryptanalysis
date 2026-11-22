"""Independent integer and Fraction replay of known-relation lifts."""
from fractions import Fraction as F
from pathlib import Path
import gzip, hashlib, json, math

H=Path(__file__).resolve().parent
protocol=json.loads((H/'protocol.json').read_text())
source=(H.parent/'xedni-hensel-fresh-transfer-20261118'/'run-result.json.gz').read_bytes()
assert hashlib.sha256(source).hexdigest()==protocol['fresh_result_gzip_sha256']
parent=json.loads(gzip.decompress(source))
result=json.loads((H/'run-result.json').read_text())
assert result['protocol_sha256']==hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest()
assert result['source_gzip_sha256']==protocol['fresh_result_gzip_sha256']
assert len(result['rows'])==len(parent['public_hits'])

def add(P,Q,A,mod=None):
    if P is None: return Q
    if Q is None: return P
    x,y=P; u,v=Q
    if mod is None:
        if x==u and y==-v: return None
        slope=(3*x*x+A)/(2*y) if P==Q else (v-y)/(u-x)
        xx=slope*slope-x-u
        return (xx,slope*(x-xx)-y)
    if x==u and (y+v)%mod==0: return None
    slope=((3*x*x+A)*pow(2*y,-1,mod) if P==Q else
           (v-y)*pow(u-x,-1,mod))%mod
    xx=(slope*slope-x-u)%mod
    return (xx,(slope*(x-xx)-y)%mod)

def mul(n,P,A,mod=None):
    if n<0:
        P=(P[0],-P[1] if mod is None else (-P[1])%mod)
        n=-n
    out=None
    while n:
        if n&1: out=add(out,P,A,mod)
        P=add(P,P,A,mod); n//=2
    return out

def decode(P):
    return tuple(F(int(z['num']),int(z['den'])) for z in P)
def red(z,p):
    assert math.gcd(z.denominator,p)==1
    return z.numerator*pow(z.denominator,-1,p)%p
def bits(z): return max(abs(z.numerator).bit_length(),z.denominator.bit_length())

counts={}
for index,(hit,row) in enumerate(zip(parent['public_hits'],result['rows'])):
    assert row['hit_index']==index and row['hit']==hit
    status=row['status']; counts[status]=counts.get(status,0)+1
    if hit['status']!='eligible':
        assert status=='excluded_'+hit['status']; continue
    p,q=hit['p'],hit['q']; a,b=hit['a'],hit['b']
    if b==0 or math.gcd(b,q)!=1:
        assert status=='noninvertible_b'; continue
    assert status=='exact_relation'
    assert row['inverse_b_mod_q']==pow(b,-1,q)
    R=tuple(row['R']); U=tuple(hit['U']); V=tuple(hit['V'])
    assert (R[1]*R[1]-R[0]**3+R[0]+2)%p==0
    assert mul(row['inverse_b_mod_q'],U,-1,p)==R
    assert mul(b,R,-1,p)==U and mul(-a,R,-1,p)==V
    M=row['model']; A=M['A']; B=M['B']; x,y=M['T']
    assert A==-1 and x==R[0]-(p if R[0]>p//2 else 0)
    assert y==R[1]-(p if R[1]>p//2 else 0)
    assert B==y*y-x*x*x-A*x and B%p==p-2
    disc=-16*(4*A**3+27*B**2)
    assert str(disc)==M['discriminant'] and disc%p!=0
    assert M['model_bits']==max(bits(F(z)) for z in (A,B,x,y))
    T=(F(x),F(y)); P1=decode(row['P1']); P2=decode(row['P2'])
    assert y*y==x*x*x+A*x+B
    assert P1==mul(b,T,A) and P2==mul(-a,T,A)
    assert all(v*v==u*u*u+A*u+B for u,v in (P1,P2))
    assert add(mul(a,P1,A),mul(b,P2,A),A) is None
    assert tuple(red(z,p) for z in P1)==U
    assert tuple(red(z,p) for z in P2)==V
    assert row['lift_coordinate_bits']==max(bits(z) for z in (*P1,*P2))
assert result['exact_relation_count']==counts.get('exact_relation',0)
assert result['status']=='complete' and len(result['rows'])==13
out={'schema':'xedni-known-relation-lifts-audit-v1','status':'pass',
     'source_public_hits':len(parent['public_hits']),
     'exact_relation_count':counts.get('exact_relation',0),'statuses':counts}
(H/'audit-result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
