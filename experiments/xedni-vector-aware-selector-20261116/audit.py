"""Independent modular-Jacobian and Fraction replay of leading defects."""
from collections import Counter
from fractions import Fraction
from pathlib import Path
import gzip
import hashlib
import itertools
import json

H=Path(__file__).resolve().parent
P=json.loads((H/'protocol.json').read_text())
R=json.loads((H/'run-result.json').read_text())
SOURCE=H.parent/'xedni-height-selected-two-image-20261116'/'protocol.json'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==P['source_protocol_sha256']
PRIOR=H.parent/'xedni-qdefect-proxy-20261116'/'protocol.json'
assert hashlib.sha256(PRIOR.read_bytes()).hexdigest()==P['prior_proxy_protocol_sha256']
LEADING=H.parent/'xedni-leading-defect-selector-20261116'/'protocol.json'
assert hashlib.sha256(LEADING.read_bytes()).hexdigest()==P['prior_leading_protocol_sha256']
BASE=json.loads(SOURCE.read_text())
assert hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest()==R['protocol_sha256']

def read_part(meta):
    blob=(H/meta['path']).read_bytes()
    assert len(blob)==meta['gzip_bytes']
    assert hashlib.sha256(blob).hexdigest()==meta['gzip_sha256']
    raw=gzip.decompress(blob)
    assert hashlib.sha256(raw).hexdigest()==meta['raw_sha256']
    rows=[json.loads(line) for line in raw.splitlines()]
    assert len(rows)==meta['rows']
    return rows

queries=read_part(R['queries'])
vectors=read_part(R['vectors'])
assert len(queries)==512 and len(vectors)==6656
assert len(R['summaries'])==len(R['candidate_parts'])

def add(Pt,Qt,A,m=None):
    if Pt is None: return Qt
    if Qt is None: return Pt
    x,y=Pt; u,v=Qt
    if m is not None:
        if x==u and (y+v)%m==0: return None
        slope=((3*x*x+A)*pow(2*y,-1,m))%m if Pt==Qt else ((v-y)*pow(u-x,-1,m))%m
        X=(slope*slope-x-u)%m
        return X,(slope*(x-X)-y)%m
    if x==u and y+v==0: return None
    slope=(3*x*x+A)/(2*y) if Pt==Qt else (v-y)/(u-x)
    X=slope*slope-x-u
    return X,slope*(x-X)-y

def mul(n,Pt,A,m=None):
    if n<0:
        Pt=(Pt[0],(-Pt[1])%m if m is not None else -Pt[1]); n=-n
    out=None
    while n:
        if n&1: out=add(out,Pt,A,m)
        Pt=add(Pt,Pt,A,m); n//=2
    return out

def jdbl(Pt,A,M):
    X,Y,Z=Pt
    if Z==0 or Y==0: return (0,1,0)
    XX=X*X%M; YY=Y*Y%M; YYYY=YY*YY%M; ZZ=Z*Z%M
    S=2*((X+YY)**2-XX-YYYY)%M
    Mv=(3*XX+A*ZZ*ZZ)%M
    X3=(Mv*Mv-2*S)%M
    Y3=(Mv*(S-X3)-8*YYYY)%M
    Z3=((Y+Z)**2-YY-ZZ)%M
    return X3,Y3,Z3

def jadd(Pt,Qt,A,M):
    if Pt[2]==0: return Qt
    if Qt[2]==0: return Pt
    X1,Y1,Z1=Pt; X2,Y2,Z2=Qt
    Z1Z1=Z1*Z1%M; Z2Z2=Z2*Z2%M
    U1=X1*Z2Z2%M; U2=X2*Z1Z1%M
    S1=Y1*Z2*Z2Z2%M; S2=Y2*Z1*Z1Z1%M
    if U1==U2:
        return jdbl(Pt,A,M) if S1==S2 else (0,1,0)
    HH=(U2-U1)%M
    I=(2*HH)**2%M; J=HH*I%M; rr=2*(S2-S1)%M; V=U1*I%M
    X3=(rr*rr-J-2*V)%M
    Y3=(rr*(V-X3)-2*S1*J)%M
    Z3=(((Z1+Z2)**2-Z1Z1-Z2Z2)*HH)%M
    return X3,Y3,Z3

def jmul(n,Pt,A,M):
    out=(0,1,0)
    while n:
        if n&1: out=jadd(out,Pt,A,M)
        Pt=jdbl(Pt,A,M); n//=2
    return out

