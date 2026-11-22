"""Paired N131 public/constructed check of shared cubic elimination."""
import hashlib,json,resource,time
from pathlib import Path
from macaulay import Field,source_basis,source_value
from shared_core import normalize,SharedCubicCore
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((HERE/'shared_core_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_SHARED_CUBIC_PROBE'
for label,item in cfg['sources'].items():assert sha(item['path'])==item['sha256'],label
prior=json.loads((HERE/'n131_result.json').read_text())
source=json.loads(Path(cfg['sources']['coefficients']['path']).read_text())
field=Field(131,(1<<13)|(1<<2)|(1<<1)|1)
seed=898618;bits=[i for i in range(29) if i!=seed.bit_length()-1]
pbasis=source_basis(field,seed<<1,bits,0)
qbasis=source_basis(field,seed<<1,bits,18)
terms=[{(i,j):c for i,j,c in row['terms']} for row in source['rows'][:2]]
start=time.monotonic()
first_p=source_value(3,pbasis)
mons,normalized,leading=normalize(field,terms[0],first_p,qbasis)
core=SharedCubicCore(131,len(bits),mons,normalized)
prepared=time.monotonic()
rows=[];status='COMPLETE_SHARED_CUBIC_PANEL'
for previous in prior['rows']:
    if time.monotonic()-start>=cfg['wall_cap_seconds']:
        status='WALL_CAP_PARTIAL_PANEL';break
    p=source_value(previous['p_code'],pbasis)
    t0=time.monotonic()
    mons2,norm,lead=normalize(field,terms[previous['target_index']],p,qbasis)
    assert mons2==mons
    normalized_at=time.monotonic()
    check=core.check(norm)
    finished=time.monotonic()
    assert check['rank']==previous['rank']
    assert check['reject']==previous['reject']
    row={'target_index':previous['target_index'],'p_code':previous['p_code'],
         'leading_coefficient':lead,'normalization_seconds':normalized_at-t0,
         'shared_elimination_seconds':finished-normalized_at,
         'original_linearization_seconds':previous['linearization_seconds'],**check}
    rows.append(row)
    print(json.dumps({k:row[k] for k in ('target_index','p_code','rank','reject','normalization_seconds','shared_elimination_seconds')},sort_keys=True),flush=True)
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>cfg['rss_cap_bytes']:
        status='RSS_CAP_PARTIAL_PANEL';break
result={'status':status,'candidate_id':None,'rows':rows,'requested_rows':len(prior['rows']),
        'precompute_seconds':prepared-start,'high_rank':core.high_rank,
        'high_nullity':len(core.nullcombs),'wall_seconds':time.monotonic()-start,
        'peak_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'protocol_sha256':sha(HERE/'shared_core_protocol.json'),'script_sha256':sha(Path(__file__))}
(HERE/'shared_core_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:result[k] for k in ('status','precompute_seconds','high_rank','high_nullity','wall_seconds','peak_rss_raw')},sort_keys=True),flush=True)
