"""Hash-bound N41/N131 target-conditioned partial-sum gate."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((H/'terminal_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_PREFIX_SUFFIX_X_TERMINAL'
for label,s in cfg['sources'].items():assert sha(s['path'])==s['sha256'],label
n41gate=json.loads((H/'n41_gate.json').read_text())
assert n41gate['status']=='PASS_UNPINNED_N41_PREFIX_SUFFIX_X_GATE'
for case,expected in [('n41',9),('n131',9)]:
    p=json.loads((H/(case+'_protocol.json')).read_text())
    r=json.loads((H/(case+'_result.json')).read_text())
    c=json.loads((H/(case+'_receipt.json')).read_text())
    assert p['status']=='FROZEN_BEFORE_PREFIX_SUFFIX_X_'+case.upper()
    for label,s in p['sources'].items():assert sha(s['path'])==s['sha256'],(case,label)
    assert r['status']=='COMPLETE_PREFIX_SUFFIX_X' and r['boxes_completed']==expected
    assert r['verified_hits']==1 and all(row['verified_hits']==[] for row in r['rows'][1:])
    assert all(row['prefix_states']==64 and row['suffix_states']==16 and
               row['prefix_x_buckets']==32 and row['suffix_x_buckets']==8 and
               row['residual_x_queries']==64 for row in r['rows'])
    assert sum(row['candidate_group_checks'] for row in r['rows'])==4
    assert c['status']=='COMPLETE' and c['exit_code']==0 and c['stop_reason'] is None
    assert c['monitor_error'] is None and c['command'][0]=='/Volumes/SSD990/cryptanalysis/sage'
    assert c['wall_seconds']<(120 if case=='n41' else 600)
    assert c['sampled_peak_combined_rss_bytes']<4294967296
    assert c['result_sha256']==sha(H/(case+'_result.json'))
    assert c['stdout_sha256']==sha(H/(case+'.stdout'))
    assert c['stderr_sha256']==sha(H/(case+'.stderr'))
    assert (H/(case+'.stderr')).read_bytes()==b''
    if case=='n41':assert r['rows'][0]['verified_hits']==[[0,1,1,1,1]]
    else:assert r['rows'][0]['verified_hits']==[[1,1,0,1,1]]
lean=(H/'PrefixSuffix.lean').read_text();stdout=(H/'lean.stdout').read_text()
assert all(bad not in lean for bad in ('sorry','admit','axiom '))
assert (H/'lean.stderr').read_bytes()==b'' and 'sorryAx' not in stdout
assert "'PrefixSuffix.residual_key_covered' depends on axioms: [propext]" in stdout
assert "'PrefixSuffix.indexed_decomposition_covered' depends on axioms: [propext]" in stdout
n41=json.loads((H/'n41_result.json').read_text());n131=json.loads((H/'n131_result.json').read_text())
result={'status':'PASS_PREFIX_SUFFIX_X_FINITE_PANEL_AUDIT','candidate_id':None,
        'n41_boxes_checked':9,'n131_boxes_checked':9,
        'n131_public_boxes_checked':8,'n131_public_assignments':8192,
        'n131_public_group_hits':0,'n131_precompute_seconds':n131['precompute_seconds'],
        'n131_query_seconds':n131['query_seconds'],
        'n131_direct_seconds':n131['direct_seconds'],
        'protocol_sha256':sha(H/'terminal_protocol.json'),
        'verifier_sha256':sha(Path(__file__))}
(H/'terminal_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True))
