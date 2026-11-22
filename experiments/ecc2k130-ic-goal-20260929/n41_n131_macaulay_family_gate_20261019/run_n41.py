"""Frozen N41 two-pair whole-second-code Macaulay rejection panel."""
import hashlib,json,resource,time
from pathlib import Path
from macaulay import Field,source_basis,source_value,coefficients,evaluate_boolean,evaluate_resultant,certificate
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((HERE/'n41_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_N41_PANEL'
for label,item in cfg['sources'].items():assert sha(item['path'])==item['sha256'],label
lines=Path(cfg['sources']['resultant_input']['path']).read_text().splitlines()
assert lines[0]=='FREECODE 25 281 13'
valid={}
for line in lines[1:282]:
    tag,code,p,q=line.split();assert tag=='P'
    valid[int(code)]=(int(p),int(q))
assert len(valid)==281
terms={0:{},1:{}}
points={}
for line in lines[282:]:
    parts=line.split()
    if parts[0]=='T':
        idx=int(parts[1])
        if idx in terms:points[idx]=list(map(int,parts[2:]))
    elif parts[0]=='C':
        idx=int(parts[1])
        if idx in terms:terms[idx][int(parts[2]),int(parts[3])]=int(parts[4])
assert len(terms[0])==len(terms[1])==13
field=Field(41,(1<<3)|1)
seed=112;bits=[0,1,2,3,4,6,7,8,9,10]
pbasis=source_basis(field,seed,bits,12)
qbasis=source_basis(field,seed,bits,24)
for code,(p,q) in valid.items():
    assert source_value(code,pbasis)==p
    assert source_value(code,qbasis)==q
rows=[];start=time.monotonic();status='COMPLETE_N41_FAMILY_PANEL'
for target_index in cfg['target_indexes']:
    for code in cfg['p_codes']:
        if time.monotonic()-start>=cfg['wall_cap_seconds']:
            status='WALL_CAP_PARTIAL_PANEL';break
        p=valid[code][0];t0=time.monotonic()
        mons,values=coefficients(field,terms[target_index],p,qbasis)
        for qcode in cfg['expansion_check_qcodes']:
            q=source_value(qcode,qbasis)
            assert evaluate_boolean(mons,values,qcode)==evaluate_resultant(field,terms[target_index],p,q)
        built=time.monotonic()
        cert=certificate(41,len(bits),mons,values)
        tested=time.monotonic()
        valid_hits=[qcode for qcode in sorted(valid) if evaluate_boolean(mons,values,qcode)==0]
        if cert['reject']:assert valid_hits==[]
        if target_index==0 and code==253:assert 63 in valid_hits and not cert['reject']
        row={'target_index':target_index,'p_code':code,'p_product':p,'positive_q_code':63 if target_index==0 and code==253 else None,
             'valid_q_hits':valid_hits,'rank':cert['rank'],'monomials':cert['monomials'],
             'equations':cert['equations'],'reject':cert['reject'],
             'certificate_rows':cert['certificate_rows'],
             'coefficients_seconds':built-t0,'linearization_seconds':tested-built,
             'valid_scan_seconds':time.monotonic()-tested}
        rows.append(row)
        print(json.dumps({k:row[k] for k in ('target_index','p_code','rank','reject','valid_q_hits','linearization_seconds')},sort_keys=True),flush=True)
    if status!='COMPLETE_N41_FAMILY_PANEL':break
result={'status':status,'candidate_id':None,'curve_id':cfg['curve_id'],'rows':rows,
        'requested_rows':len(cfg['target_indexes'])*len(cfg['p_codes']),
        'rejected_rows':sum(row['reject'] for row in rows),'exact_valid_miss_rows':sum(not row['valid_q_hits'] for row in rows),
        'wall_seconds':time.monotonic()-start,'peak_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'protocol_sha256':sha(HERE/'n41_protocol.json'),'script_sha256':sha(Path(__file__))}
(HERE/'n41_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:result[k] for k in ('status','requested_rows','rejected_rows','exact_valid_miss_rows','wall_seconds','peak_rss_raw')},sort_keys=True),flush=True)
