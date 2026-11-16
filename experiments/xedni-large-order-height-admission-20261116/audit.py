"""Independent pure-Python replay of public and rational group arithmetic."""
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
import gzip, hashlib, itertools, json, statistics

H=Path(__file__).resolve().parent
P=json.loads((H/'protocol.json').read_text())
S=H.parent/'xedni-large-order-admission-20261115'/'result.json'
assert hashlib.sha256(S.read_bytes()).hexdigest()==P['source_sha256']
R=json.loads((H/'run-result.json').read_text())
A=json.loads((H/'storage-amendment.json').read_text())
assert A['measurement_changed'] is False
assert hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest()==R['protocol_sha256']

def read_rows(name,key):
    info=A['files'][name]
    packed=(H/info['gzip_path']).read_bytes()
    assert hashlib.sha256(packed).hexdigest()==info['gzip_sha256']
    raw=gzip.decompress(packed)
    assert len(raw)==info['raw_bytes']
    assert hashlib.sha256(raw).hexdigest()==R[key]==info['raw_sha256']
    return [json.loads(line) for line in raw.decode('utf-8').splitlines()]
public=read_rows('public.jsonl','public_sha256')
lifts=read_rows('lifts.jsonl','lifts_sha256')
assert len(public)==6656 and len(lifts)==R['counts']['lift_attempts']

def add(P,Q,a,m=None):
    if P is None: return Q
    if Q is None: return P
    x,y=P; u,v=Q
    if m is not None:
        if x==u and (y+v)%m==0: return None
        slope=((3*x*x+a)*pow(2*y,-1,m))%m if P==Q else ((v-y)*pow(u-x,-1,m))%m
        X=(slope*slope-x-u)%m
        return (X,(slope*(x-X)-y)%m)
    if x==u and y+v==0: return None
    slope=(3*x*x+a)/(2*y) if P==Q else (v-y)/(u-x)
    X=slope*slope-x-u
    return (X,slope*(x-X)-y)

def mul(n,P,a,m=None):
    if n<0:
        P=(P[0],(-P[1])%m if m is not None else -P[1]); n=-n
    R=None
    while n:
        if n&1: R=add(R,P,a,m)
        P=add(P,P,a,m); n//=2
    return R

def pt(x): return None if x is None else tuple(x)
def reduce(z,p):
    assert z.denominator%p
    return z.numerator*pow(z.denominator,-1,p)%p

def score(A,B,X,Y):
    return max(max(abs(z.numerator).bit_length(),z.denominator.bit_length())
               for z in (Fraction(A),Fraction(B),*X,*Y))

