"""Freeze the unpinned N41 correctness gate before N131 promotion."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((H/'n41_gate_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_PREFIX_SUFFIX_X_N41_GATE'
for label,s in cfg['sources'].items():assert sha(s['path'])==s['sha256'],label
p=json.loads((H/'n41_protocol.json').read_text());r=json.loads((H/'n41_result.json').read_text())
c=json.loads((H/'n41_receipt.json').read_text())
prior=json.loads(Path(cfg['sources']['prior_relation_result']['path']).read_text())
assert p['status']=='FROZEN_BEFORE_PREFIX_SUFFIX_X_N41'
for label,s in p['sources'].items():assert sha(s['path'])==s['sha256'],label
assert r['status']=='COMPLETE_PREFIX_SUFFIX_X' and r['boxes_completed']==9
assert r['verified_hits']==1 and r['rows'][0]['verified_hits']==[[0,1,1,1,1]]
assert all(x['verified_hits']==[] for x in r['rows'][1:])
assert all(x['prefix_states']==64 and x['suffix_states']==16 and
           x['prefix_x_buckets']==32 and x['suffix_x_buckets']==8 for x in r['rows'])
assert sum(x['candidate_group_checks'] for x in r['rows'])==4
assert prior['rows'][0]['group_hits']==[[0,30]]
assert all(x['group_hits']==[] for x in prior['rows'][1:])
assert c['status']=='COMPLETE' and c['exit_code']==0 and c['stop_reason'] is None
assert c['monitor_error'] is None and c['command'][0]=='/Volumes/SSD990/cryptanalysis/sage'
assert c['wall_seconds']<120 and c['sampled_peak_combined_rss_bytes']<4294967296
assert c['result_sha256']==sha(H/'n41_result.json')
assert c['stdout_sha256']==sha(H/'n41.stdout') and c['stderr_sha256']==sha(H/'n41.stderr')
assert (H/'n41.stderr').read_bytes()==b''
result={'status':'PASS_UNPINNED_N41_PREFIX_SUFFIX_X_GATE','candidate_id':None,
        'curve_id':r['curve_id'],'ordinary_relation_hits':1,
        'boxes_checked':9,'candidate_group_checks':4,
        'protocol_sha256':sha(H/'n41_gate_protocol.json'),
        'verifier_sha256':sha(Path(__file__))}
(H/'n41_gate.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True))
