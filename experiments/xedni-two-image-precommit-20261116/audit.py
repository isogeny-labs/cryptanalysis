"""Independent pure-Python replay of the two-image rational interpolation panel."""
from collections import Counter
from fractions import Fraction
from pathlib import Path
import gzip, hashlib, json

H=Path(__file__).resolve().parent
P=json.loads((H/'protocol.json').read_text())
R=json.loads((H/'run-result.json').read_text())
assert hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest()==R['protocol_sha256']
source=H.parent/'xedni-large-order-height-admission-20261116'/'public.jsonl.gz'
assert hashlib.sha256(source.read_bytes()).hexdigest()==P['source_public_sha256']==R['source_public_sha256']
public=[json.loads(x) for x in gzip.decompress(source.read_bytes()).splitlines()]

def read(key):
    info=R[key]; blob=(H/info['path']).read_bytes()
    assert len(blob)==info['gzip_bytes']
    assert hashlib.sha256(blob).hexdigest()==info['gzip_sha256']
    raw=gzip.decompress(blob)
    assert hashlib.sha256(raw).hexdigest()==info['raw_sha256']
    rows=[json.loads(x) for x in raw.splitlines()]
    assert len(rows)==info['rows']
    return rows
queries=read('queries'); vectors=read('vectors')
assert len(public)==len(vectors)==6656 and len(queries)==512

def add(P,Q,a,m=None):
    if P is None: return Q
    if Q is None: return P
    x,y=P; u,v=Q
    if m is not None:
        if x==u and (y+v)%m==0: return None
        slope=((3*x*x+a)*pow(2*y,-1,m))%m if P==Q else ((v-y)*pow(u-x,-1,m))%m
        X=(slope*slope-x-u)%m
        return X,(slope*(x-X)-y)%m
    if x==u and y+v==0: return None
    slope=(3*x*x+a)/(2*y) if P==Q else (v-y)/(u-x)
    X=slope*slope-x-u
    return X,slope*(x-X)-y

def mul(n,P,a,m=None):
    if n<0:
        P=(P[0],(-P[1])%m if m is not None else -P[1]); n=-n
    out=None
    while n:
        if n&1: out=add(out,P,a,m)
        P=add(P,P,a,m); n//=2
    return out

def mod(z,p):
    assert z.denominator%p
    return z.numerator*pow(z.denominator,-1,p)%p

def center(z,p): return z-p if z>p//2 else z

counts=Counter(); per_field=Counter()
for qi,qr in enumerate(queries):
    group=public[13*qi:13*(qi+1)]
    vr=vectors[13*qi:13*(qi+1)]
    assert len(group)==len(vr)==13
    s=group[0]; p=s['p']; U=tuple(s['U']); V=tuple(s['V'])
    assert (qr['p'],qr['q'],qr['target_index'],qr['query_index'])==(p,s['q'],s['target_index'],s['query_index'])
    assert (tuple(qr['U']),tuple(qr['V']))==(U,V)
    assert qr['status']=='pass'
    xu,yu=(center(z,p) for z in U)
    xv,yv=(center(z,p) for z in V)
    if U[0]==V[0]:
        assert (U[1]+V[1])%p==0
        xv,yv=xu,-yu
        A=Fraction(-1); B=Fraction(yu*yu-xu*xu*xu+xu)
        assert qr['branch']=='equal_x_opposite'
        counts['equal_x']+=1
    else:
        fu=yu*yu-xu*xu*xu; fv=yv*yv-xv*xv*xv
        A=Fraction(fu-fv,xu-xv); B=Fraction(fu)-A*xu
        assert qr['branch']=='distinct_x'
        counts['distinct_x']+=1
    X=(Fraction(xu),Fraction(yu)); Y=(Fraction(xv),Fraction(yv))
    assert X[1]**2==X[0]**3+A*X[0]+B
    assert Y[1]**2==Y[0]**3+A*Y[0]+B
    assert 4*A**3+27*B**2!=0
    assert (mod(A,p),mod(B,p))==(p-1,p-2)
    assert (mod(X[0],p),mod(X[1],p))==U
    assert (mod(Y[0],p),mod(Y[1],p))==V
    assert (qr['A'],qr['B'],qr['P'],qr['R'])==(str(A),str(B),[str(z) for z in X],[str(z) for z in Y])
    for vi,(src,out) in enumerate(zip(group,vr)):
        assert src['vector_index']==out['vector_index']==vi
        assert (out['p'],out['target_index'],out['query_index'])==(p,s['target_index'],s['query_index'])
        a,b=src['a'],src['b']
        assert (out['a'],out['b'])==(a,b)
        pub=add(mul(a,U,-1,p),mul(b,V,-1,p),-1,p) is None
        assert pub==src['public_relation']==out['public_relation']
        rel=add(mul(a,X,A),mul(b,Y,A),A) is None
        assert out['status']=='tested' and out['rational_relation']==rel
        assert not rel or pub
        counts['public_hits']+=int(pub)
        counts['rational_hits']+=int(rel)
        per_field[(p,'public')]+=int(pub)
        per_field[(p,'rational')]+=int(rel)
        counts['attempts']+=1
assert counts['attempts']==R['counts']['vector_attempts']==6656
assert counts['public_hits']==R['counts']['public_hits']==17
assert counts['rational_hits']==R['counts']['rational_hits']==0
assert counts['distinct_x']==511 and counts['equal_x']==1
assert R['counts']['query_failure']==0 and R['status']=='complete'
summary={'schema':'xedni-two-image-precommit-audit-v1','status':'PASS','counts':dict(counts),
         'per_field':{str(p):{'public_hits':per_field[(p,'public')],'rational_hits':per_field[(p,'rational')]} for p in sorted({q['p'] for q in queries})},
         'run_result_sha256':hashlib.sha256((H/'run-result.json').read_bytes()).hexdigest()}
(H/'audit.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
print(json.dumps(summary,sort_keys=True,indent=2))
