"""Independent full-ledger replay of the fresh wide-grid experiment."""
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
import gzip,hashlib,itertools,json

H=Path(__file__).resolve().parent; ROOT=H.parent
P=json.loads((H/'protocol.json').read_text()); R=json.loads((H/'result.json').read_text())
assert hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest()==R['protocol_sha256']
assert hashlib.sha256((ROOT/'xedni-large-order-admission-20261115'/'result.json').read_bytes()).hexdigest()==P['field_registry_sha256']
assert hashlib.sha256((ROOT/'xedni-large-order-height-admission-20261116'/'protocol.json').read_bytes()).hexdigest()==P['vector_family_sha256']
registry=json.loads((ROOT/'xedni-large-order-admission-20261115'/'result.json').read_text())
assert P['fields']==[{'p':r['field_prime'],'q':r['subgroup_order'],'order':r['curve_order']} for r in registry['rows'] if r['selected']]
assert P['vectors']==json.loads((ROOT/'xedni-large-order-height-admission-20261116'/'protocol.json').read_text())['vectors']

def read(info):
    blob=(H/info['path']).read_bytes()
    assert len(blob)==info['gzip_bytes'] and hashlib.sha256(blob).hexdigest()==info['gzip_sha256']
    raw=gzip.decompress(blob)
    assert hashlib.sha256(raw).hexdigest()==info['raw_sha256']
    rows=[json.loads(x) for x in raw.splitlines()]
    assert len(rows)==info['rows']
    return rows

queries=read(R['files']['queries']); vectors=read(R['files']['vectors']); hits=read(R['files']['hit_candidates'])
parts=[read(x) for x in R['files']['candidate_parts']]
assert len(parts)==32 and len(queries)==512 and len(vectors)==6656
candidates=defaultdict(list)
for part in parts:
    for row in part: candidates[row['event_index']].append(row)
hit_map=defaultdict(list)
for row in hits: hit_map[(row['event_index'],row['vector_index'])].append(row)

def plus(P,Q,A,m=None):
    if P is None: return Q
    if Q is None: return P
    x,y=P; u,v=Q
    if m is not None:
        if x==u and (y+v)%m==0: return None
        s=((3*x*x+A)*pow(2*y,-1,m))%m if P==Q else ((v-y)*pow(u-x,-1,m))%m
        z=(s*s-x-u)%m
        return (z,(s*(x-z)-y)%m)
    if x==u and y==-v: return None
    s=Fraction(3*x*x+A,2*y) if P==Q else Fraction(v-y,u-x)
    z=s*s-x-u
    return (z,s*(x-z)-y)

def times(n,P,A,m=None):
    if n<0: P=(P[0],(-P[1])%m if m is not None else -P[1]); n=-n
    R=None
    while n:
        if n&1: R=plus(R,P,A,m)
        P=plus(P,P,A,m); n//=2
    return R

def repeated(n,P,A):
    if n<0: P=(P[0],-P[1]); n=-n
    R=None
    for _ in range(n): R=plus(R,P,A)
    return R