def plead(Pt,A,q,p,precision):
    M=p**precision
    X,Y,Z=jmul(q,(int(Pt[0])%M,int(Pt[1])%M,1),A%M,M)
    assert Z%p==0 and X%p!=0 and Y%p!=0
    t=(-X*Z*pow(Y,-1,M))%M
    lead=(t//p)%p
    if t==0: return precision,lead
    k=0
    while t%p==0: t//=p; k+=1
    assert k>=1
    return k,lead

def center(z,p): return z-p if z>p//2 else z

def mod(z,p):
    z=Fraction(z)
    assert z.denominator%p
    return z.numerator*pow(z.denominator,-1,p)%p

def bits(z):
    z=Fraction(z)
    return max(abs(z.numerator).bit_length(),z.denominator.bit_length())

def v_int(n,p):
    n=abs(n)
    if n==0: return None
    k=0
    while n%p==0: n//=p; k+=1
    return k

def v_rat(z,p):
    z=Fraction(z)
    if z.numerator==0: return None
    return v_int(z.numerator,p)-v_int(z.denominator,p)

def candidate(p,U,V,shift):
    x1c,y1c=[center(z,p) for z in U]
    x2c,y2c=[center(z,p) for z in V]
    if shift is None:
        assert U[0]==V[0] and (U[1]+V[1])%p==0
        x1,y1,x2,y2=x1c,y1c,x1c,-y1c
        A,B=Fraction(-1),Fraction(y1*y1-x1**3+x1)
    else:
        x1,y1=x1c+shift[0]*p,y1c+shift[1]*p
        x2,y2=x2c+shift[2]*p,y2c+shift[3]*p
        A=Fraction((y1*y1-x1**3)-(y2*y2-x2**3),x1-x2)
        B=Fraction(y1*y1-x1**3)-A*x1
    assert 4*A**3+27*B**2!=0
    assert (mod(A,p),mod(B,p))==(p-1,p-2)
    assert (x1%p,y1%p)==tuple(U) and (x2%p,y2%p)==tuple(V)
    P1,P2=(Fraction(x1),Fraction(y1)),(Fraction(x2),Fraction(y2))
    assert P1[1]**2==P1[0]**3+A*P1[0]+B
    assert P2[1]**2==P2[0]**3+A*P2[0]+B
    score=max(bits(z) for z in (A,B,*P1,*P2))
    return A,B,P1,P2,score

counts=Counter(); q1_hist=Counter(); q2_hist=Counter(); family_hist=Counter(); residual_hist=Counter()
event_index=0; hit_index=0
for spec in BASE['fields']:
    p,q,N=spec['p'],spec['q'],spec['order']
    G=None
    for x in range(p):
        for y in range(p):
            if (y*y-x*x*x+x+2)%p: continue
            T=mul(N//q,(x,y),-1,p)
            if T is not None and mul(q,T,-1,p) is None:
                G=T; break
        if G is not None: break
    assert G is not None
    for j in range(4):
        w=1+int.from_bytes(hashlib.sha256(f'xedni-vector-aware-v1|{p}|{j}'.encode()).digest(),'big')%(q-1)
        Q=mul(w,G,-1,p)
        pairs=[]
        for t1,t2 in itertools.permutations(BASE['offsets'],2):
            U=add(Q,mul(-t1,G,-1,p),-1,p)
            V=add(Q,mul(-t2,G,-1,p),-1,p)
            if U is not None and V is not None: pairs.append((t1,t2,U,V))
            if len(pairs)==16: break
        assert len(pairs)==16
        for qi,(t1,t2,U,V) in enumerate(pairs):
            query=queries[event_index]
            assert (query['event_index'],query['p'],query['q'],query['order'],tuple(query['G']),
                    query['target_index'],query['w'],query['query_index'],query['t1'],query['t2'],
                    tuple(query['U']),tuple(query['V']))==(event_index,p,q,N,G,j,w,qi,t1,t2,U,V)
            assert query['branch']==('equal_x_opposite' if U[0]==V[0] else 'distinct_x')
            counts['queries']+=1
            for vi,(a,b) in enumerate(BASE['vectors']):
                vector=vectors[event_index*13+vi]
                assert (vector['event_index'],vector['vector_index'],vector['a'],vector['b'])==(event_index,vi,a,b)
                public=(a*(w-t1)+b*(w-t2))%q==0
                assert public==(add(mul(a,U,-1,p),mul(b,V,-1,p),-1,p) is None)
                assert vector['public_relation']==public
                counts['vector_tests']+=1; counts['public_hits']+=int(public)
                if not public: continue
                summary=R['summaries'][hit_index]
                rows=read_part(R['candidate_parts'][hit_index])
                assert (summary['event_index'],summary['vector_index'],summary['p'],summary['a'],summary['b'])==(
                    event_index,vi,p,a,b)
                shifts=[None] if U[0]==V[0] else list(itertools.product(P['shift_values'],repeat=4))
                assert len(rows)==len(shifts)
                eligible=[]
                for row,shift in zip(rows,shifts):
                    assert row['event_index']==event_index and row['vector_index']==vi
                    assert row['shift']==(None if shift is None else list(shift))
                    A,B,P1,P2,score=candidate(p,U,V,shift)
                    assert row['status']=='pass' and row['proxy_status']=='pass'
                    assert (row['A'],row['B'],row['model_score_bits'])==(str(A),str(B),score)
                    A_mod=mod(A,p**P['proxy_precision'])
                    k1,c1=plead(P1,A_mod,q,p,P['proxy_precision'])
                    k2,c2=plead(P2,A_mod,q,p,P['proxy_precision'])
                    family_score=sum((aa*c1+bb*c2)%p==0 for aa,bb in BASE['vectors'])
                    assert (row['qdepth1'],row['qdepth2'],row['lead1'],row['lead2'],row['family_score'])==(k1,k2,c1,c2,family_score)
                    assert add(P1,(P1[0],-P1[1]),A) is None
                    residual=add(mul(a,P1,A),mul(b,P2,A),A)
                    depth=None if residual is None else v_rat(-residual[0]/residual[1],p)
                    assert (row['rational_relation'],row['residual_depth'])==(residual is None,depth)
                    assert residual is None or depth>=1
                    predicted=(a*c1+b*c2)%p==0
                    matched=predicted==(depth is None or depth>=2)
                    assert (row['predicted_depth_ge_2'],row['prediction_match'])==(predicted,matched)
                    q1_hist[k1]+=1; q2_hist[k2]+=1; family_hist[family_score]+=1
                    residual_hist[depth]+=1
                    counts['candidate_attempts']+=1; counts['candidate_pass']+=1
                    counts['rational_controls']+=1; counts['qproxy_controls']+=2
                    counts['prediction_pass' if matched else 'prediction_fail']+=1
                    counts['rational_hits']+=int(residual is None)
                    eligible.append(row)
                baseline=min(eligible,key=lambda r:(r['model_score_bits'],() if r['shift'] is None else r['shift']))
                chosen=min(eligible,key=lambda r:(-r['family_score'],r['model_score_bits'],
                                                   () if r['shift'] is None else r['shift']))
                oracle_candidates=[r for r in eligible if (a*r['lead1']+b*r['lead2'])%p==0]
                oracle=min(oracle_candidates,key=lambda r:(r['model_score_bits'],
                    () if r['shift'] is None else r['shift'])) if oracle_candidates else None
                aware=oracle if oracle is not None else baseline
                assert summary=={'event_index':event_index,'vector_index':vi,'p':p,'a':a,'b':b,
                    'candidate_attempts':len(rows),'eligible':len(eligible),
                    'baseline_shift':baseline['shift'],'proxy_shift':chosen['shift'],
                    'oracle_shift':None if oracle is None else oracle['shift'],
                    'aware_shift':aware['shift'],
                    'proxy_family_score':chosen['family_score'],
                    'baseline_residual_depth':baseline['residual_depth'],
                    'proxy_residual_depth':chosen['residual_depth'],
                    'oracle_residual_depth':None if oracle is None else oracle['residual_depth'],
                    'aware_residual_depth':aware['residual_depth'],
                    'baseline_relation':baseline['rational_relation'],
                    'proxy_relation':chosen['rational_relation'],
                    'aware_relation':aware['rational_relation'],
                    'predicted_candidates':sum(bool(r['predicted_depth_ge_2']) for r in rows),
                    'all_rational_hits':sum(bool(r['rational_relation']) for r in rows)}
                counts['proxy_selection_events']+=1
                counts['equal_x_hits']+=int(U[0]==V[0])
                hit_index+=1
            event_index+=1
assert hit_index==len(R['candidate_parts'])==len(R['summaries'])
assert all(counts[k]==v for k,v in R['counts'].items())
assert counts['candidate_attempts']==625*counts['public_hits']
result={'schema':'xedni-vector-aware-selector-audit-v1','status':'PASS',
        'counts':dict(counts),'qdepth1_histogram':dict(sorted(q1_hist.items())),
        'qdepth2_histogram':dict(sorted(q2_hist.items())),
        'family_score_histogram':dict(sorted(family_hist.items())),
        'residual_depth_histogram':dict(sorted(residual_hist.items())),
        'proxy_changed_hits':sum(s['proxy_shift']!=s['baseline_shift'] for s in R['summaries']),
        'proxy_depth_improvements':sum(s['proxy_residual_depth']>s['baseline_residual_depth'] for s in R['summaries']),
        'proxy_depth_worsenings':sum(s['proxy_residual_depth']<s['baseline_residual_depth'] for s in R['summaries']),
        'aware_depth_improvements':sum(s['aware_residual_depth']>s['baseline_residual_depth'] for s in R['summaries']),
        'aware_depth_worsenings':sum(s['aware_residual_depth']<s['baseline_residual_depth'] for s in R['summaries']),
        'aware_selected_depth2':sum(s['aware_residual_depth'] is not None and s['aware_residual_depth']>=2 for s in R['summaries']),
        'oracle_depth2_hits':sum(s['oracle_residual_depth'] is not None and s['oracle_residual_depth']>=2 for s in R['summaries']),
        'predicted_candidates':sum(s['predicted_candidates'] for s in R['summaries']),
        'run_result_sha256':hashlib.sha256((H/'run-result.json').read_bytes()).hexdigest()}
(H/'audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,indent=2,sort_keys=True))
