"""Frozen 81-shift two-image interpolation on public hits and controls."""
from sage.all import EllipticCurve, QQ
from pathlib import Path
import gzip, hashlib, itertools, json, time

H=Path(__file__).resolve().parent
P=json.loads((H/'protocol.json').read_text())
ROOT=H.parent
source=ROOT/'xedni-large-order-height-admission-20261116'
pre=ROOT/'xedni-two-image-precommit-20261116'
assert hashlib.sha256((source/'public.jsonl.gz').read_bytes()).hexdigest()==P['source_public_sha256']
assert hashlib.sha256((source/'run-result.json').read_bytes()).hexdigest()==P['source_public_run_sha256']
assert hashlib.sha256((pre/'queries.jsonl.gz').read_bytes()).hexdigest()==P['source_precommit_query_sha256']
assert hashlib.sha256((pre/'run-result.json').read_bytes()).hexdigest()==P['source_precommit_result_sha256']
public=[json.loads(x) for x in gzip.decompress((source/'public.jsonl.gz').read_bytes()).splitlines()]
parent=[json.loads(x) for x in gzip.decompress((pre/'queries.jsonl.gz').read_bytes()).splitlines()]
parent_map={(r['p'],r['target_index'],r['query_index']):r for r in parent}
assert len(public)==6656 and len(parent)==512
controls={}
for row in public:
    if not row['public_relation']:
        controls.setdefault((row['p'],row['target_index']),row)
assert len(controls)==32
control_keys={(r['p'],r['target_index'],r['query_index'],r['vector_index']) for r in controls.values()}
events=[r for r in public if r['public_relation'] or (r['p'],r['target_index'],r['query_index'],r['vector_index']) in control_keys]
assert len(events)==49 and sum(r['public_relation'] for r in events)==17
START=time.monotonic()

def center(z,p): return z-p if z>p//2 else z

def mod(z,p):
    n,d=int(z.numerator()),int(z.denominator())
    if d%p==0: raise ValueError('nonintegral_reduction')
    return n*pow(d,-1,p)%p

def bits(z):
    return max(abs(int(z.numerator())).bit_length(),int(z.denominator()).bit_length())

rows=[]
counts={'source_public_attempts':len(public),'positive_events':17,'control_events':32,
        'candidate_attempts':0,'candidate_pass':0,'candidate_failure':0,
        'rational_hits_positive':0,'rational_hits_control':0,'centered_parent_matches':0}
for event_index,row in enumerate(events):
    p=row['p']; U=row['U']; V=row['V']; a=row['a']; b=row['b']
    assert U[0]!=V[0]
    x1c,y1c=[center(z,p) for z in U]
    x2c,y2c=[center(z,p) for z in V]
    key=(p,row['target_index'],row['query_index'])
    parent_row=parent_map[key]
    assert parent_row['status']=='pass' and parent_row['branch']=='distinct_x'
    for shift in itertools.product((-1,0,1),repeat=4):
        kx1,ky1,kx2,ky2=shift
        x1,y1=x1c+kx1*p,y1c+ky1*p
        x2,y2=x2c+kx2*p,y2c+ky2*p
        f1=y1*y1-x1*x1*x1; f2=y2*y2-x2*x2*x2
        rec={'event_index':event_index,'p':p,'q':row['q'],'target_index':row['target_index'],
             'query_index':row['query_index'],'vector_index':row['vector_index'],
             'a':a,'b':b,'public_relation':row['public_relation'],'control':not row['public_relation'],
             'shift':list(shift),'status':None}
        counts['candidate_attempts']+=1
        try:
            A=QQ(f1-f2)/QQ(x1-x2); B=QQ(f1)-A*x1
            rec.update({'A':str(A),'B':str(B)})
            C=EllipticCurve(QQ,[A,B]); P1=C(QQ(x1),QQ(y1)); P2=C(QQ(x2),QQ(y2))
            assert mod(A,p)==p-1 and mod(B,p)==p-2
            assert [mod(P1[0],p),mod(P1[1],p)]==U
            assert [mod(P2[0],p),mod(P2[1],p)]==V
            relation=(a*P1+b*P2).is_zero()
            assert not relation or row['public_relation']
            score=max(bits(z) for z in (A,B,QQ(x1),QQ(y1),QQ(x2),QQ(y2)))
            rec.update({'status':'pass','rational_relation':relation,'score_bits':score})
            counts['candidate_pass']+=1
            counts['rational_hits_control' if rec['control'] else 'rational_hits_positive']+=int(relation)
            if shift==(0,0,0,0):
                assert (str(A),str(B))==(parent_row['A'],parent_row['B'])
                counts['centered_parent_matches']+=1
        except Exception as exc:
            rec.update({'status':'failure','error':f'{type(exc).__name__}: {exc}',
                        'rational_relation':None,'score_bits':None})
            counts['candidate_failure']+=1
        rows.append(rec)
        if time.monotonic()-START>P['run_cap_seconds']:
            raise TimeoutError('frozen run cap exceeded')
assert counts['candidate_attempts']==49*81
raw=(''.join(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n' for r in rows)).encode()
blob=gzip.compress(raw,compresslevel=9,mtime=0)
(H/'candidates.jsonl.gz').write_bytes(blob)
result={'schema':'xedni-two-image-shift-grid-result-v1','status':'complete',
        'counts':counts,'elapsed_wall_seconds':time.monotonic()-START,
        'protocol_sha256':hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest(),
        'candidate_raw_sha256':hashlib.sha256(raw).hexdigest(),
        'candidate_gzip_sha256':hashlib.sha256(blob).hexdigest(),
        'candidate_gzip_bytes':len(blob)}
(H/'run-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,indent=2,sort_keys=True))
