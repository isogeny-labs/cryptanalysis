"""Independent finite-group replay of the four-state adaptive extension."""
import audit as base
from fractions import Fraction as F
from pathlib import Path
import gzip, hashlib, json, math

H=Path(__file__).resolve().parent
P=json.loads((H/'extension-protocol.json').read_text())
R=json.loads((H/'extension-result.json').read_text())
parent_bytes=(H/'run-result.json').read_bytes()
assert hashlib.sha256(parent_bytes).hexdigest()==P['parent_result_sha256']==R['parent_result_sha256']
assert hashlib.sha256((H/'rows.json.gz').read_bytes()).hexdigest()==P['parent_rows_gzip_sha256']
assert hashlib.sha256((H/'extension-protocol.json').read_bytes()).hexdigest()==R['protocol_sha256']
parent=json.loads(parent_bytes)
open_ids=[s['state_id'] for s in parent['summaries'] if s['status']!='certified_independent']
assert open_ids==P['states']
blob=(H/'extension-rows.json.gz').read_bytes(); raw=gzip.decompress(blob)
assert len(blob)==R['rows_gzip_bytes']
assert hashlib.sha256(blob).hexdigest()==R['rows_gzip_sha256']
assert hashlib.sha256(raw).hexdigest()==R['rows_raw_sha256']
rows=json.loads(raw)

def points_fast(A,B,ell):
    roots={}
    for y in range(ell): roots.setdefault(y*y%ell,[]).append(y)
    out=[None]
    for x in range(ell):
        for y in roots.get((x*x*x+A*x+B)%ell,[]): out.append((x,y))
    return out

primes=[ell for ell in range(211,998) if base.prime(ell)]
assert R['primes']==primes and len(rows)==len(P['states'])*len(primes)==R['rows']==488
assert R['status']=='complete'
index=0; summaries=[]; statuses={}
for state_id in P['states']:
    hit,beam_id=state_id.split(':',1); hit_index=int(hit[3:])
    parent_summary=next(s for s in parent['summaries'] if s['state_id']==state_id)
    assert parent_summary['odd_order_witness'] is not None
    assert parent_summary['quotient_witness'] is None
    source=base.B['results'][hit_index]
    state=next(s for s in source['beam']['stages'][-1]['beam'] if s['id']==beam_id)
    e=state['exact']; A=base.q(e['A']); B=base.q(e['B'])
    coords1=[base.q(z) for z in e['P1']]
    coords2=[base.q(z) for z in e['P2']]
    disc=-16*(4*A**3+27*B**2)
    assert disc!=0
    first=None; good=0; good_points=0
    for ell in primes:
        row=rows[index]; index+=1
        assert row['state_id']==state_id and row['ell']==ell
        if not base.unit(A,ell) or not base.unit(B,ell) or not base.unit(disc,ell) or base.mod(disc,ell)==0:
            assert row=={'state_id':state_id,'ell':ell,'status':'bad_model_reduction'}
            statuses[row['status']]=statuses.get(row['status'],0)+1
            continue
        a,b=base.mod(A,ell),base.mod(B,ell)
        group=points_fast(a,b,ell); order=len(group); good+=1
        assert row['curve_order']==order
        if all(base.unit(z,ell) for z in (*coords1,*coords2)):
            p1=tuple(base.mod(z,ell) for z in coords1)
            p2=tuple(base.mod(z,ell) for z in coords2)
            assert p1 in group and p2 in group
            doubles={base.add(T,T,a,ell) for T in group}
            difference=base.add(p1,base.neg(p2,ell),a,ell)
            qualifies=(p1 not in doubles and p2 not in doubles and difference not in doubles)
            assert row['status']=='good_points'
            assert row['P1']==list(p1) and row['P2']==list(p2)
            assert row['double_image_size']==len(doubles)
            assert row['quotient_independent']==qualifies
            good_points+=1
            if qualifies and first is None: first=ell
        else:
            assert row['status']=='point_denominator_nonunit'
        statuses[row['status']]=statuses.get(row['status'],0)+1
    summaries.append({'state_id':state_id,'first_extension_quotient_witness':first,
                      'good_curve_primes':good,'good_point_primes':good_points,
                      'status':'certified_with_extension' if first is not None
                               else 'uncertified_through_997'})
assert index==len(rows) and summaries==R['summaries']
assert all(s['status']=='certified_with_extension' for s in summaries)
out={'schema':'xedni-fresh-beam-independence-extension-audit-v1','status':'pass',
     'extension_rows':len(rows),'original_certified':parent['certified_count'],
     'extension_certified':len(summaries),'combined_certified':parent['certified_count']+len(summaries),
     'witnesses':{s['state_id']:s['first_extension_quotient_witness'] for s in summaries},
     'statuses':statuses,'extension_rows_gzip_sha256':R['rows_gzip_sha256']}
(H/'extension-audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
