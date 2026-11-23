"""Versioned adaptive prime extension for four uncategorized beam states."""
from sage.all import EllipticCurve, GF, QQ, is_prime
from pathlib import Path
import gzip, hashlib, json, math, time

H=Path(__file__).resolve().parent
P=json.loads((H/'extension-protocol.json').read_text())
assert hashlib.sha256((H/'run-result.json').read_bytes()).hexdigest()==P['parent_result_sha256']
assert hashlib.sha256((H/'rows.json.gz').read_bytes()).hexdigest()==P['parent_rows_gzip_sha256']
parent=json.loads((H/'run-result.json').read_text())
assert [s['state_id'] for s in parent['summaries'] if s['status']!='certified_independent']==P['states']
fresh=json.loads(gzip.decompress((H.parent/'xedni-hensel-fresh-transfer-20261118'/'run-result.json.gz').read_bytes()))
start=time.monotonic()

def q(meta): return QQ(int(meta['num']))/QQ(int(meta['den']))
def unit(z,ell): return math.gcd(int(z.denominator()),ell)==1
def point(T): return None if T.is_zero() else [int(T[0]),int(T[1])]

primes=[ell for ell in range(211,998) if is_prime(ell)]
rows=[]; summaries=[]
for state_id in P['states']:
    h,beam_id=state_id.split(':',1)
    hit_index=int(h[3:]); hit_row=fresh['results'][hit_index]
    state=next(s for s in hit_row['beam']['stages'][-1]['beam'] if s['id']==beam_id)
    e=state['exact']; A=q(e['A']); Bb=q(e['B'])
    coords1=[q(z) for z in e['P1']]; coords2=[q(z) for z in e['P2']]
    E=EllipticCurve(QQ,[A,Bb]); P1=E(*coords1); P2=E(*coords2)
    assert not (hit_row['hit']['a']*P1+hit_row['hit']['b']*P2).is_zero()
    disc=E.discriminant(); first=None; good=0; good_points=0
    for ell in primes:
        row={'state_id':state_id,'ell':ell}
        if time.monotonic()-start>P['run_cap_seconds']:
            row['status']='not_run_cap'; rows.append(row); continue
        if not unit(A,ell) or not unit(Bb,ell) or not unit(disc,ell) or GF(ell)(disc)==0:
            row['status']='bad_model_reduction'; rows.append(row); continue
        F=GF(ell); Eell=EllipticCurve(F,[F(A),F(Bb)])
        order=int(Eell.cardinality()); good+=1
        row.update({'curve_order':order,'status':'good_curve'})
        if all(unit(z,ell) for z in (*coords1,*coords2)):
            p1=Eell(F(coords1[0]),F(coords1[1]))
            p2=Eell(F(coords2[0]),F(coords2[1]))
            doubles={2*T for T in Eell.points()}
            qualifies=(p1 not in doubles and p2 not in doubles and p1-p2 not in doubles)
            row.update({'status':'good_points','P1':point(p1),'P2':point(p2),
                        'double_image_size':len(doubles),
                        'quotient_independent':bool(qualifies)})
            good_points+=1
            if qualifies and first is None: first=ell
        else:
            row['status']='point_denominator_nonunit'
        rows.append(row)
    summaries.append({'state_id':state_id,'first_extension_quotient_witness':first,
                      'good_curve_primes':good,'good_point_primes':good_points,
                      'status':'certified_with_extension' if first is not None
                               else 'uncertified_through_997'})
assert len(rows)==len(P['states'])*len(primes)
raw=json.dumps(rows,sort_keys=True,separators=(',',':')).encode()
blob=gzip.compress(raw,compresslevel=9,mtime=0)
(H/'extension-rows.json.gz').write_bytes(blob)
result={'schema':'xedni-fresh-beam-independence-extension-result-v1',
        'status':'complete' if all(r['status']!='not_run_cap' for r in rows) else 'capped',
        'protocol_sha256':hashlib.sha256((H/'extension-protocol.json').read_bytes()).hexdigest(),
        'parent_result_sha256':P['parent_result_sha256'],
        'primes':primes,'rows':len(rows),'states':len(summaries),
        'rows_raw_sha256':hashlib.sha256(raw).hexdigest(),
        'rows_gzip_sha256':hashlib.sha256(blob).hexdigest(),
        'rows_gzip_bytes':len(blob),
        'summaries':summaries,'elapsed_wall_seconds':time.monotonic()-start}
(H/'extension-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'rows':len(rows),
                  'witnesses':[(s['state_id'],s['first_extension_quotient_witness']) for s in summaries],
                  'elapsed_wall_seconds':result['elapsed_wall_seconds']},indent=2))
