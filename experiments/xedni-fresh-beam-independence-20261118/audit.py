"""Independent Fraction and finite-group replay of all 104 state certificates."""
from fractions import Fraction as F
from pathlib import Path
import gzip, hashlib, json, math

H=Path(__file__).resolve().parent
P=json.loads((H/'protocol.json').read_text())
R=json.loads((H/'run-result.json').read_text())
source=(H.parent/'xedni-hensel-fresh-transfer-20261118'/'run-result.json.gz').read_bytes()
assert hashlib.sha256(source).hexdigest()==P['fresh_result_gzip_sha256']==R['source_gzip_sha256']
B=json.loads(gzip.decompress(source))
compressed=(H/'rows.json.gz').read_bytes(); raw=gzip.decompress(compressed)
assert len(compressed)==R['rows_gzip_bytes']
assert hashlib.sha256(compressed).hexdigest()==R['rows_gzip_sha256']
assert hashlib.sha256(raw).hexdigest()==R['rows_raw_sha256']
rows=json.loads(raw)
assert hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest()==R['protocol_sha256']

def q(meta): return F(int(meta['num']),int(meta['den']))
def mod(z,ell):
    z=F(z); assert math.gcd(z.denominator,ell)==1
    return z.numerator*pow(z.denominator,-1,ell)%ell
def prime(n):
    return n>=2 and all(n%d for d in range(2,math.isqrt(n)+1))
def neg(Pt,ell): return None if Pt is None else (Pt[0],-Pt[1]%ell)
def add(Pt,Qt,A,ell):
    if Pt is None: return Qt
    if Qt is None: return Pt
    x,y=Pt; u,v=Qt
    if x==u and (y+v)%ell==0: return None
    lam=((3*x*x+A)*pow(2*y,-1,ell) if Pt==Qt else
         (v-y)*pow(u-x,-1,ell))%ell
    xx=(lam*lam-x-u)%ell
    return xx,(lam*(x-xx)-y)%ell
def points(A,Bb,ell):
    out=[None]
    for x in range(ell):
        rhs=(x*x*x+A*x+Bb)%ell
        for y in range(ell):
            if y*y%ell==rhs: out.append((x,y))
    return out
def unit(z,ell): return math.gcd(F(z).denominator,ell)==1

primes=[n for n in range(3,200,2) if prime(n)]
assert R['primes']==primes and R['status']=='complete'
states=[]
for hit_index,hit_row in enumerate(B['results']):
    assert hit_row['status']=='measured' and hit_row['beam']['status']=='depth_cap'
    beam=hit_row['beam']['stages'][-1]['beam']; assert len(beam)==8
    for state in beam: states.append((hit_index,hit_row['hit'],state))
assert len(states)==R['state_count']==104
assert len(rows)==len(states)*len(primes)==R['rows']==4680
index=0; summaries=[]; statuses={}
for hit_index,hit,state in states:
    state_id=f'hit{hit_index:02d}:{state["id"]}'
    e=state['exact']; A=q(e['A']); Bb=q(e['B'])
    Pcoords=[q(z) for z in e['P1']]
    Qcoords=[q(z) for z in e['P2']]
    disc=-16*(4*A**3+27*Bb**2)
    assert disc!=0 and e['depth']>=8 and not e['relation']
    assert Pcoords[1]**2==Pcoords[0]**3+A*Pcoords[0]+Bb
    assert Qcoords[1]**2==Qcoords[0]**3+A*Qcoords[0]+Bb
    p=hit['p']
    assert (mod(A,p),mod(Bb,p))==(p-1,p-2)
    assert [mod(z,p) for z in Pcoords]==hit['U']
    assert [mod(z,p) for z in Qcoords]==hit['V']
    odd=None; independent=None; good_count=0; point_count=0
    for ell in primes:
        row=rows[index]; index+=1
        assert row['state_id']==state_id and row['ell']==ell
        if not unit(A,ell) or not unit(Bb,ell) or not unit(disc,ell) or mod(disc,ell)==0:
            assert row=={'state_id':state_id,'ell':ell,'status':'bad_model_reduction'}
            statuses[row['status']]=statuses.get(row['status'],0)+1
            continue
        a,b=mod(A,ell),mod(Bb,ell)
        group=points(a,b,ell); order=len(group); good_count+=1
        assert row['curve_order']==order
        if order%2 and odd is None: odd=ell
        if all(unit(z,ell) for z in (*Pcoords,*Qcoords)):
            p1=tuple(mod(z,ell) for z in Pcoords)
            p2=tuple(mod(z,ell) for z in Qcoords)
            assert p1 in group and p2 in group
            doubles={add(T,T,a,ell) for T in group}
            difference=add(p1,neg(p2,ell),a,ell)
            qualifies=(p1 not in doubles and p2 not in doubles and difference not in doubles)
            assert row['status']=='good_points'
            assert row['P1']==list(p1) and row['P2']==list(p2)
            assert row['double_image_size']==len(doubles)
            assert row['quotient_independent']==qualifies
            point_count+=1
            if qualifies and independent is None: independent=ell
        else:
            assert row['status']=='point_denominator_nonunit'
        statuses[row['status']]=statuses.get(row['status'],0)+1
    summaries.append({'state_id':state_id,'hit_index':hit_index,
        'beam_state_id':state['id'],'p':p,'model_bits':e['model_bits'],
        'residual_depth':e['depth'],'odd_order_witness':odd,
        'quotient_witness':independent,'good_curve_primes':good_count,
        'good_point_primes':point_count,
        'status':'certified_independent' if odd is not None and independent is not None
                 else 'uncertified_in_prime_cap'})
assert index==len(rows) and summaries==R['summaries']
certified=sum(s['status']=='certified_independent' for s in summaries)
assert R['certified_count']==certified
out={'schema':'xedni-fresh-beam-independence-audit-v1','status':'pass',
     'state_count':len(states),'prime_rows':len(rows),'certified_count':certified,
     'uncertified':[s['state_id'] for s in summaries if s['status']!='certified_independent'],
     'statuses':statuses,'rows_gzip_sha256':R['rows_gzip_sha256']}
(H/'audit-result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
