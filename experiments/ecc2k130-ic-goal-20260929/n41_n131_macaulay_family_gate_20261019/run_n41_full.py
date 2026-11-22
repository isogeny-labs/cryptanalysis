"""All valid first-code families over all frozen N41 residual resultants."""
import gzip,hashlib,json,resource,time
from pathlib import Path
from macaulay import Field,source_basis,source_value,coefficients,certificate
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((HERE/'n41_full_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_FULL_N41_CENSUS'
for label,item in cfg['sources'].items():assert sha(item['path'])==item['sha256'],label
lines=Path(cfg['sources']['resultant_input']['path']).read_text().splitlines()
assert lines[0]=='FREECODE 25 281 13'
valid={}
for line in lines[1:282]:
    tag,code,p,q=line.split();assert tag=='P'
    valid[int(code)]=(int(p),int(q))
assert len(valid)==281
terms={i:{} for i in range(25)}
for line in lines[282:]:
    words=line.split()
    if words[0]=='C':terms[int(words[1])][int(words[2]),int(words[3])]=int(words[4])
assert all(len(v)==13 for v in terms.values())
field=Field(41,(1<<3)|1)
bits=[0,1,2,3,4,6,7,8,9,10]
pbasis=source_basis(field,112,bits,12)
qbasis=source_basis(field,112,bits,24)
for code,(p,q) in valid.items():
    assert source_value(code,pbasis)==p
    assert source_value(code,qbasis)==q
start=time.monotonic();status='COMPLETE_FULL_N41_FAMILY_CENSUS';panels=[];total=0
stream=HERE/'n41_full_rows.jsonl.gz'
assert not stream.exists()
with gzip.open(stream,'wt',compresslevel=6) as out:
    for ti in range(25):
        rejected=0;survivors=[]
        for code in sorted(valid):
            if time.monotonic()-start>=cfg['wall_cap_seconds']:
                status='WALL_CAP_PARTIAL_CENSUS';break
            p=valid[code][0]
            mons,values=coefficients(field,terms[ti],p,qbasis)
            cert=certificate(41,len(bits),mons,values)
            out.write(json.dumps([ti,code,cert['rank'],cert['reject'],cert['certificate_rows']],separators=(',',':'))+'\n')
            total+=1
            if cert['reject']:rejected+=1
            else:survivors.append(code)
        panels.append({'target_index':ti,'first_codes_checked':rejected+len(survivors),
                       'rejected_first_code_families':rejected,'unresolved_first_codes':survivors})
        print(json.dumps(panels[-1],sort_keys=True),flush=True)
        if status!='COMPLETE_FULL_N41_FAMILY_CENSUS':break
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>cfg['rss_cap_bytes']:
            status='RSS_CAP_PARTIAL_CENSUS';break
assert status!='COMPLETE_FULL_N41_FAMILY_CENSUS' or total==25*281
result={'status':status,'candidate_id':None,'curve_id':cfg['curve_id'],
        'row_count':total,'requested_row_count':25*281,
        'rejected_row_count':sum(p['rejected_first_code_families'] for p in panels),
        'panels':panels,'rows_gzip_sha256':sha(stream),
        'wall_seconds':time.monotonic()-start,'peak_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'protocol_sha256':sha(HERE/'n41_full_protocol.json'),'runner_sha256':sha(Path(__file__))}
(HERE/'n41_full_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:result[k] for k in ('status','row_count','requested_row_count','rejected_row_count','wall_seconds','peak_rss_raw')},sort_keys=True),flush=True)
