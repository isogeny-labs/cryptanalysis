"""Preselect two-image lifts by model height on fresh public queries."""
from sage.all import EllipticCurve, GF, QQ
from fractions import Fraction
from pathlib import Path
import gzip, hashlib, itertools, json, time

H=Path(__file__).resolve().parent; ROOT=H.parent
P=json.loads((H/'protocol.json').read_text())
registry=ROOT/'xedni-large-order-admission-20261115'/'result.json'
family=ROOT/'xedni-large-order-height-admission-20261116'/'protocol.json'
assert hashlib.sha256(registry.read_bytes()).hexdigest()==P['field_registry_sha256']
assert hashlib.sha256(family.read_bytes()).hexdigest()==P['vector_family_source_sha256']
assert json.loads(family.read_text())['vectors']==P['vectors']
START=time.monotonic()

def center(z,p): return z-p if z>p//2 else z

def parts(z):
    numerator=z.numerator
    denominator=z.denominator
    return int(numerator() if callable(numerator) else numerator), int(denominator() if callable(denominator) else denominator)

def mod(z,p):
    n,d=parts(z)
    if d%p==0: raise ValueError('nonintegral_reduction')
    return n*pow(d,-1,p)%p

def bits(z):
    n,d=parts(z)
    return max(abs(n).bit_length(),d.bit_length())

def coords(point): return None if point.is_zero() else [int(point[0]),int(point[1])]

