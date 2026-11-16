"""Independent pure-Python replay of fresh-query height-selected two-image lifts."""
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
import gzip,hashlib,itertools,json,statistics

H=Path(__file__).resolve().parent; ROOT=H.parent
P=json.loads((H/'protocol.json').read_text()); R=json.loads((H/'run-result.json').read_text())
assert hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest()==R['protocol_sha256']
registry=ROOT/'xedni-large-order-admission-20261115'/'result.json'
family=ROOT/'xedni-large-order-height-admission-20261116'/'protocol.json'
assert hashlib.sha256(registry.read_bytes()).hexdigest()==P['field_registry_sha256']
assert hashlib.sha256(family.read_bytes()).hexdigest()==P['vector_family_source_sha256']
assert json.loads(family.read_text())['vectors']==P['vectors']
selected=[r for r in json.loads(registry.read_text())['rows'] if r['selected']]
assert P['fields']==[{'p':r['field_prime'],'q':r['subgroup_order'],'order':r['curve_order']} for r in selected]

def read(info):
    blob=(H/info['path']).read_bytes()
    assert len(blob)==info['gzip_bytes']
    assert hashlib.sha256(blob).hexdigest()==info['gzip_sha256']
    raw=gzip.decompress(blob)
    assert hashlib.sha256(raw).hexdigest()==info['raw_sha256']
    rows=[json.loads(line) for line in raw.splitlines()]
    assert len(rows)==info['rows']
    return rows
queries=read(R['queries']); vectors=read(R['vectors'])
parts=[read(part) for part in R['candidate_parts']]
assert len(parts)==32 and len(queries)==512 and len(vectors)==6656
candidates=defaultdict(list)
for part in parts:
    for row in part: candidates[row['event_index']].append(row)

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

def center(z,p): return z-p if z>p//2 else z

def mod(z,p):
    z=Fraction(z)
    assert z.denominator%p
    return z.numerator*pow(z.denominator,-1,p)%p

def bits(z):
    z=Fraction(z)
    return max(abs(z.numerator).bit_length(),z.denominator.bit_length())

def calc_candidate(p,U,V,shift):
    x1c,y1c=[center(z,p) for z in U]
    x2c,y2c=[center(z,p) for z in V]
    if shift is None:
        assert U[0]==V[0] and (U[1]+V[1])%p==0
        x1,y1,x2,y2=x1c,y1c,x1c,-y1c
        A=Fraction(-1); B=Fraction(y1*y1-x1*x1*x1+x1)
    else:
        kx1,ky1,kx2,ky2=shift
        x1,y1=x1c+kx1*p,y1c+ky1*p
        x2,y2=x2c+kx2*p,y2c+ky2*p
        f1=y1*y1-x1*x1*x1; f2=y2*y2-x2*x2*x2
        A=Fraction(f1-f2,x1-x2); B=Fraction(f1)-A*x1
    assert 4*A**3+27*B**2!=0
    assert (mod(A,p),mod(B,p))==(p-1,p-2)
    assert (x1%p,y1%p)==U and (x2%p,y2%p)==V
    P1=(Fraction(x1),Fraction(y1)); P2=(Fraction(x2),Fraction(y2))
    assert P1[1]**2==P1[0]**3+A*P1[0]+B
    assert P2[1]**2==P2[0]**3+A*P2[0]+B
    score=max(bits(z) for z in (A,B,*P1,*P2))
    return A,B,P1,P2,score

