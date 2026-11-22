"""Construct exact rational lifts from each already known public relation."""
from sage.all import EllipticCurve, GF, QQ
from pathlib import Path
import gzip, hashlib, json, math, time

H=Path(__file__).resolve().parent
P=json.loads((H/'protocol.json').read_text())
SOURCE=H.parent/'xedni-hensel-fresh-transfer-20261118'/'run-result.json.gz'
compressed=SOURCE.read_bytes()
assert hashlib.sha256(compressed).hexdigest()==P['fresh_result_gzip_sha256']
parent=json.loads(gzip.decompress(compressed))
assert parent['schema']=='xedni-hensel-fresh-transfer-result-v1'
start=time.monotonic()

def centered(z,p): return z-p if z>p//2 else z
def rat(z):
    z=QQ(z)
    return {'num':str(z.numerator()),'den':str(z.denominator())}
def point(T): return None if T.is_zero() else [rat(T[0]),rat(T[1])]
def red(z,p):
    z=QQ(z); n=int(z.numerator()); d=int(z.denominator())
    if math.gcd(d,p)!=1: raise ValueError('nonunit_point_denominator')
    return n*pow(d,-1,p)%p
def bits(z):
    z=QQ(z)
    return max(abs(int(z.numerator())).bit_length(),int(z.denominator()).bit_length())

rows=[]
for hit_index,hit in enumerate(parent['public_hits']):
    row={'hit_index':hit_index,'hit':hit}
    if hit['status']!='eligible':
        row['status']='excluded_'+hit['status']; rows.append(row); continue
    p,q=hit['p'],hit['q']; a,b=hit['a'],hit['b']
    if not b or math.gcd(b,q)!=1:
        row['status']='noninvertible_b'; rows.append(row); continue
    if time.monotonic()-start>P['run_cap_seconds']:
        row['status']='not_run_cap'; rows.append(row); continue
    try:
        F=GF(p); Epub=EllipticCurve(F,[-1,-2])
        U=Epub(F(hit['U'][0]),F(hit['U'][1]))
        V=Epub(F(hit['V'][0]),F(hit['V'][1]))
        assert q*U==Epub(0) and q*V==Epub(0)
        assert a*U+b*V==Epub(0)
        inv_b=pow(b,-1,q); R=inv_b*U
        assert b*R==U and -a*R==V
        x=centered(int(R[0]),p); y=centered(int(R[1]),p)
        A=-1; B=y*y-x*x*x-A*x
        E=EllipticCurve(QQ,[A,B]); assert E.discriminant()!=0
        assert red(A,p)==p-1 and red(B,p)==p-2
        T=E(QQ(x),QQ(y)); P1=b*T; P2=-a*T
        assert a*P1+b*P2==E(0)
        assert not P1.is_zero() and not P2.is_zero()
        assert [red(P1[0],p),red(P1[1],p)]==hit['U']
        assert [red(P2[0],p),red(P2[1],p)]==hit['V']
        row.update({'status':'exact_relation','inverse_b_mod_q':inv_b,
                    'R': [int(R[0]),int(R[1])],
                    'model':{'A':A,'B':B,'T':[x,y],
                             'discriminant':str(E.discriminant()),
                             'model_bits':max(bits(z) for z in (A,B,x,y))},
                    'P1':point(P1),'P2':point(P2),
                    'lift_coordinate_bits':max(bits(z) for z in (P1[0],P1[1],P2[0],P2[1]))})
    except Exception as exc:
        row.update({'status':'construction_failure','error':f'{type(exc).__name__}: {exc}'})
    rows.append(row)
result={'schema':'xedni-known-relation-lifts-result-v1',
        'status':'complete' if len(rows)==len(parent['public_hits']) else 'incomplete',
        'protocol_sha256':hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest(),
        'source_gzip_sha256':P['fresh_result_gzip_sha256'],
        'rows':rows,'exact_relation_count':sum(r['status']=='exact_relation' for r in rows),
        'elapsed_wall_seconds':time.monotonic()-start}
(H/'run-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'rows':len(rows),
                  'exact_relation_count':result['exact_relation_count'],
                  'statuses':[r['status'] for r in rows],
                  'model_bits':[r['model']['model_bits'] for r in rows if r['status']=='exact_relation'],
                  'lift_coordinate_bits':[r['lift_coordinate_bits'] for r in rows if r['status']=='exact_relation']},indent=2))
