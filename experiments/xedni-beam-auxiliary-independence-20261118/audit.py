"""Pure-Python replay of all auxiliary curve and quotient certificates."""
from fractions import Fraction as F
from pathlib import Path
import hashlib, json, math

H=Path(__file__).resolve().parent
P=json.loads((H/'protocol.json').read_text())
R=json.loads((H/'run-result.json').read_text())
rows=json.loads((H/'rows.json').read_text())
B=json.loads((H.parent/'xedni-height-beam-20261118'/'run-result.json').read_text())
B.pop('elapsed_wall_seconds')
assert hashlib.sha256(json.dumps(B,sort_keys=True).encode()).hexdigest()==P['beam_result_normalized_sha256']
assert hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest()==R['protocol_sha256']
states=B['stages'][-1]['beam']
assert len(states)==R['state_count']==8

def q(meta): return F(int(meta['num']),int(meta['den']))
def mod(z,ell):
    z=F(z)
    assert math.gcd(z.denominator,ell)==1
    return z.numerator*pow(z.denominator,-1,ell)%ell
def prime(n):
    if n<2: return False
    return all(n%d for d in range(2,math.isqrt(n)+1))
def neg(Pt,ell): return None if Pt is None else (Pt[0],-Pt[1]%ell)
def add(Pt,Qt,A,ell):
    if Pt is None: return Qt
    if Qt is None: return Pt
    x,y=Pt; u,v=Qt
    if x==u and (y+v)%ell==0: return None
    if Pt==Qt: lam=(3*x*x+A)*pow(2*y,-1,ell)%ell
    else: lam=(v-y)*pow(u-x,-1,ell)%ell
    X=(lam*lam-x-u)%ell
    return X,(lam*(x-X)-y)%ell
def points(A,Bb,ell):
    out=[None]
    for x in range(ell):
        rhs=(x*x*x+A*x+Bb)%ell
        for y in range(ell):
            if y*y%ell==rhs: out.append((x,y))
    return out
def unit(z,ell): return math.gcd(F(z).denominator,ell)==1

primes=[n for n in range(3,200,2) if prime(n)]
assert R['primes']==primes and len(rows)==len(states)*len(primes)==R['rows']
index=0; summaries=[]; statuses={}
for state in states:
    e=state['exact']; A=q(e['A']); Bb=q(e['B'])
    Pcoords=[q(z) for z in e['P1']]
    Qcoords=[q(z) for z in e['P2']]
    disc=-16*(4*A**3+27*Bb**2)
    assert disc!=0 and e['depth']>=8 and not e['relation']
    assert Pcoords[1]**2==Pcoords[0]**3+A*Pcoords[0]+Bb
    assert Qcoords[1]**2==Qcoords[0]**3+A*Qcoords[0]+Bb
    assert (mod(A,313),mod(Bb,313))==(312,311)
    assert [mod(z,313) for z in Pcoords]==B['selected']['U']
    assert [mod(z,313) for z in Qcoords]==B['selected']['V']
    odd=None; independent=None; good_count=0; point_count=0
    for ell in primes:
        row=rows[index]; index+=1
        assert row['state_id']==state['id'] and row['ell']==ell
        if not unit(A,ell) or not unit(Bb,ell) or not unit(disc,ell) or mod(disc,ell)==0:
            assert row=={'state_id':state['id'],'ell':ell,'status':'bad_model_reduction'}
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
    summary={'state_id':state['id'],'model_bits':e['model_bits'],
             'residual_depth':e['depth'],'odd_order_witness':odd,
             'quotient_witness':independent,'good_curve_primes':good_count,
             'good_point_primes':point_count,
             'status':'certified_independent' if odd is not None and independent is not None
                      else 'uncertified_in_prime_cap'}
    summaries.append(summary)
assert index==len(rows) and summaries==R['summaries']
assert R['certified_count']==sum(s['status']=='certified_independent' for s in summaries)==8
out={'schema':'xedni-beam-auxiliary-independence-audit-v1','status':'pass',
     'state_count':len(states),'prime_rows':len(rows),'certified_count':R['certified_count'],
     'statuses':statuses,'first_witnesses':[
         {'state_id':s['state_id'],'odd_order_prime':s['odd_order_witness'],
          'quotient_prime':s['quotient_witness']} for s in summaries],
     'rows_sha256':hashlib.sha256((H/'rows.json').read_bytes()).hexdigest()}
(H/'audit-result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
