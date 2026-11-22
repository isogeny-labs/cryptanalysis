"""Fresh public panel with precommitted five-shift rational lift selection."""
from fractions import Fraction
from pathlib import Path
import gzip, hashlib, itertools, json, time

H=Path(__file__).resolve().parent
ROOT=H.parent
P=json.loads((H/'protocol.json').read_text())
assert hashlib.sha256((ROOT/'xedni-large-order-admission-20261115'/'result.json').read_bytes()).hexdigest()==P['field_registry_sha256']
assert hashlib.sha256((ROOT/'xedni-large-order-height-admission-20261116'/'protocol.json').read_bytes()).hexdigest()==P['vector_family_sha256']
started=time.monotonic()

def add(P,Q,a,m=None):
    if P is None: return Q
    if Q is None: return P
    x,y=P; u,v=Q
    if m is not None:
        if x==u and (y+v)%m==0: return None
        s=((3*x*x+a)*pow(2*y,-1,m))%m if P==Q else ((v-y)*pow(u-x,-1,m))%m
        X=(s*s-x-u)%m
        return X,(s*(x-X)-y)%m
    if x==u and y+v==0: return None
    s=(3*x*x+a)/(2*y) if P==Q else (v-y)/(u-x)
    X=s*s-x-u
    return X,s*(x-X)-y

def mul(n,P,a,m=None):
    if n<0: P=(P[0],(-P[1])%m if m is not None else -P[1]); n=-n
    R=None
    while n:
        if n&1: R=add(R,P,a,m)
        P=add(P,P,a,m); n//=2
    return R

