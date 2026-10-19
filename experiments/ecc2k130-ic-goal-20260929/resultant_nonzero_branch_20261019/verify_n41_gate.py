"""Check the frozen N41 positive/ordinary controls before N131 promotion."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg=json.loads((HERE/'n41_gate_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_N41_GATE'
for name,source in cfg['sources'].items():
    assert sha(source['path'])==source['sha256'],name
rows=[]
for case in ('n41_p_k5','n41_o_k5'):
    result=json.loads((HERE/(case+'_result.json')).read_text())
    receipt=json.loads((HERE/(case+'_receipt.json')).read_text())
    assert receipt['status']=='COMPLETE' and receipt['exit_code']==0
    assert receipt['stop_reason'] is None and receipt['monitor_error'] is None
    assert receipt['sampled_peak_combined_rss_bytes']<4294967296
    assert receipt['rss_samples']>0 and receipt['wall_seconds']<120
    assert receipt['result_sha256']==sha(HERE/(case+'_result.json'))
    assert receipt['stdout_sha256']==sha(HERE/(case+'.stdout'))
    assert receipt['stderr_sha256']==sha(HERE/(case+'.stderr'))
    assert result['protocol_sha256']==sha(HERE/'protocol.json')
    assert result['anf_monomials']==446 and result['source_anf_monomials']==886
    assert result['degree_histogram']=={'0':1,'1':15,'2':105,'3':325}
    assert result['equations']==42 and result['nonzero_branch_products_checked']==16
    rows.append({'case':case,'status':result['status'],'gb_seconds':result['gb_seconds'],
                 'wall_seconds':receipt['wall_seconds'],'peak_rss_bytes':receipt['sampled_peak_combined_rss_bytes']})
assert json.loads((HERE/'n41_p_k5_result.json').read_text())['recovered_codes']=={'first_code':253,'second_code':63}
assert json.loads((HERE/'n41_o_k5_result.json').read_text())['status']=='GB_UNIT_IDEAL'
prior=json.loads(Path(cfg['sources']['prior_relation_replay']['path']).read_text())
assert prior['status']=='PASS_INDEPENDENT_N41_W11_FIVEPAIR_PUBLIC_RELATION'
out={'status':'PASS_N41_NONZERO_BRANCH_CONTROL','candidate_id':None,'protocol_sha256':sha(HERE/'n41_gate_protocol.json'),
     'script_sha256':sha(__file__),'rows':rows}
(HERE/'n41_gate.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True))
