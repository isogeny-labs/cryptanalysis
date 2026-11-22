"""Frozen auxiliary reduction census for all eight final Hensel beam states."""
from sage.all import EllipticCurve, GF, QQ, is_prime
from pathlib import Path
import hashlib, json, math, time

H=Path(__file__).resolve().parent
P=json.loads((H/'protocol.json').read_text())
BH=H.parent/'xedni-height-beam-20261118'
B=json.loads((BH/'run-result.json').read_text())
BN={k:v for k,v in B.items() if k!='elapsed_wall_seconds'}
assert hashlib.sha256(json.dumps(BN,sort_keys=True).encode()).hexdigest()==P['beam_result_normalized_sha256']
assert B['status']=='depth_cap' and B['stages'][-1]['depth']==8
states=B['stages'][-1]['beam']
assert len(states)==8
start=time.monotonic()

def q(meta): return QQ(int(meta['num']))/QQ(int(meta['den']))
def point(T): return None if T.is_zero() else [int(T[0]),int(T[1])]
def unit(z,ell): return math.gcd(int(z.denominator()),ell)==1

rows=[]; summaries=[]
primes=[ell for ell in range(3,200,2) if is_prime(ell)]
for state in states:
    Edata=state['exact']; A=q(Edata['A']); Bb=q(Edata['B'])
    Pcoords=[q(z) for z in Edata['P1']]
    Qcoords=[q(z) for z in Edata['P2']]
    E=EllipticCurve(QQ,[A,Bb])
    P1=E(*Pcoords); P2=E(*Qcoords)
    residual=5*P1+4*P2
    assert not residual.is_zero() and Edata['depth']>=8
    assert [str(residual[0]),str(residual[1])]==[
        str(q(Edata['R'][0])),str(q(Edata['R'][1]))]
    disc=E.discriminant()
    odd=None; independent=None; good_count=0; point_count=0
    for ell in primes:
        row={'state_id':state['id'],'ell':ell}
        if not unit(A,ell) or not unit(Bb,ell) or not unit(disc,ell) or GF(ell)(disc)==0:
            row['status']='bad_model_reduction'; rows.append(row); continue
        F=GF(ell); Eell=EllipticCurve(F,[F(A),F(Bb)])
        order=int(Eell.cardinality()); good_count+=1
        row.update({'curve_order':order,'status':'good_curve'})
        if order%2==1 and odd is None: odd=ell
        if all(unit(z,ell) for z in (*Pcoords,*Qcoords)):
            p1=Eell(F(Pcoords[0]),F(Pcoords[1]))
            p2=Eell(F(Qcoords[0]),F(Qcoords[1]))
            point_count+=1
            doubles={2*T for T in Eell.points()}
            quotient_independent=(p1 not in doubles and p2 not in doubles
                                  and p1-p2 not in doubles)
            row.update({'status':'good_points','P1':point(p1),'P2':point(p2),
                        'double_image_size':len(doubles),
                        'quotient_independent':bool(quotient_independent)})
            if quotient_independent and independent is None: independent=ell
        else:
            row['status']='point_denominator_nonunit'
        rows.append(row)
    summaries.append({'state_id':state['id'],'model_bits':Edata['model_bits'],
                      'residual_depth':Edata['depth'],'odd_order_witness':odd,
                      'quotient_witness':independent,'good_curve_primes':good_count,
                      'good_point_primes':point_count,
                      'status':'certified_independent' if odd is not None and independent is not None
                      else 'uncertified_in_prime_cap'})
    if time.monotonic()-start>P['run_cap_seconds']: raise TimeoutError('run_cap_seconds')
assert len(rows)==len(states)*len(primes)
(H/'rows.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
result={'schema':'xedni-beam-auxiliary-independence-result-v1',
        'protocol_sha256':hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest(),
        'beam_result_normalized_sha256':P['beam_result_normalized_sha256'],
        'primes':primes,'state_count':len(states),'rows':len(rows),
        'certified_count':sum(x['status']=='certified_independent' for x in summaries),
        'summaries':summaries,'elapsed_wall_seconds':time.monotonic()-start}
(H/'run-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'state_count':len(states),'rows':len(rows),
                  'certified_count':result['certified_count'],
                  'witnesses':[(x['state_id'],x['odd_order_witness'],x['quotient_witness'])
                               for x in summaries],
                  'elapsed_wall_seconds':result['elapsed_wall_seconds']},indent=2))