def generator(E,p,q,N):
    for x in range(p):
        for T in sorted(E.lift_x(GF(p)(x),all=True),key=lambda z:int(z[1])):
            G=(N//q)*T
            if not G.is_zero() and (q*G).is_zero(): return G
    raise ValueError('generator_missing')

def candidate(p,U,V,shift):
    x1c,y1c=[center(z,p) for z in U]
    x2c,y2c=[center(z,p) for z in V]
    if shift is None:
        if U[0]!=V[0] or (U[1]+V[1])%p!=0: raise ValueError('invalid_equal_x_exception')
        x1,y1,x2,y2=x1c,y1c,x1c,-y1c
        A=Fraction(-1); B=Fraction(y1*y1-x1*x1*x1+x1)
    else:
        kx1,ky1,kx2,ky2=shift
        x1,y1=x1c+kx1*p,y1c+ky1*p
        x2,y2=x2c+kx2*p,y2c+ky2*p
        f1=y1*y1-x1*x1*x1; f2=y2*y2-x2*x2*x2
        A=Fraction(f1-f2,x1-x2); B=Fraction(f1)-A*x1
    if 4*A**3+27*B**2==0: raise ValueError('singular_curve')
    if (mod(A,p),mod(B,p))!=(p-1,p-2): raise ValueError('wrong_coefficient_reduction')
    if (x1%p,y1%p)!=tuple(U) or (x2%p,y2%p)!=tuple(V):
        raise ValueError('wrong_point_reduction')
    score=max(bits(z) for z in (A,B,x1,y1,x2,y2))
    return A,B,x1,y1,x2,y2,score

def packed(path,rows):
    raw=(''.join(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n' for r in rows)).encode()
    blob=gzip.compress(raw,compresslevel=9,mtime=0)
    (H/path).write_bytes(blob)
    return {'path':path,'rows':len(rows),'raw_sha256':hashlib.sha256(raw).hexdigest(),
            'gzip_sha256':hashlib.sha256(blob).hexdigest(),'gzip_bytes':len(blob)}

query_rows=[]; vector_rows=[]; candidate_chunks=[[] for _ in range(32)]
counts={k:0 for k in ('queries','distinct_x_queries','equal_x_queries','candidate_attempts',
 'candidate_pass','candidate_failure','public_vector_attempts','public_hits','rational_hits',
 'rational_control_pass','chosen_curves')}
for spec in P['fields']:
    p,q,N=spec['p'],spec['q'],spec['order']
    E=EllipticCurve(GF(p),P['curve_coefficients'])
    assert int(E.cardinality())==N
    G=generator(E,p,q,N)
    for j in range(4):
        w=1+int.from_bytes(hashlib.sha256(f'xedni-height-selected-v1|{p}|{j}'.encode()).digest(),'big')%(q-1)
        Q=w*G
        queries=[]
        for t1,t2 in itertools.permutations(P['offsets'],2):
            U=Q-t1*G; V=Q-t2*G
            if not U.is_zero() and not V.is_zero(): queries.append((t1,t2,U,V))
            if len(queries)==16: break
        assert len(queries)==16
        for qi,(t1,t2,U,V) in enumerate(queries):
            event_index=len(query_rows)
            u,v=coords(U),coords(V)
            equal=u[0]==v[0]
            counts['equal_x_queries' if equal else 'distinct_x_queries']+=1
            shifts=[None] if equal else itertools.product((-1,0,1),repeat=4)
            winner=None
            for shift in shifts:
                rec={'event_index':event_index,'p':p,'target_index':j,'query_index':qi,
                     'shift':None if shift is None else list(shift)}
                counts['candidate_attempts']+=1
                try:
                    A,B,x1,y1,x2,y2,score=candidate(p,u,v,shift)
                    rec.update({'status':'pass','A':str(A),'B':str(B),'score_bits':score})
                    counts['candidate_pass']+=1
                    tie=() if shift is None else tuple(shift)
                    key=(score,tie)
                    if winner is None or key<winner[0]: winner=(key,rec,(A,B,x1,y1,x2,y2))
                except Exception as exc:
                    rec.update({'status':'failure','error':f'{type(exc).__name__}: {exc}',
                                'score_bits':None})
                    counts['candidate_failure']+=1
                candidate_chunks[event_index//16].append(rec)
            qr={'event_index':event_index,'p':p,'q':q,'order':N,'G':coords(G),
                'target_index':j,'w':w,'query_index':qi,'t1':t1,'t2':t2,'U':u,'V':v,
                'branch':'equal_x_opposite' if equal else 'distinct_x'}
            if winner is None:
                qr.update({'status':'no_valid_candidate'})
                query_rows.append(qr)
                for vi,(a,b) in enumerate(P['vectors']):
                    pub=(a*U+b*V).is_zero()
                    assert pub==((a*(w-t1)+b*(w-t2))%q==0)
                    vector_rows.append({'event_index':event_index,'vector_index':vi,'a':a,'b':b,
                                        'public_relation':pub,'status':'no_valid_candidate','rational_relation':None})
                    counts['public_vector_attempts']+=1; counts['public_hits']+=int(pub)
                continue
            chosen=winner[1]; A,B,x1,y1,x2,y2=winner[2]
            C=EllipticCurve(QQ,[QQ(A.numerator)/QQ(A.denominator),QQ(B.numerator)/QQ(B.denominator)])
            P1=C(QQ(x1),QQ(y1)); P2=C(QQ(x2),QQ(y2))
            assert [mod(P1[0],p),mod(P1[1],p)]==u
            assert [mod(P2[0],p),mod(P2[1],p)]==v
            assert (P1+(-P1)).is_zero()
            assert [mod((-P1)[0],p),mod((-P1)[1],p)]==coords(-U)
            counts['rational_control_pass']+=1
            counts['chosen_curves']+=1
            qr.update({'status':'pass','chosen_shift':chosen['shift'],'A':str(A),'B':str(B),
                       'score_bits':chosen['score_bits'],'candidate_count':81 if not equal else 1})
            query_rows.append(qr)
            for vi,(a,b) in enumerate(P['vectors']):
                pub=(a*U+b*V).is_zero()
                assert pub==((a*(w-t1)+b*(w-t2))%q==0)
                rel=(a*P1+b*P2).is_zero()
                assert not rel or pub
                vector_rows.append({'event_index':event_index,'vector_index':vi,'a':a,'b':b,
                                    'public_relation':pub,'status':'tested','rational_relation':rel})
                counts['public_vector_attempts']+=1; counts['public_hits']+=int(pub)
                counts['rational_hits']+=int(rel)
            counts['queries']+=1
            if time.monotonic()-START>P['run_cap_seconds']:
                raise TimeoutError('frozen run cap exceeded')
assert len(query_rows)==512 and len(vector_rows)==6656
assert counts['candidate_attempts']==81*counts['distinct_x_queries']+counts['equal_x_queries']
parts=[packed(f'candidates.part{i:02d}.jsonl.gz',rows) for i,rows in enumerate(candidate_chunks)]
query_file=packed('queries.jsonl.gz',query_rows)
vector_file=packed('vectors.jsonl.gz',vector_rows)
result={'schema':'xedni-height-selected-two-image-result-v1','status':'complete',
        'counts':counts,'elapsed_wall_seconds':time.monotonic()-START,
        'protocol_sha256':hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest(),
        'candidate_parts':parts,'queries':query_file,'vectors':vector_file}
(H/'run-result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True,indent=2))
