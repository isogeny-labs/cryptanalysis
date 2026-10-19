"""N131 W29 degree-three family certificates on constructed and public rows."""
import hashlib,json,resource,time
from pathlib import Path
from macaulay import Field,source_basis,source_value,coefficients,evaluate_boolean,evaluate_resultant,certificate
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((HERE/'n131_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_N131_PANEL'
for label,item in cfg['sources'].items():assert sha(item['path'])==item['sha256'],label
source=json.loads(Path(cfg['sources']['coefficients']['path']).read_text())
assert source['status']=='PASS_N131_W33_FREECODE_RESULTANT_EXPORT'
assert source['seed_mask']==898618 and source['free_code_bits']==32
terms=[{(i,j):word for i,j,word in row['terms']} for row in source['rows'][:2]]
assert all(len(row)==13 for row in terms)
field=Field(131,(1<<13)|(1<<2)|(1<<1)|1)
mask=898618;bits=[i for i in range(29) if i!=mask.bit_length()-1]
assert len(bits)==28
pbasis=source_basis(field,mask<<1,bits,0)
qbasis=source_basis(field,mask<<1,bits,18)
assert source_value(3,pbasis)==source['positive_source_checks'][0]['unrotated_product']
positive_q=source_value(16722,qbasis)
assert positive_q==source['rows'][0]['positive_pair_products'][1]
rows=[];start=time.monotonic();status='COMPLETE_N131_W29_FAMILY_PANEL'
for target_index in cfg['target_indexes']:
    for pcode in cfg['p_codes']:
        if time.monotonic()-start>=cfg['wall_cap_seconds']:
            status='WALL_CAP_PARTIAL_PANEL';break
        p=source_value(pcode,pbasis);t0=time.monotonic()
        mons,values=coefficients(field,terms[target_index],p,qbasis)
        sample_zeros=[]
        for qcode in cfg['expansion_check_qcodes']:
            q=source_value(qcode,qbasis)
            left=evaluate_boolean(mons,values,qcode)
            right=evaluate_resultant(field,terms[target_index],p,q)
            assert left==right
            if not left:sample_zeros.append(qcode)
        built=time.monotonic()
        cert=certificate(131,len(bits),mons,values)
        finished=time.monotonic()
        if target_index==0 and pcode==3:
            assert 16722 in sample_zeros and not cert['reject']
        if cert['reject']:assert sample_zeros==[]
        row={'target_index':target_index,'p_code':pcode,'p_product':p,
             'sample_zero_q_codes':sample_zeros,'rank':cert['rank'],
             'monomials':cert['monomials'],'equations':cert['equations'],
             'reject':cert['reject'],'certificate_rows':cert['certificate_rows'],
             'coefficients_seconds':built-t0,'linearization_seconds':finished-built}
        rows.append(row)
        print(json.dumps({k:row[k] for k in ('target_index','p_code','rank','reject','sample_zero_q_codes','linearization_seconds')},sort_keys=True),flush=True)
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>cfg['rss_cap_bytes']:
            status='RSS_CAP_PARTIAL_PANEL';break
    if status!='COMPLETE_N131_W29_FAMILY_PANEL':break
result={'status':status,'candidate_id':None,'curve_id':cfg['curve_id'],'rows':rows,
        'requested_rows':len(cfg['target_indexes'])*len(cfg['p_codes']),
        'rejected_rows':sum(row['reject'] for row in rows),
        'wall_seconds':time.monotonic()-start,'peak_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'protocol_sha256':sha(HERE/'n131_protocol.json'),'script_sha256':sha(Path(__file__))}
(HERE/'n131_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:result[k] for k in ('status','requested_rows','rejected_rows','wall_seconds','peak_rss_raw')},sort_keys=True),flush=True)