counts=Counter(); per_field=Counter(); chosen_scores=[]; centered_scores=[]
event_index=0
for spec in P['fields']:
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
        w=1+int.from_bytes(hashlib.sha256(f'xedni-height-selected-v1|{p}|{j}'.encode()).digest(),'big')%(q-1)
        Q=mul(w,G,-1,p)
        pairs=[]
        for t1,t2 in itertools.permutations(P['offsets'],2):
            U=add(Q,mul(-t1,G,-1,p),-1,p)
            V=add(Q,mul(-t2,G,-1,p),-1,p)
            if U is not None and V is not None: pairs.append((t1,t2,U,V))
            if len(pairs)==16: break
        assert len(pairs)==16
        for qi,(t1,t2,U,V) in enumerate(pairs):
            qr=queries[event_index]
            assert (qr['event_index'],qr['p'],qr['q'],qr['order'],tuple(qr['G']),
                    qr['target_index'],qr['w'],qr['query_index'],qr['t1'],qr['t2'],
                    tuple(qr['U']),tuple(qr['V']))==(event_index,p,q,N,G,j,w,qi,t1,t2,U,V)
            equal=U[0]==V[0]
            assert qr['branch']==('equal_x_opposite' if equal else 'distinct_x')
            shifts=[None] if equal else list(itertools.product((-1,0,1),repeat=4))
            rows=candidates[event_index]
            assert len(rows)==len(shifts)
            best=None
            for row,shift in zip(rows,shifts):
                assert row['event_index']==event_index and row['p']==p and row['target_index']==j and row['query_index']==qi
                assert row['shift']==(None if shift is None else list(shift))
                A,B,P1,P2,score=calc_candidate(p,U,V,shift)
                assert row['status']=='pass' and (row['A'],row['B'],row['score_bits'])==(str(A),str(B),score)
                key=(score,() if shift is None else shift)
                if best is None or key<best[0]: best=(key,shift,A,B,P1,P2)
                counts['candidate_attempts']+=1
            key,shift,A,B,P1,P2=best
            assert qr['status']=='pass' and qr['chosen_shift']==(None if shift is None else list(shift))
            assert (qr['A'],qr['B'],qr['score_bits'],qr['candidate_count'])==(
                str(A),str(B),key[0],len(shifts))
            chosen_scores.append(key[0])
            centered_scores.append(next(r['score_bits'] for r in rows if r['shift'] in (None,[0,0,0,0])))
            assert add(P1,(P1[0],-P1[1]),A) is None
            assert (P1[0].numerator%p*pow(P1[0].denominator,-1,p)%p,
                    (-P1[1].numerator)%p)==mul(-1,U,-1,p)
            counts['rational_control_pass']+=1
            for vi,(a,b) in enumerate(P['vectors']):
                vr=vectors[event_index*13+vi]
                assert (vr['event_index'],vr['vector_index'],vr['a'],vr['b'])==(event_index,vi,a,b)
                pub=(a*(w-t1)+b*(w-t2))%q==0
                assert pub==(add(mul(a,U,-1,p),mul(b,V,-1,p),-1,p) is None)
                rel=add(mul(a,P1,A),mul(b,P2,A),A) is None
                assert vr['status']=='tested' and vr['public_relation']==pub and vr['rational_relation']==rel
                assert not rel or pub
                counts['public_hits']+=int(pub); counts['rational_hits']+=int(rel)
                counts['vector_attempts']+=1
                per_field[(p,'public')]+=int(pub); per_field[(p,'rational')]+=int(rel)
            counts['equal_x_queries' if equal else 'distinct_x_queries']+=1
            counts['queries']+=1
            event_index+=1
assert counts['queries']==512 and counts['candidate_attempts']==41392
assert counts['vector_attempts']==6656 and counts['public_hits']==22 and counts['rational_hits']==0
assert counts['rational_control_pass']==512
assert R['counts']['candidate_failure']==0 and R['counts']['candidate_pass']==41392
summary={'schema':'xedni-height-selected-two-image-audit-v1','status':'PASS',
         'counts':dict(counts),'selected_model_score':{'median':statistics.median(chosen_scores),
                                                      'max':max(chosen_scores),'min':min(chosen_scores)},
         'centered_model_score':{'median':statistics.median(centered_scores),
                                 'max':max(centered_scores),'min':min(centered_scores)},
         'height_selection':{'improved_queries':sum(a>b for a,b in zip(centered_scores,chosen_scores)),
                             'paired_reduction_median':statistics.median(a-b for a,b in zip(centered_scores,chosen_scores))},
         'per_field':{str(s['p']):{'public_hits':per_field[(s['p'],'public')],
                                  'rational_hits':per_field[(s['p'],'rational')]} for s in P['fields']},
         'run_result_sha256':hashlib.sha256((H/'run-result.json').read_bytes()).hexdigest()}
(H/'audit.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,indent=2,sort_keys=True))
