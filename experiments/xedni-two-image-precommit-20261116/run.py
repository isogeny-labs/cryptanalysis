"""Precommit one rational curve and two lifted points per public query."""
from sage.all import EllipticCurve, GF, QQ
from pathlib import Path
import gzip, hashlib, json, time

H=Path(__file__).resolve().parent
P=json.loads((H/'protocol.json').read_text())
S=H.parent/'xedni-large-order-height-admission-20261116'/'public.jsonl.gz'
assert hashlib.sha256(S.read_bytes()).hexdigest()==P['source_public_sha256']
source=[json.loads(line) for line in gzip.decompress(S.read_bytes()).splitlines()]
assert len(source)==P['vector_attempts']
START=time.monotonic()

def center(z,p):
    return z-p if z>p//2 else z

def mod(z,p):
    n,d=int(z.numerator()),int(z.denominator())
    if d%p==0: raise ValueError('nonintegral_reduction')
    return n*pow(d,-1,p)%p

def packed(name,rows):
    raw=(''.join(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n' for row in rows)).encode()
    blob=gzip.compress(raw,compresslevel=9,mtime=0)
    (H/name).write_bytes(blob)
    return {'path':name,'rows':len(rows),'raw_sha256':hashlib.sha256(raw).hexdigest(),
            'gzip_sha256':hashlib.sha256(blob).hexdigest(),'gzip_bytes':len(blob)}

queries=[]; attempts=[]; counts={'query_distinct_x':0,'query_equal_x':0,'query_pass':0,
 'query_failure':0,'vector_attempts':0,'public_hits':0,'rational_hits':0,'relation_mismatches':0}
for start in range(0,len(source),13):
    group=source[start:start+13]
    assert len(group)==13
    first=group[0]
    key=(first['p'],first['target_index'],first['query_index'])
    assert all((r['p'],r['target_index'],r['query_index'])==key for r in group)
    p=first['p']; u,v=first['U'],first['V']
    assert u is not None and v is not None
    xu,yu=[center(z,p) for z in u]
    xv,yv=[center(z,p) for z in v]
    branch='equal_x_opposite' if u[0]==v[0] else 'distinct_x'
    counts['query_equal_x' if branch=='equal_x_opposite' else 'query_distinct_x']+=1
    qr={'p':p,'q':first['q'],'target_index':first['target_index'],'query_index':first['query_index'],
        'U':u,'V':v,'branch':branch,'status':None}
    try:
        if branch=='equal_x_opposite':
            assert u[0]==v[0] and (u[1]+v[1])%p==0
            xv,yv=xu,-yu
            A=QQ(-1); B=QQ(yu*yu-xu*xu*xu+xu)
        else:
            fu=yu*yu-xu*xu*xu
            fv=yv*yv-xv*xv*xv
            A=QQ(fu-fv)/QQ(xu-xv)
            B=QQ(fu)-A*xu
        C=EllipticCurve(QQ,[A,B])
        Uq=C(QQ(xu),QQ(yu)); Vq=C(QQ(xv),QQ(yv))
        assert mod(A,p)==p-1 and mod(B,p)==p-2
        assert [mod(Uq[0],p),mod(Uq[1],p)]==u
        assert [mod(Vq[0],p),mod(Vq[1],p)]==v
        assert int(C.discriminant())!=0 if C.discriminant().denominator()==1 else C.discriminant()!=0
        qr.update({'status':'pass','A':str(A),'B':str(B),
                   'P':[str(Uq[0]),str(Uq[1])],'R':[str(Vq[0]),str(Vq[1])]})
        counts['query_pass']+=1
    except Exception as exc:
        C=Uq=Vq=None
        qr.update({'status':'failure','error':f'{type(exc).__name__}: {exc}'})
        counts['query_failure']+=1
    queries.append(qr)
    for row in group:
        a,b=row['a'],row['b']
        rec={'p':p,'target_index':row['target_index'],'query_index':row['query_index'],
             'vector_index':row['vector_index'],'a':a,'b':b,'public_relation':row['public_relation'],
             'query_status':qr['status']}
        counts['vector_attempts']+=1
        counts['public_hits']+=int(row['public_relation'])
        if qr['status']=='pass':
            relation=(a*Uq+b*Vq).is_zero()
            rec.update({'status':'tested','rational_relation':relation})
            counts['rational_hits']+=int(relation)
            if relation and not row['public_relation']:
                counts['relation_mismatches']+=1
        else:
            rec.update({'status':'query_failure','rational_relation':None})
        attempts.append(rec)
    if time.monotonic()-START>P['run_cap_seconds']:
        break
qfile=packed('queries.jsonl.gz',queries)
vfile=packed('vectors.jsonl.gz',attempts)
status='complete' if len(queries)==P['query_count'] and counts['vector_attempts']==P['vector_attempts'] else 'capped'
if counts['relation_mismatches']: status='invariant_failure'
result={'schema':'xedni-two-image-precommit-result-v1','status':status,'counts':counts,
        'elapsed_wall_seconds':time.monotonic()-START,'protocol_sha256':hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest(),
        'source_public_sha256':P['source_public_sha256'],'queries':qfile,'vectors':vfile}
(H/'run-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,indent=2,sort_keys=True))