def generator(p,q,N):
    squares={}
    for y in range(p): squares.setdefault(y*y%p,[]).append(y)
    for x in range(p):
        for y in squares.get((x*x*x-x-2)%p,[]):
            G=mul(N//q,(x,y),-1,p)
            if G is not None and mul(q,G,-1,p) is None: return G
    raise ValueError('generator_missing')

def cent(z,p): return z-p if z>p//2 else z

def residue(z,p):
    assert z.denominator%p
    return z.numerator*pow(z.denominator,-1,p)%p

def candidate(p,U,V,shift):
    x1,y1=map(lambda z:cent(z,p),U)
    x2,y2=map(lambda z:cent(z,p),V)
    if shift is None:
        assert U[0]==V[0] and (U[1]+V[1])%p==0
        x2,y2=x1,-y1
        A=Fraction(-1); B=Fraction(y1*y1-x1*x1*x1+x1)
    else:
        x1+=p*shift[0]; y1+=p*shift[1]; x2+=p*shift[2]; y2+=p*shift[3]
        f1=y1*y1-x1*x1*x1; f2=y2*y2-x2*x2*x2
        A=Fraction(f1-f2,x1-x2); B=Fraction(f1)-A*x1
    assert 4*A**3+27*B**2!=0
    assert (residue(A,p),residue(B,p))==(p-1,p-2)
    assert (x1%p,y1%p)==tuple(U) and (x2%p,y2%p)==tuple(V)
    score=max(max(abs(z.numerator).bit_length(),z.denominator.bit_length()) for z in (A,B,Fraction(x1),Fraction(y1),Fraction(x2),Fraction(y2)))
    return A,B,(Fraction(x1),Fraction(y1)),(Fraction(x2),Fraction(y2)),score

def pack(path,rows):
    raw=(''.join(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n' for x in rows)).encode()
    blob=gzip.compress(raw,compresslevel=9,mtime=0)
    (H/path).write_bytes(blob)
    return {'path':path,'rows':len(rows),'gzip_bytes':len(blob),'gzip_sha256':hashlib.sha256(blob).hexdigest(),'raw_sha256':hashlib.sha256(raw).hexdigest()}

queries=[]; vectors=[]; hit_candidates=[]; parts=[]; chunk=[]
counts={k:0 for k in ('query_attempts','distinct_x','equal_x','candidate_attempts','candidate_pass','candidate_failure','selected_pass','vector_tests','public_hits','selected_rational_hits','hit_candidate_tests','hit_candidate_relations','hit_candidate_failures')}
for spec in P['fields']:
    p,q,N=spec['p'],spec['q'],spec['order']
    G=generator(p,q,N)
    for j in range(4):
        w=1+int.from_bytes(hashlib.sha256(f'xedni-wide-grid-v1|{p}|{j}'.encode()).digest(),'big')%(q-1)
        Q=mul(w,G,-1,p)
        pairs=[]
        for t1,t2 in itertools.permutations(P['offsets'],2):
            U=add(Q,mul(-t1,G,-1,p),-1,p)
            V=add(Q,mul(-t2,G,-1,p),-1,p)
            if U is not None and V is not None: pairs.append((t1,t2,U,V))
            if len(pairs)==16: break
        assert len(pairs)==16
        for qi,(t1,t2,U,V) in enumerate(pairs):
            event=len(queries); equal=U[0]==V[0]
            counts['query_attempts']+=1; counts['equal_x' if equal else 'distinct_x']+=1
            shifts=[None] if equal else itertools.product(range(-2,3),repeat=4)
            passed=[]; winner=None
            for shift in shifts:
                row={'event_index':event,'shift':None if shift is None else list(shift)}
                counts['candidate_attempts']+=1
                try:
                    A,B,P1,P2,score=candidate(p,U,V,shift)
                    row.update({'status':'pass','A':str(A),'B':str(B),'score_bits':score})
                    counts['candidate_pass']+=1
                    passed.append((row,A,P1,P2))
                    key=(score,() if shift is None else shift)
                    if winner is None or key<winner[0]: winner=(key,row,A,P1,P2)
                except (AssertionError, ArithmeticError, ValueError, TypeError, ZeroDivisionError) as exc:
                    row.update({'status':'failure','error':type(exc).__name__+': '+str(exc),'score_bits':None})
                    counts['candidate_failure']+=1
                chunk.append(row)
            qr={'event_index':event,'p':p,'q':q,'order':N,'G':list(G),'target_index':j,'w':w,'query_index':qi,'t1':t1,'t2':t2,'U':list(U),'V':list(V),'branch':'equal_x_opposite' if equal else 'distinct_x','candidate_count':len(chunk) if event%16==0 else (1 if equal else 625)}
            # The chosen candidate is committed before the vector loop.
            if winner is None:
                qr['status']='no_valid_candidate'
            else:
                _,selected,A,P1,P2=winner
                qr.update({'status':'pass','chosen_shift':selected['shift'],'A':str(A),'B':str(selected['B']),'score_bits':selected['score_bits']})
                counts['selected_pass']+=1
            queries.append(qr)
            for vi,(a,b) in enumerate(P['vectors']):
                pub=(a*(w-t1)+b*(w-t2))%q==0
                assert pub==(add(mul(a,U,-1,p),mul(b,V,-1,p),-1,p) is None)
                row={'event_index':event,'vector_index':vi,'a':a,'b':b,'public_relation':pub}
                counts['vector_tests']+=1; counts['public_hits']+=int(pub)
                if winner is None: row.update({'status':'no_valid_candidate','selected_rational_relation':None})
                else:
                    rel=add(mul(a,P1,A),mul(b,P2,A),A) is None
                    assert not rel or pub
                    row.update({'status':'tested','selected_rational_relation':rel})
                    counts['selected_rational_hits']+=int(rel)
                vectors.append(row)
                if pub:
                    for cand,C,U1,V1 in passed:
                        status='relation' if add(mul(a,U1,C),mul(b,V1,C),C) is None else 'nonidentity'
                        hit_candidates.append({'event_index':event,'vector_index':vi,'shift':cand['shift'],'status':status})
                        counts['hit_candidate_tests']+=1; counts['hit_candidate_relations']+=int(status=='relation')
                    counts['hit_candidate_failures']+=(1 if equal else 625)-len(passed)
            if (event+1)%16==0:
                parts.append(pack(f'candidates.part{event//16:02d}.jsonl.gz',chunk)); chunk=[]
            if time.monotonic()-started>P['resource_cap_seconds']: raise TimeoutError('frozen run cap exceeded')
assert not chunk and len(queries)==P['expected_queries'] and len(vectors)==P['expected_vector_tests']
assert counts['candidate_attempts']==625*counts['distinct_x']+counts['equal_x']
files={'queries':pack('queries.jsonl.gz',queries),'vectors':pack('vectors.jsonl.gz',vectors),'hit_candidates':pack('hit-candidates.jsonl.gz',hit_candidates),'candidate_parts':parts}
result={'schema':'xedni-fresh-wide-grid-result-v1','status':'complete','protocol_sha256':hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest(),'counts':counts,'files':files,'elapsed_wall_seconds':round(time.monotonic()-started,3)}
(H/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'counts':counts,'elapsed_wall_seconds':result['elapsed_wall_seconds']},sort_keys=True,indent=2))
