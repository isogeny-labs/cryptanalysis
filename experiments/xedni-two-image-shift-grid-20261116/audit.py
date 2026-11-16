"""Independent exact replay of every two-image shift candidate."""
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
import gzip, hashlib, itertools, json, statistics

H=Path(__file__).resolve().parent; ROOT=H.parent
P=json.loads((H/'protocol.json').read_text()); R=json.loads((H/'run-result.json').read_text())
assert hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest()==R['protocol_sha256']
S=ROOT/'xedni-large-order-height-admission-20261116'
PRE=ROOT/'xedni-two-image-precommit-20261116'
for file,key in [(S/'public.jsonl.gz','source_public_sha256'),
                 (S/'run-result.json','source_public_run_sha256'),
                 (PRE/'queries.jsonl.gz','source_precommit_query_sha256'),
                 (PRE/'run-result.json','source_precommit_result_sha256')]:
    assert hashlib.sha256(file.read_bytes()).hexdigest()==P[key]
public=[json.loads(line) for line in gzip.decompress((S/'public.jsonl.gz').read_bytes()).splitlines()]
parent=[json.loads(line) for line in gzip.decompress((PRE/'queries.jsonl.gz').read_bytes()).splitlines()]
parent_map={(r['p'],r['target_index'],r['query_index']):r for r in parent}
assert len(public)==6656 and len(parent)==512
amendment=json.loads((H/'storage-amendment.json').read_text())
assert amendment['measurement_changed'] is False
assert amendment['raw_sha256']==R['candidate_raw_sha256']
assert amendment['original_gzip_sha256']==R['candidate_gzip_sha256']
chunks=[]
for part in amendment['parts']:
    packed=(H/part['path']).read_bytes()
    assert len(packed)==part['bytes']
    assert hashlib.sha256(packed).hexdigest()==part['sha256']
    chunk=gzip.decompress(packed)
    assert chunk.count(b'\n')==part['lines']
    chunks.append(chunk)
raw=b''.join(chunks)
assert hashlib.sha256(raw).hexdigest()==R['candidate_raw_sha256']
original=gzip.compress(raw,compresslevel=9,mtime=0)
assert len(original)==R['candidate_gzip_bytes']
assert hashlib.sha256(original).hexdigest()==R['candidate_gzip_sha256']
rows=[json.loads(line) for line in raw.splitlines()]
assert len(rows)==3969

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

def bits(z): return max(abs(z.numerator).bit_length(),z.denominator.bit_length())

for r in public:
    q=r['q']; a=r['a']; b=r['b']; w=r['w']; t1=r['t1']; t2=r['t2']
    assert r['public_relation']==((a*(w-t1)+b*(w-t2))%q==0)
controls={}
for r in public:
    if not r['public_relation']:
        controls.setdefault((r['p'],r['target_index']),r)
keys={(r['p'],r['target_index'],r['query_index'],r['vector_index']) for r in controls.values()}
events=[r for r in public if r['public_relation'] or (r['p'],r['target_index'],r['query_index'],r['vector_index']) in keys]
assert len(events)==49 and sum(r['public_relation'] for r in events)==17
counts=Counter(); grouped=defaultdict(list)
for event_index,event in enumerate(events):
    p,q,a,b=event['p'],event['q'],event['a'],event['b']
    U,V=tuple(event['U']),tuple(event['V'])
    assert U[0]!=V[0]
    G=tuple(event['G'])
    assert mul(q,G,-1,p) is None
    assert mul((event['w']-event['t1'])%q,G,-1,p)==U
    assert mul((event['w']-event['t2'])%q,G,-1,p)==V
    assert (add(mul(a,U,-1,p),mul(b,V,-1,p),-1,p) is None)==event['public_relation']
    x1c,y1c=[center(z,p) for z in U]
    x2c,y2c=[center(z,p) for z in V]
    parent_row=parent_map[(p,event['target_index'],event['query_index'])]
    for candidate_index,shift in enumerate(itertools.product((-1,0,1),repeat=4)):
        rec=rows[event_index*81+candidate_index]
        assert rec['event_index']==event_index and rec['shift']==list(shift)
        assert (rec['p'],rec['q'],rec['target_index'],rec['query_index'],rec['vector_index'])==(
            p,q,event['target_index'],event['query_index'],event['vector_index'])
        assert (rec['a'],rec['b'],rec['public_relation'],rec['control'])==(
            a,b,event['public_relation'],not event['public_relation'])
        kx1,ky1,kx2,ky2=shift
        x1,y1=x1c+kx1*p,y1c+ky1*p
        x2,y2=x2c+kx2*p,y2c+ky2*p
        f1=y1*y1-x1*x1*x1; f2=y2*y2-x2*x2*x2
        A=Fraction(f1-f2,x1-x2); B=Fraction(f1)-A*x1
        assert (rec['A'],rec['B'])==(str(A),str(B))
        assert 4*A**3+27*B**2!=0
        P1=(Fraction(x1),Fraction(y1)); P2=(Fraction(x2),Fraction(y2))
        assert P1[1]**2==P1[0]**3+A*P1[0]+B
        assert P2[1]**2==P2[0]**3+A*P2[0]+B
        assert (mod(A,p),mod(B,p))==(p-1,p-2)
        assert (mod(P1[0],p),mod(P1[1],p))==U
        assert (mod(P2[0],p),mod(P2[1],p))==V
        relation=add(mul(a,P1,A),mul(b,P2,A),A) is None
        assert rec['status']=='pass' and rec['rational_relation']==relation
        assert not relation or event['public_relation']
        score=max(bits(z) for z in (A,B,*P1,*P2))
        assert rec['score_bits']==score
        if shift==(0,0,0,0):
            assert (str(A),str(B))==(parent_row['A'],parent_row['B'])
            counts['centered_matches']+=1
        counts['rational_hits_control' if rec['control'] else 'rational_hits_positive']+=int(relation)
        counts['attempts']+=1
        grouped[event_index].append(rec)
assert counts['attempts']==3969 and counts['centered_matches']==49
assert counts['rational_hits_positive']==counts['rational_hits_control']==0
caps={}
positive=[grouped[i] for i,e in enumerate(events) if e['public_relation']]
controls=[grouped[i] for i,e in enumerate(events) if not e['public_relation']]
for cap in P['caps_bits']:
    caps[str(cap)]={'positive_centered_models':sum(next(r for r in rr if r['shift']==[0,0,0,0])['score_bits']<=cap for rr in positive),
                    'positive_any_shift_models':sum(min(r['score_bits'] for r in rr)<=cap for rr in positive),
                    'positive_rational_relations':0,
                    'control_any_shift_models':sum(min(r['score_bits'] for r in rr)<=cap for rr in controls),
                    'control_rational_relations':0}
centered=[next(r for r in rr if r['shift']==[0,0,0,0])['score_bits'] for rr in positive]
best=[min(r['score_bits'] for r in rr) for rr in positive]
summary={'schema':'xedni-two-image-shift-grid-audit-v1','status':'PASS','counts':dict(counts),
         'positive_events':17,'control_events':32,'caps':caps,
         'positive_scores':{'centered_median':statistics.median(centered),'best_median':statistics.median(best),
                            'paired_reduction_median':statistics.median(a-b for a,b in zip(centered,best))},
         'run_result_sha256':hashlib.sha256((H/'run-result.json').read_bytes()).hexdigest()}
(H/'audit.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,indent=2,sort_keys=True))
