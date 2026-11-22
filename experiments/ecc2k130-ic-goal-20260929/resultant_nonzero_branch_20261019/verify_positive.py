"""Freeze the N131 positive branch gate before a public-block query."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
read=lambda path:json.loads(Path(path).read_text())
cfg=read(HERE/'positive_gate_protocol.json')
assert cfg['status']=='FROZEN_BEFORE_POSITIVE_GATE'
for name,source in cfg['sources'].items():
    assert sha(source['path'])==source['sha256'],name
row=read(HERE/'n131_p_k4_result.json')
receipt=read(HERE/'n131_p_k4_receipt.json')
replay=read(cfg['sources']['independent_curve_replay']['path'])
assert receipt['status']=='COMPLETE' and receipt['exit_code']==0
assert receipt['stop_reason'] is None and receipt['monitor_error'] is None
assert 0<receipt['wall_seconds']<600
assert 0<receipt['sampled_peak_combined_rss_bytes']<4294967296
assert receipt['rss_samples']>0
assert receipt['result_sha256']==sha(HERE/'n131_p_k4_result.json')
assert receipt['stdout_sha256']==sha(HERE/'n131_p_k4.stdout')
assert receipt['stderr_sha256']==sha(HERE/'n131_p_k4.stderr')
assert row['status']=='GB_COMPLETE' and row['target_index']==0
assert row['recovered_codes']=={'first_code':3,'second_code':16722}
assert row['nonzero_branch_products_checked']==8
assert row['anf_monomials']==2314 and row['source_anf_monomials']==5317
assert row['protocol_sha256']==sha(HERE/'protocol.json')
assert replay['status']=='PASS_INDEPENDENT_N131_CURVE_REPLAY'
assert replay['curve_id']==row['curve_id']
assert replay['source_codes']==[3,16722]
assert replay['target_point']==row['target_point']
out={'status':'PASS_N131_NONZERO_BRANCH_POSITIVE_GATE','candidate_id':None,
     'protocol_sha256':sha(HERE/'positive_gate_protocol.json'),
     'verifier_sha256':sha(__file__),
     'curve_id':row['curve_id'],'recovered_codes':row['recovered_codes'],
     'wall_seconds':receipt['wall_seconds'],
     'sampled_peak_combined_rss_bytes':receipt['sampled_peak_combined_rss_bytes']}
(HERE/'positive_gate.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True))
