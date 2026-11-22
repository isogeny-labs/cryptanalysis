"""Auxiliary-prime independence census for every fresh-panel final beam state."""
from sage.all import EllipticCurve, GF, QQ, is_prime
from pathlib import Path
import gzip, hashlib, json, math, time

H=Path(__file__).resolve().parent
P=json.loads((H/'protocol.json').read_text())
SOURCE=H.parent/'xedni-hensel-fresh-transfer-20261118'/'run-result.json.gz'
blob=SOURCE.read_bytes()
assert hashlib.sha256(blob).hexdigest()==P['fresh_result_gzip_sha256']
B=json.loads(gzip.decompress(blob))
assert B['schema']=='xedni-hensel-fresh-transfer-result-v1'
assert len(B['results'])==13 and all(x['status']=='measured' for x in B['results'])
start=time.monotonic()

def q(meta): return QQ(int(meta['num']))/QQ(int(meta['den']))
def unit(z,ell): return math.gcd(int(z.denominator()),ell)==1
def red(z,ell): return int(z.numerator())*pow(int(z.denominator()),-1,ell)%ell
def point(T): return None if T.is_zero() else [int(T[0]),int(T[1])]

primes=[ell for ell in range(3,200,2) if is_prime(ell)]
rows=[]; summaries=[]
for hit_index,hit_row in enumerate(B['results']):
    hit=hit_row['hit']; p=hit['p']; a,b=hit['a'],hit['b']
    states=hit_row['beam']['stages'][-1]['beam']
    assert len(states)==8 and hit_row['beam']['status']=='depth_cap'
    for state in states:
        state_id=f'hit{hit_index:02d}:{state["id"]}'
        Edata=state['exact']; A=q(Edata['A']); Bb=q(Edata['B'])
        Pcoords=[q(z) for z in Edata['P1']]
        Qcoords=[q(z) for z in Edata['P2']]
        E=EllipticCurve(QQ,[A,Bb]); P1=E(*Pcoords); P2=E(*Qcoords)
        residual=a*P1+b*P2
        assert not residual.is_zero() and Edata['depth']>=8
        assert [str(residual[0]),str(residual[1])]==[
            str(q(Edata['R'][0])),str(q(Edata['R'][1]))]
        assert all(unit(z,p) for z in (A,Bb,*Pcoords,*Qcoords))
        assert (red(A,p),red(Bb,p))==(p-1,p-2)
        assert [red(z,p) for z in Pcoords]==hit['U']
        assert [red(z,p) for z in Qcoords]==hit['V']
        disc=E.discriminant()
        odd=None; independent=None; good_count=0; point_count=0
        for ell in primes:
            row={'state_id':state_id,'ell':ell}
            if time.monotonic()-start>P['run_cap_seconds']:
                row['status']='not_run_cap'; rows.append(row); continue
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
                qualifies=(p1 not in doubles and p2 not in doubles and p1-p2 not in doubles)
                row.update({'status':'good_points','P1':point(p1),'P2':point(p2),
                            'double_image_size':len(doubles),
                            'quotient_independent':bool(qualifies)})
                if qualifies and independent is None: independent=ell
            else:
                row['status']='point_denominator_nonunit'
            rows.append(row)
        summaries.append({'state_id':state_id,'hit_index':hit_index,
                          'beam_state_id':state['id'],'p':p,'model_bits':Edata['model_bits'],
                          'residual_depth':Edata['depth'],'odd_order_witness':odd,
                          'quotient_witness':independent,'good_curve_primes':good_count,
                          'good_point_primes':point_count,
                          'status':'certified_independent' if odd is not None and independent is not None
                          else 'uncertified_in_prime_cap'})
assert len(summaries)==104 and len(rows)==104*len(primes)
raw=json.dumps(rows,sort_keys=True,separators=(',',':')).encode()
compressed=gzip.compress(raw,compresslevel=9,mtime=0)
(H/'rows.json.gz').write_bytes(compressed)
result={'schema':'xedni-fresh-beam-independence-result-v1',
        'status':'complete' if all(r['status']!='not_run_cap' for r in rows) else 'capped',
        'protocol_sha256':hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest(),
        'source_gzip_sha256':P['fresh_result_gzip_sha256'],
        'primes':primes,'state_count':len(summaries),'rows':len(rows),
        'rows_raw_sha256':hashlib.sha256(raw).hexdigest(),
        'rows_gzip_sha256':hashlib.sha256(compressed).hexdigest(),
        'rows_gzip_bytes':len(compressed),
        'certified_count':sum(x['status']=='certified_independent' for x in summaries),
        'summaries':summaries,'elapsed_wall_seconds':time.monotonic()-start}
(H/'run-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'state_count':len(summaries),
                  'rows':len(rows),'certified_count':result['certified_count'],
                  'uncertified':[x['state_id'] for x in summaries
                                 if x['status']!='certified_independent'],
                  'elapsed_wall_seconds':result['elapsed_wall_seconds']},indent=2))