pub_by_key={}
counts=Counter(); per_field=Counter()
for spec in P['fields']:
    p,q,N=spec['p'],spec['q'],spec['order']
    G=None
    for x in range(p):
        ys=[y for y in range(p) if (y*y-x*x*x+x+2)%p==0]
        for y in ys:
            C=mul(N//q,(x,y),-1,p)
            if C is not None and mul(q,C,-1,p) is None:
                G=C; break
        if G is not None: break
    assert G is not None
    for j in range(4):
        w=1+int.from_bytes(hashlib.sha256(f'xedni-large-height-v1|{p}|{j}'.encode()).digest(),'big')%(q-1)
        Q=mul(w,G,-1,p)
        queries=[]
        for t1,t2 in itertools.permutations(P['offsets'],2):
            U=add(Q,mul(-t1,G,-1,p),-1,p)
            V=add(Q,mul(-t2,G,-1,p),-1,p)
            if U is not None and V is not None: queries.append((t1,t2,U,V))
            if len(queries)==16: break
        assert len(queries)==16
        for qi,(t1,t2,U,V) in enumerate(queries):
            for vi,(a,b) in enumerate(P['vectors']):
                key=(p,j,qi,vi)
                row=public[len(pub_by_key)]
                assert (row['p'],row['target_index'],row['query_index'],row['vector_index'])==key
                assert row['q']==q and row['order']==N and row['G']==list(G) and row['w']==w
                assert (row['t1'],row['t2'],pt(row['U']),pt(row['V']))==(t1,t2,U,V)
                assert (row['a'],row['b'])==(a,b)
                hit=add(mul(a,U,-1,p),mul(b,V,-1,p),-1,p) is None
                assert hit==row['public_relation']==((a*(w-t1)+b*(w-t2))%q==0)
                if hit:
                    assert (a+b)%q!=0
                    recovered=((a*t1+b*t2)*pow((a+b)%q,-1,q))%q
                    assert recovered==w and mul(recovered,G,-1,p)==Q
                counts['hits' if hit else 'nonhits']+=1
                per_field[(p,'hits' if hit else 'nonhits')]+=1
                pub_by_key[key]=row
assert len(pub_by_key)==len(public)

by_event=defaultdict(list)
for row in lifts:
    key=(row['p'],row['target_index'],row['query_index'],row['vector_index'])
    source=pub_by_key[key]
    assert row['public_relation']==source['public_relation']
    assert (row['a'],row['b'])==(source['a'],source['b'])
    assert row['status']=='pass'
    assert row['event_id']==f"p{key[0]}-j{key[1]}-q{key[2]}-v{key[3]}"
    assert row['shift'] in [list(z) for z in itertools.product((-1,0,1),repeat=3)]
    p,q,a,b=key[0],row['q'],row['a'],row['b']
    U,V=pt(source['U']),pt(source['V'])
    S=mul(pow(b%q,-1,q),U,-1,p)
    x0,y0=[z-p if z>p//2 else z for z in S]
    kx,ky,kA=row['shift']
    x,y,A=x0+kx*p,y0+ky*p,-1+kA*p
    B=y*y-x*x*x-A*x
    assert (row['x'],row['y'],row['A'],row['B'])==(x,y,A,B)
    assert -16*(4*A**3+27*B**2)!=0 and (B+2)%p==0
    T=(Fraction(x),Fraction(y))
    X=mul(b,T,Fraction(A)); Y=mul(-a,T,Fraction(A))
    assert X is not None and Y is not None
    assert add(mul(a,X,Fraction(A)),mul(b,Y,Fraction(A)),Fraction(A)) is None
    assert [str(z) for z in X]==row['P'] and [str(z) for z in Y]==row['R']
    rX=tuple(reduce(z,p) for z in X); rY=tuple(reduce(z,p) for z in Y)
    assert rX==U and list(rX)==row['P_reduction'] and list(rY)==row['R_reduction']
    assert (rY==V)==source['public_relation']==row['second_match']
    assert score(A,B,X,Y)==row['score_bits']
    by_event[key].append(row)

assert len(by_event)==counts['hits']+32
assert sum(not rows[0]['public_relation'] for rows in by_event.values())==32
for rows in by_event.values():
    assert len(rows)==27 and len({tuple(z['shift']) for z in rows})==27
    assert all(z['control']==(not rows[0]['public_relation']) for z in rows)

caps={}
positive=[rows for rows in by_event.values() if rows[0]['public_relation']]
controls=[rows for rows in by_event.values() if not rows[0]['public_relation']]
for cap in P['caps_bits']:
    base=sum(next(z for z in rows if z['shift']==[0,0,0])['score_bits']<=cap for rows in positive)
    any_hit=sum(min(z['score_bits'] for z in rows)<=cap for rows in positive)
    control_bounded=sum(min(z['score_bits'] for z in rows)<=cap for rows in controls)
    assert base<=any_hit
    caps[str(cap)]={'positive_baseline':base,'positive_any_shift':any_hit,
                    'control_bounded_mismatches':control_bounded,'control_admissions':0}
base_scores=[next(z for z in rows if z['shift']==[0,0,0])['score_bits'] for rows in positive]
best_scores=[min(z['score_bits'] for z in rows) for rows in positive]
summary={'schema':'xedni-large-order-height-admission-audit-v1','status':'PASS',
         'public_attempts':len(public),'public_hits':counts['hits'],
         'positive_events':len(positive),'control_events':len(controls),'lift_attempts':len(lifts),
         'per_field':{str(p):{'hits':per_field[(p,'hits')],'nonhits':per_field[(p,'nonhits')]} for p in (f['p'] for f in P['fields'])},
         'positive_scores':{'baseline_median':statistics.median(base_scores),'best_median':statistics.median(best_scores),
                            'paired_reduction_median':statistics.median(a-b for a,b in zip(base_scores,best_scores))},
         'caps':caps,'run_result_sha256':hashlib.sha256((H/'run-result.json').read_bytes()).hexdigest()}
(H/'audit.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,indent=2,sort_keys=True))