def generator(p,q,N):
    squares=defaultdict(list)
    for y in range(p): squares[y*y%p].append(y)
    for x in range(p):
        for y in squares[(x*x*x-x-2)%p]:
            G=times(N//q,(x,y),-1,p)
            if G is not None and times(q,G,-1,p) is None:return G
    raise AssertionError('generator_missing')

def val(z,p): return z.numerator*pow(z.denominator,-1,p)%p

def calc(q,row):
    p=q['p']; U=q['U']; V=q['V']; shift=row['shift']
    def cent(x):return x-p if x>p//2 else x
    x1,y1=map(cent,U);x2,y2=map(cent,V)
    if shift is None:
        assert q['branch']=='equal_x_opposite' and U[0]==V[0] and (U[1]+V[1])%p==0
        x2,y2=x1,-y1
        A=Fraction(-1);B=Fraction(y1*y1-x1*x1*x1+x1)
    else:
        x1+=p*shift[0];y1+=p*shift[1];x2+=p*shift[2];y2+=p*shift[3]
        A=Fraction((y1*y1-x1*x1*x1)-(y2*y2-x2*x2*x2),x1-x2)
        B=Fraction(y1*y1-x1*x1*x1)-A*x1
    assert 4*A**3+27*B**2!=0 and (val(A,p),val(B,p))==(p-1,p-2)
    assert (x1%p,y1%p)==tuple(U) and (x2%p,y2%p)==tuple(V)
    P1=(Fraction(x1),Fraction(y1));P2=(Fraction(x2),Fraction(y2))
    assert P1[1]**2==P1[0]**3+A*P1[0]+B and P2[1]**2==P2[0]**3+A*P2[0]+B
    score=max(max(abs(t.numerator).bit_length(),t.denominator.bit_length()) for t in (A,B,*P1,*P2))
    assert (str(A),str(B),score)==(row['A'],row['B'],row['score_bits'])
    return A,P1,P2,score

count=Counter();event=0
for spec in P['fields']:
    p,q,N=spec['p'],spec['q'],spec['order'];G=generator(p,q,N)
    squares={y*y%p for y in range(p)}
    assert 1+sum(1 if (x*x*x-x-2)%p==0 else 2 if (x*x*x-x-2)%p in squares else 0 for x in range(p))==N
    for j in range(4):
        w=1+int.from_bytes(hashlib.sha256(f'xedni-wide-grid-v1|{p}|{j}'.encode()).digest(),'big')%(q-1)
        Q=times(w,G,-1,p);pairs=[]
        for t1,t2 in itertools.permutations(P['offsets'],2):
            U=plus(Q,times(-t1,G,-1,p),-1,p);V=plus(Q,times(-t2,G,-1,p),-1,p)
            if U is not None and V is not None:pairs.append((t1,t2,U,V))
            if len(pairs)==16:break
        assert len(pairs)==16
        for qi,(t1,t2,U,V) in enumerate(pairs):
            qr=queries[event]
            assert (qr['event_index'],qr['p'],qr['q'],qr['order'],tuple(qr['G']),qr['target_index'],qr['w'],qr['query_index'],qr['t1'],qr['t2'],tuple(qr['U']),tuple(qr['V']))==(event,p,q,N,G,j,w,qi,t1,t2,U,V)
            shifts=[None] if U[0]==V[0] else list(itertools.product(range(-2,3),repeat=4))
            rows=candidates[event]
            assert len(rows)==len(shifts)==qr['candidate_count']
            chosen=None;lifted=[]
            for row,shift in zip(rows,shifts):
                assert row['shift']==(None if shift is None else list(shift)) and row['status']=='pass'
                A,P1,P2,score=calc(qr,row)
                lifted.append((A,P1,P2))
                key=(score,() if shift is None else shift)
                if chosen is None or key<chosen[0]:chosen=(key,row,A,P1,P2)
                count['candidate_pass']+=1
            _,selected,A,P1,P2=chosen
            assert qr['status']=='pass' and qr['chosen_shift']==selected['shift'] and qr['score_bits']==selected['score_bits']
            for vi,(a,b) in enumerate(P['vectors']):
                vr=vectors[event*13+vi]
                assert (vr['event_index'],vr['vector_index'],vr['a'],vr['b'])==(event,vi,a,b)
                pub=(a*(w-t1)+b*(w-t2))%q==0
                assert pub==(plus(times(a,U,-1,p),times(b,V,-1,p),-1,p) is None)
                rel=plus(repeated(a,P1,A),repeated(b,P2,A),A) is None
                assert vr['status']=='tested' and vr['public_relation']==pub and vr['selected_rational_relation']==rel
                assert not rel or pub
                count['vector_tests']+=1;count['public_hits']+=int(pub);count['selected_rational_hits']+=int(rel)
                hr=hit_map.get((event,vi),[])
                assert len(hr)==(len(lifted) if pub else 0)
                for record,(C,U1,V1),shift in zip(hr,lifted,shifts):
                    assert record['shift']==(None if shift is None else list(shift))
                    status='relation' if plus(repeated(a,U1,C),repeated(b,V1,C),C) is None else 'nonidentity'
                    assert record['status']==status
                    count['hit_candidate_tests']+=1;count['hit_candidate_relations']+=int(status=='relation')
            count['query_attempts']+=1;count['equal_x' if shifts==[None] else 'distinct_x']+=1
            event+=1
assert event==512
for k,v in count.items():assert R['counts'][k]==v,(k,v,R['counts'][k])
assert R['counts']['candidate_failure']==R['counts']['hit_candidate_failures']==0
out={'schema':'xedni-fresh-wide-grid-audit-v1','status':'PASS','counts':dict(count),'result_sha256':hashlib.sha256((H/'result.json').read_bytes()).hexdigest()}
(H/'audit-result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(json.dumps(out,sort_keys=True,indent=2))
